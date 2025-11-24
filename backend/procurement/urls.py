from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PurchaseRequestViewSet, PendingRequestsView, ApprovalActionView,
    FinanceApprovedRequestsView, ReceiptValidationView,
    PurchaseOrderViewSet, UserStatsView
)

router = DefaultRouter()
router.register(r'requests', PurchaseRequestViewSet, basename='purchase-request')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')

urlpatterns = [
    path('', include(router.urls)),
    
    # Specific endpoints for workflow
    path('requests/pending/', PendingRequestsView.as_view(), name='pending-requests'),
    path('requests/<uuid:pk>/approve/', ApprovalActionView.as_view(), name='approve-request'),
    path('requests/<uuid:pk>/reject/', ApprovalActionView.as_view(), name='reject-request'),
    
    # Finance endpoints
    path('finance/requests/approved/', FinanceApprovedRequestsView.as_view(), name='finance-approved-requests'),
    path('finance/validate-receipt/', ReceiptValidationView.as_view(), name='validate-receipt'),
    
    # User statistics
    path('dashboard/stats/', UserStatsView.as_view(), name='user-stats'),
]