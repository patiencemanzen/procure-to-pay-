import os
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


def upload_proforma_to(instance, filename):
    """Generate upload path for proforma invoices."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"proformas/{instance.id}/{filename}"


def upload_receipt_to(instance, filename):
    """Generate upload path for receipts."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"receipts/{instance.id}/{filename}"


def upload_po_to(instance, filename):
    """Generate upload path for purchase orders."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"purchase_orders/{instance.purchase_request.id}/{filename}"


class PurchaseRequest(models.Model):
    """Model for purchase requests."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    
    # Relationships
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_requests')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    
    # File uploads
    proforma = models.FileField(upload_to=upload_proforma_to, blank=True, null=True)
    receipt = models.FileField(upload_to=upload_receipt_to, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.status}"
    
    @property
    def can_be_edited(self):
        """Check if the request can be edited."""
        return self.status == self.Status.PENDING
    
    @property
    def is_pending(self):
        return self.status == self.Status.PENDING
    
    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED
    
    @property
    def is_rejected(self):
        return self.status == self.Status.REJECTED


class RequestItem(models.Model):
    """Model for individual items in a purchase request."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.name} (x{self.quantity})"
    
    @property
    def total_price(self):
        """Calculate total price for this item."""
        return self.quantity * self.unit_price


class Approval(models.Model):
    """Model for tracking approvals in the workflow."""
    
    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    class Level(models.IntegerChoices):
        LEVEL_1 = 1, 'Level 1'
        LEVEL_2 = 2, 'Level 2'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.IntegerField(choices=Level.choices)
    decision = models.CharField(max_length=10, choices=Decision.choices)
    comments = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['level', 'created_at']
        unique_together = ['purchase_request', 'level']
        indexes = [
            models.Index(fields=['purchase_request', 'level']),
        ]
    
    def __str__(self):
        return f"Level {self.level} - {self.decision} by {self.approver.full_name}"


class PurchaseOrder(models.Model):
    """Model for generated purchase orders."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_request = models.OneToOneField(PurchaseRequest, on_delete=models.CASCADE, related_name='purchase_order')
    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    extracted_details = models.JSONField(default=dict, blank=True)
    file = models.FileField(upload_to=upload_po_to)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['po_number']),
        ]
    
    def __str__(self):
        return f"PO-{self.po_number}"
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            # Generate PO number
            last_po = PurchaseOrder.objects.order_by('-created_at').first()
            if last_po:
                last_number = int(last_po.po_number.split('-')[-1])
                self.po_number = f"PO-{last_number + 1:06d}"
            else:
                self.po_number = "PO-000001"
        super().save(*args, **kwargs)


class ReceiptValidation(models.Model):
    """Model for storing receipt validation results."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='receipt_validations')
    receipt_file = models.FileField(upload_to='receipt_validations/')
    is_valid = models.BooleanField(default=False)
    discrepancies = models.JSONField(default=list, blank=True)
    validated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Receipt validation for {self.purchase_order.po_number} - {'Valid' if self.is_valid else 'Invalid'}"