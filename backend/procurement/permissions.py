from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to only allow owners of an object to edit it."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner
        return obj.created_by == request.user


class IsStaffUser(permissions.BasePermission):
    """Permission for staff users only."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff_member


class IsApproverUser(permissions.BasePermission):
    """Permission for approver users only."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_approve


class IsApproverLevel1(permissions.BasePermission):
    """Permission for Level 1 approvers only."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_approver_level_1


class IsApproverLevel2(permissions.BasePermission):
    """Permission for Level 2 approvers only."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_approver_level_2


class IsFinanceUser(permissions.BasePermission):
    """Permission for finance users only."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_finance_user


class CanApprovePurchaseRequest(permissions.BasePermission):
    """Permission to check if user can approve a specific purchase request."""
    
    def has_object_permission(self, request, view, obj):
        if not request.user.can_approve:
            return False
        
        # Get existing approvals for this request
        existing_approvals = obj.approvals.all().order_by('level')
        
        # If no approvals yet, Level 1 approver can approve
        if not existing_approvals:
            return request.user.is_approver_level_1
        
        last_approval = existing_approvals.last()
        
        # If rejected, no further approvals allowed
        if last_approval.decision == 'rejected':
            return False
        
        # If Level 1 approved, Level 2 can approve
        if last_approval.level == 1 and last_approval.decision == 'approved':
            return request.user.is_approver_level_2
        
        # If already fully approved, no more approvals needed
        return False


class CanEditPurchaseRequest(permissions.BasePermission):
    """Permission to check if user can edit a purchase request."""
    
    def has_object_permission(self, request, view, obj):
        # Only the creator can edit
        if obj.created_by != request.user:
            return False
        
        # Can only edit if status is pending
        return obj.can_be_edited


class StaffCanCreateAndEditOwn(permissions.BasePermission):
    """Permission for staff to create requests and edit their own pending requests."""
    
    def has_permission(self, request, view):
        # Must be staff to create
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.is_staff_member
        
        # Other methods handled by has_object_permission
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permission for staff on their own requests
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_staff_member and obj.created_by == request.user
        
        # Edit permission only for own pending requests
        if request.method in ['PUT', 'PATCH']:
            return (request.user.is_staff_member and 
                   obj.created_by == request.user and 
                   obj.can_be_edited)
        
        return False


class ApproverCanViewPending(permissions.BasePermission):
    """Permission for approvers to view pending requests they can act on."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_approve
    
    def has_object_permission(self, request, view, obj):
        if not request.user.can_approve:
            return False
        
        # Can only view pending requests
        if not obj.is_pending:
            return False
        
        # Check if this approver can act on this request
        existing_approvals = obj.approvals.all().order_by('level')
        
        # If no approvals yet, Level 1 approver can view
        if not existing_approvals:
            return request.user.is_approver_level_1
        
        last_approval = existing_approvals.last()
        
        # If rejected, no one can view for approval
        if last_approval.decision == 'rejected':
            return False
        
        # If Level 1 approved, Level 2 can view
        if last_approval.level == 1 and last_approval.decision == 'approved':
            return request.user.is_approver_level_2
        
        return False


class FinanceCanViewApproved(permissions.BasePermission):
    """Permission for finance users to view approved requests."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_finance_user
    
    def has_object_permission(self, request, view, obj):
        # Finance can only view approved requests
        return request.user.is_finance_user and obj.is_approved