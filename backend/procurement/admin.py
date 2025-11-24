from django.contrib import admin
from django.utils.html import format_html
from .models import PurchaseRequest, RequestItem, Approval, PurchaseOrder, ReceiptValidation


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 1
    fields = ('name', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)


class ApprovalInline(admin.TabularInline):
    model = Approval
    extra = 0
    readonly_fields = ('level', 'decision', 'comments', 'approver', 'created_at')
    fields = readonly_fields


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'amount', 'created_by', 'created_at', 'approved_at')
    list_filter = ('status', 'created_at', 'approved_at')
    search_fields = ('title', 'description', 'created_by__full_name', 'created_by__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'approved_at', 'can_be_edited')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'description', 'amount', 'status')
        }),
        ('Users', {
            'fields': ('created_by', 'approved_by')
        }),
        ('Files', {
            'fields': ('proforma', 'receipt')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Computed Fields', {
            'fields': ('can_be_edited',),
            'classes': ('collapse',)
        })
    )
    
    inlines = [RequestItemInline, ApprovalInline]
    
    def has_change_permission(self, request, obj=None):
        if obj and not obj.can_be_edited:
            return False
        return super().has_change_permission(request, obj)


@admin.register(RequestItem)
class RequestItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'purchase_request', 'quantity', 'unit_price', 'total_price')
    list_filter = ('purchase_request__status',)
    search_fields = ('name', 'purchase_request__title')
    readonly_fields = ('total_price',)


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('purchase_request', 'approver', 'level', 'decision', 'created_at')
    list_filter = ('level', 'decision', 'created_at')
    search_fields = ('purchase_request__title', 'approver__full_name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('purchase_request', 'approver', 'level', 'decision')
        }),
        ('Details', {
            'fields': ('comments', 'created_at')
        })
    )


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'vendor', 'total_amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('po_number', 'vendor', 'purchase_request__title')
    readonly_fields = ('id', 'po_number', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'po_number', 'purchase_request')
        }),
        ('Vendor Info', {
            'fields': ('vendor', 'total_amount')
        }),
        ('Files', {
            'fields': ('file',)
        }),
        ('Extracted Data', {
            'fields': ('extracted_details',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # POs should only be created automatically
        return False


@admin.register(ReceiptValidation)
class ReceiptValidationAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'is_valid', 'validated_by', 'created_at')
    list_filter = ('is_valid', 'created_at')
    search_fields = ('purchase_order__po_number', 'validated_by__full_name')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('purchase_order', 'receipt_file', 'validated_by')
        }),
        ('Validation Results', {
            'fields': ('is_valid', 'discrepancies')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('purchase_order', 'receipt_file', 'validated_by')
        return self.readonly_fields