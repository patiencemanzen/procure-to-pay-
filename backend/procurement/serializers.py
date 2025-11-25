from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import PurchaseRequest, RequestItem, Approval, PurchaseOrder, ReceiptValidation

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    """Simple user serializer for foreign key relationships."""
    
    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'role')


class RequestItemSerializer(serializers.ModelSerializer):
    """Serializer for request items."""
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = RequestItem
        fields = ('id', 'name', 'quantity', 'unit_price', 'total_price')
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value
    
    def validate_unit_price(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Unit price must be greater than 0.")
        return value


class ApprovalSerializer(serializers.ModelSerializer):
    """Serializer for approvals."""
    approver = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = Approval
        fields = ('id', 'level', 'decision', 'comments', 'approver', 'created_at')


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for purchase orders."""
    
    class Meta:
        model = PurchaseOrder
        fields = ('id', 'po_number', 'vendor', 'total_amount', 'extracted_details', 'file', 'created_at')


class ReceiptValidationSerializer(serializers.ModelSerializer):
    """Serializer for receipt validation."""
    validated_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = ReceiptValidation
        fields = ('id', 'receipt_file', 'is_valid', 'discrepancies', 'validated_by', 'created_at')


class PurchaseRequestSerializer(serializers.ModelSerializer):
    """Serializer for purchase requests."""
    items = RequestItemSerializer(many=True, required=False)
    approvals = ApprovalSerializer(many=True, read_only=True)
    purchase_order = PurchaseOrderSerializer(read_only=True)
    created_by = UserSimpleSerializer(read_only=True)
    approved_by = UserSimpleSerializer(read_only=True)
    
    # Calculated fields
    total_items_amount = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()
    can_edit = serializers.ReadOnlyField(source='can_be_edited')
    
    class Meta:
        model = PurchaseRequest
        fields = (
            'id', 'title', 'description', 'amount', 'status', 'created_by', 'approved_by',
            'proforma', 'receipt', 'created_at', 'updated_at', 'approved_at',
            'items', 'approvals', 'purchase_order', 'total_items_amount', 
            'approval_status', 'can_edit'
        )
        read_only_fields = ('status', 'approved_by', 'approved_at')
    
    def get_total_items_amount(self, obj):
        """Calculate total amount from items."""
        return sum(item.total_price for item in obj.items.all())
    
    def get_approval_status(self, obj):
        """Get current approval status."""
        approvals = obj.approvals.all().order_by('level')
        if not approvals:
            return {'current_level': 1, 'pending_approver_level': 1}
        
        last_approval = approvals.last()
        if last_approval.decision == 'rejected':
            return {'current_level': last_approval.level, 'status': 'rejected', 'rejected_at_level': last_approval.level}
        
        approved_levels = [a.level for a in approvals if a.decision == 'approved']
        if len(approved_levels) >= 2:
            return {'current_level': 2, 'status': 'fully_approved'}
        elif 1 in approved_levels:
            return {'current_level': 1, 'pending_approver_level': 2}
        else:
            return {'current_level': 0, 'pending_approver_level': 1}
    
    def validate_amount(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        request = PurchaseRequest.objects.create(**validated_data)
        
        for item_data in items_data:
            RequestItem.objects.create(purchase_request=request, **item_data)
        
        return request
    
    def update(self, instance, validated_data):
        # Check if request can be updated
        if not instance.can_be_edited:
            raise serializers.ValidationError("Cannot edit request that is not in pending status.")
        
        items_data = validated_data.pop('items', None)
        
        # Update the request
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items if provided
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                RequestItem.objects.create(purchase_request=instance, **item_data)
        
        return instance


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating purchase requests."""
    items = RequestItemSerializer(many=True, required=True)
    
    class Meta:
        model = PurchaseRequest
        fields = ('title', 'description', 'amount', 'proforma', 'items')
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = PurchaseRequest.objects.create(**validated_data)
        
        for item_data in items_data:
            RequestItem.objects.create(purchase_request=request, **item_data)
        
        return request


class ApprovalActionSerializer(serializers.Serializer):
    """Serializer for approval actions."""
    decision = serializers.ChoiceField(choices=Approval.Decision.choices)
    comments = serializers.CharField(required=False, allow_blank=True)
    
    def validate_decision(self, value):
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError("Decision must be 'approved' or 'rejected'.")
        return value


class ReceiptUploadSerializer(serializers.Serializer):
    """Serializer for receipt upload."""
    receipt = serializers.FileField()
    
    def validate_receipt(self, value):
        # Validate file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 5MB.")
        
        # Validate file type
        allowed_types = ['pdf', 'png', 'jpg', 'jpeg']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_types:
            raise serializers.ValidationError(
                f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_types)}"
            )
        
        return value


class ReceiptValidationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating receipt validations."""
    
    class Meta:
        model = ReceiptValidation
        fields = ('receipt_file', 'is_valid', 'discrepancies')
        
    def create(self, validated_data):
        validated_data['validated_by'] = self.context['request'].user
        return super().create(validated_data)