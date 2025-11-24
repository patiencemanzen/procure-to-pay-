from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import PurchaseRequest, Approval, PurchaseOrder, ReceiptValidation
from .serializers import (
    PurchaseRequestSerializer, PurchaseRequestCreateSerializer,
    ApprovalSerializer, ApprovalActionSerializer, PurchaseOrderSerializer,
    ReceiptUploadSerializer, ReceiptValidationSerializer, ReceiptValidationCreateSerializer
)
from .permissions import (
    StaffCanCreateAndEditOwn, ApproverCanViewPending, FinanceCanViewApproved,
    CanApprovePurchaseRequest, IsFinanceUser
)
from .services import PurchaseRequestService

User = get_user_model()


class PurchaseRequestViewSet(ModelViewSet):
    """
    ViewSet for purchase requests with role-based access.
    
    Staff can create and view/edit their own pending requests.
    Approvers can view pending requests they can approve.
    Finance can view approved requests.
    """
    
    queryset = PurchaseRequest.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseRequestCreateSerializer
        return PurchaseRequestSerializer
    
    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update']:
            return [StaffCanCreateAndEditOwn()]
        elif self.action == 'destroy':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        
        if user.is_staff_member:
            # Staff can only see their own requests
            return PurchaseRequest.objects.filter(created_by=user).prefetch_related(
                'items', 'approvals__approver', 'created_by', 'approved_by', 'purchase_order'
            )
        elif user.can_approve:
            # Approvers can see requests they can act on
            pending_requests = PurchaseRequestService.get_pending_requests_for_approver(user)
            request_ids = [req.id for req in pending_requests]
            return PurchaseRequest.objects.filter(id__in=request_ids).prefetch_related(
                'items', 'approvals__approver', 'created_by', 'approved_by', 'purchase_order'
            )
        elif user.is_finance_user:
            # Finance can see approved requests
            return PurchaseRequest.objects.filter(
                status=PurchaseRequest.Status.APPROVED
            ).prefetch_related(
                'items', 'approvals__approver', 'created_by', 'approved_by', 'purchase_order'
            )
        else:
            return PurchaseRequest.objects.none()
    
    def perform_create(self, serializer):
        """Set the created_by field when creating a request."""
        if not self.request.user.is_staff_member:
            raise permissions.PermissionDenied("Only staff members can create purchase requests.")
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        methods=['POST'],
        request=ReceiptUploadSerializer,
        responses={200: PurchaseRequestSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[StaffCanCreateAndEditOwn])
    def submit_receipt(self, request, pk=None):
        """Upload receipt for a purchase request."""
        purchase_request = self.get_object()
        serializer = ReceiptUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            purchase_request.receipt = serializer.validated_data['receipt']
            purchase_request.save()
            
            return Response(
                PurchaseRequestSerializer(purchase_request).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PendingRequestsView(generics.ListAPIView):
    """
    List pending purchase requests for approvers.
    Only returns requests that the current user can approve.
    """
    
    serializer_class = PurchaseRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get pending requests for current approver."""
        user = self.request.user
        
        if not user.can_approve:
            return PurchaseRequest.objects.none()
        
        pending_requests = PurchaseRequestService.get_pending_requests_for_approver(user)
        request_ids = [req.id for req in pending_requests]
        
        return PurchaseRequest.objects.filter(id__in=request_ids).prefetch_related(
            'items', 'approvals__approver', 'created_by', 'approved_by'
        ).order_by('-created_at')


class ApprovalActionView(APIView):
    """
    Handle approval and rejection actions.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        request=ApprovalActionSerializer,
        responses={200: {'type': 'object'}}
    )
    def patch(self, request, pk):
        """Approve or reject a purchase request."""
        user = request.user
        
        if not user.can_approve:
            return Response(
                {'error': 'User does not have approval permissions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            purchase_request = PurchaseRequest.objects.get(id=pk)
        except PurchaseRequest.DoesNotExist:
            return Response(
                {'error': 'Purchase request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ApprovalActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Process the approval
        result = PurchaseRequestService.approve_request(
            request_id=pk,
            approver=user,
            decision=serializer.validated_data['decision'],
            comments=serializer.validated_data.get('comments', '')
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            if result.get('code') == 'NOT_FOUND':
                status_code = status.HTTP_404_NOT_FOUND
            elif result.get('code') == 'UNAUTHORIZED_APPROVAL':
                status_code = status.HTTP_403_FORBIDDEN
            
            return Response(result, status=status_code)


class FinanceApprovedRequestsView(generics.ListAPIView):
    """
    List approved purchase requests for finance users.
    """
    
    serializer_class = PurchaseRequestSerializer
    permission_classes = [IsFinanceUser]
    
    def get_queryset(self):
        return PurchaseRequest.objects.filter(
            status=PurchaseRequest.Status.APPROVED
        ).prefetch_related(
            'items', 'approvals__approver', 'created_by', 'approved_by', 'purchase_order'
        ).order_by('-approved_at')


class ReceiptValidationView(APIView):
    """
    Handle receipt validation against purchase orders.
    """
    
    permission_classes = [IsFinanceUser]
    
    @extend_schema(
        request=ReceiptValidationCreateSerializer,
        responses={200: ReceiptValidationSerializer}
    )
    def post(self, request):
        """Validate a receipt against a purchase order."""
        po_id = request.data.get('purchase_order_id')
        
        if not po_id:
            return Response(
                {'error': 'purchase_order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            purchase_order = PurchaseOrder.objects.get(id=po_id)
        except PurchaseOrder.DoesNotExist:
            return Response(
                {'error': 'Purchase order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ReceiptValidationCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Save the receipt file first
            receipt_validation = serializer.save(purchase_order=purchase_order)
            
            # Perform validation
            validation_result = PurchaseRequestService.validate_receipt_against_po(
                purchase_order=purchase_order,
                receipt_file_path=receipt_validation.receipt_file.path,
                validated_by=request.user
            )
            
            if validation_result['success']:
                # Update the validation record with results
                receipt_validation.is_valid = validation_result['is_valid']
                receipt_validation.discrepancies = validation_result['discrepancies']
                receipt_validation.save()
                
                return Response(
                    ReceiptValidationSerializer(receipt_validation).data,
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': validation_result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderViewSet(ModelViewSet):
    """
    ViewSet for purchase orders. Read-only for most users.
    """
    
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Only allow read operations for non-admin users."""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        """Filter based on user role."""
        user = self.request.user
        
        if user.is_staff_member:
            # Staff can see POs for their approved requests
            return PurchaseOrder.objects.filter(
                purchase_request__created_by=user
            ).select_related('purchase_request')
        elif user.is_finance_user or user.can_approve:
            # Finance and approvers can see all POs
            return PurchaseOrder.objects.all().select_related('purchase_request')
        else:
            return PurchaseOrder.objects.none()


class UserStatsView(APIView):
    """
    Get statistics for the current user's dashboard.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return user-specific statistics."""
        user = request.user
        stats = {}
        
        if user.is_staff_member:
            # Staff statistics
            my_requests = PurchaseRequest.objects.filter(created_by=user)
            stats = {
                'role': 'staff',
                'total_requests': my_requests.count(),
                'pending_requests': my_requests.filter(status='pending').count(),
                'approved_requests': my_requests.filter(status='approved').count(),
                'rejected_requests': my_requests.filter(status='rejected').count(),
            }
        
        elif user.can_approve:
            # Approver statistics
            pending_for_me = PurchaseRequestService.get_pending_requests_for_approver(user)
            my_approvals = Approval.objects.filter(approver=user)
            
            stats = {
                'role': f'approver_level_{1 if user.is_approver_level_1 else 2}',
                'pending_for_approval': len(pending_for_me),
                'total_approved': my_approvals.filter(decision='approved').count(),
                'total_rejected': my_approvals.filter(decision='rejected').count(),
            }
        
        elif user.is_finance_user:
            # Finance statistics
            approved_requests = PurchaseRequest.objects.filter(status='approved')
            total_purchase_orders = PurchaseOrder.objects.count()
            receipt_validations = ReceiptValidation.objects.filter(validated_by=user)
            
            stats = {
                'role': 'finance',
                'approved_requests': approved_requests.count(),
                'total_purchase_orders': total_purchase_orders,
                'receipt_validations': receipt_validations.count(),
                'valid_receipts': receipt_validations.filter(is_valid=True).count(),
            }
        
        return Response(stats)