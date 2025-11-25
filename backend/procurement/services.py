from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

from .models import PurchaseRequest, Approval, PurchaseOrder, ReceiptValidation
from .utils import extract_text_from_file, parse_proforma_text, validate_receipt
from .user_utils import is_approver_level_1, is_approver_level_2, can_approve
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class PurchaseRequestService:
    """Service class for handling purchase request business logic."""
    
    @staticmethod
    @transaction.atomic
    def approve_request(request_id: str, approver: User, decision: str, comments: str = '') -> Dict[str, Any]:
        """
        Handle approval workflow with proper transaction handling and race condition prevention.
        
        Args:
            request_id: UUID of the purchase request
            approver: User making the approval decision
            decision: 'approved' or 'rejected'
            comments: Optional comments from approver
            
        Returns:
            Dictionary with approval result
        """
        try:
            # Lock the request to prevent race conditions
            purchase_request = PurchaseRequest.objects.select_for_update().get(id=request_id)
            
            # Validate request state
            if not purchase_request.is_pending:
                return {
                    'success': False,
                    'error': 'Request is not in pending status',
                    'code': 'INVALID_STATUS'
                }
            
            # Get existing approvals
            existing_approvals = purchase_request.approvals.all().order_by('level')
            current_level = PurchaseRequestService._determine_approval_level(existing_approvals, approver)
            
            if current_level is None:
                return {
                    'success': False,
                    'error': 'User cannot approve this request at current stage',
                    'code': 'UNAUTHORIZED_APPROVAL'
                }
            
            # Check if user already approved at this level
            if existing_approvals.filter(level=current_level, approver=approver).exists():
                return {
                    'success': False,
                    'error': 'User has already approved at this level',
                    'code': 'DUPLICATE_APPROVAL'
                }
            
            # Create approval record
            approval = Approval.objects.create(
                purchase_request=purchase_request,
                approver=approver,
                level=current_level,
                decision=decision,
                comments=comments
            )
            
            # Update request status based on decision and level
            if decision == 'rejected':
                purchase_request.status = PurchaseRequest.Status.REJECTED
                purchase_request.save()
                
                logger.info(f"Request {request_id} rejected by {approver.full_name} at level {current_level}")
                
                return {
                    'success': True,
                    'action': 'rejected',
                    'level': current_level,
                    'approval_id': str(approval.id)
                }
            
            elif decision == 'approved':
                if current_level == 2:  # Final approval
                    purchase_request.status = PurchaseRequest.Status.APPROVED
                    purchase_request.approved_by = approver
                    purchase_request.approved_at = timezone.now()
                    purchase_request.save()
                    
                    # Generate Purchase Order
                    po_result = PurchaseRequestService.generate_purchase_order(purchase_request)
                    
                    logger.info(f"Request {request_id} fully approved and PO generated: {po_result.get('po_number')}")
                    
                    return {
                        'success': True,
                        'action': 'fully_approved',
                        'level': current_level,
                        'approval_id': str(approval.id),
                        'purchase_order': po_result
                    }
                else:  # Level 1 approval, waiting for level 2
                    logger.info(f"Request {request_id} approved by {approver.full_name} at level {current_level}")
                    
                    return {
                        'success': True,
                        'action': 'approved',
                        'level': current_level,
                        'approval_id': str(approval.id),
                        'next_level': current_level + 1
                    }
            
        except PurchaseRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'Purchase request not found',
                'code': 'NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Error processing approval for request {request_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'APPROVAL_ERROR'
            }
    
    @staticmethod
    def _determine_approval_level(existing_approvals, approver: User) -> Optional[int]:
        """Determine which approval level the user should approve at."""
        
        if not existing_approvals:
            # No approvals yet, Level 1 approver can start
            return 1 if is_approver_level_1(approver) else None
        
        last_approval = existing_approvals.last()
        
        # If last approval was rejected, no further approvals
        if last_approval.decision == 'rejected':
            return None
        
        # If level 1 was approved, level 2 can approve
        if last_approval.level == 1 and last_approval.decision == 'approved':
            return 2 if is_approver_level_2(approver) else None
        
        # If level 2 was already approved, no more approvals needed
        if last_approval.level == 2:
            return None
        
        return None
    
    @staticmethod
    def generate_purchase_order(purchase_request: PurchaseRequest) -> Dict[str, Any]:
        """Generate PDF purchase order and save to database."""
        try:
            # Create PO record first to get PO number
            po = PurchaseOrder(
                purchase_request=purchase_request,
                total_amount=purchase_request.amount
            )
            
            # Extract vendor info from proforma if available
            vendor_info = PurchaseRequestService._extract_vendor_info(purchase_request)
            po.vendor = vendor_info.get('vendor', 'Unknown Vendor')
            po.extracted_details = vendor_info
            
            # Generate PDF
            pdf_buffer = PurchaseRequestService._generate_po_pdf(purchase_request, po, vendor_info)
            
            # Save PDF file
            pdf_file = ContentFile(pdf_buffer.getvalue())
            po.file.save(f"PO_{po.po_number}.pdf", pdf_file, save=False)
            
            # Save PO record
            po.save()
            
            logger.info(f"Purchase order {po.po_number} generated for request {purchase_request.id}")
            
            return {
                'success': True,
                'po_number': po.po_number,
                'po_id': str(po.id),
                'total_amount': float(po.total_amount),
                'vendor': po.vendor
            }
            
        except Exception as e:
            logger.error(f"Error generating purchase order for request {purchase_request.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _extract_vendor_info(purchase_request: PurchaseRequest) -> Dict[str, Any]:
        """Extract vendor information from proforma invoice if available."""
        vendor_info = {'vendor': 'Unknown Vendor'}
        
        if purchase_request.proforma:
            try:
                # Extract text from proforma
                text = extract_text_from_file(purchase_request.proforma.path)
                parsed_data = parse_proforma_text(text)
                
                if 'error' not in parsed_data:
                    vendor_info.update(parsed_data)
                
            except Exception as e:
                logger.warning(f"Could not extract vendor info from proforma: {str(e)}")
        
        return vendor_info
    
    @staticmethod
    def _generate_po_pdf(purchase_request: PurchaseRequest, po: PurchaseOrder, vendor_info: Dict) -> BytesIO:
        """Generate PDF content for purchase order."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Build PDF content
        story = []
        
        # Header
        title = Paragraph(f"<b>Purchase Order</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # PO Details
        po_details = [
            ['PO Number:', po.po_number],
            ['Date:', timezone.now().strftime('%Y-%m-%d')],
            ['Status:', 'Approved'],
            ['Total Amount:', f"${po.total_amount:,.2f}"]
        ]
        
        po_table = Table(po_details)
        po_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(po_table)
        story.append(Spacer(1, 20))
        
        # Vendor Information
        vendor_title = Paragraph("<b>Vendor Information</b>", styles['Heading2'])
        story.append(vendor_title)
        
        vendor_details = [
            ['Vendor:', vendor_info.get('vendor', 'N/A')],
            ['Email:', vendor_info.get('vendor_email', 'N/A')],
            ['Phone:', vendor_info.get('vendor_phone', 'N/A')],
        ]
        
        vendor_table = Table(vendor_details)
        vendor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(vendor_table)
        story.append(Spacer(1, 20))
        
        # Request Details
        request_title = Paragraph("<b>Purchase Request Details</b>", styles['Heading2'])
        story.append(request_title)
        
        description = Paragraph(f"<b>Title:</b> {purchase_request.title}", styles['Normal'])
        story.append(description)
        story.append(Spacer(1, 6))
        
        desc_text = Paragraph(f"<b>Description:</b> {purchase_request.description}", styles['Normal'])
        story.append(desc_text)
        story.append(Spacer(1, 20))
        
        # Items Table
        items_title = Paragraph("<b>Items</b>", styles['Heading2'])
        story.append(items_title)
        
        items_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
        
        for item in purchase_request.items.all():
            items_data.append([
                item.name,
                str(item.quantity),
                f"${item.unit_price:,.2f}",
                f"${item.total_price:,.2f}"
            ])
        
        items_table = Table(items_data)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(items_table)
        story.append(Spacer(1, 30))
        
        # Terms and Conditions
        terms_title = Paragraph("<b>Terms and Conditions</b>", styles['Heading2'])
        story.append(terms_title)
        
        terms_text = """
        1. Payment terms: Net 30 days from invoice date
        2. All items must be delivered as specified
        3. Any changes to this order must be approved in writing
        4. Supplier must provide delivery confirmation
        """
        
        terms = Paragraph(terms_text, styles['Normal'])
        story.append(terms)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def validate_receipt_against_po(purchase_order: PurchaseOrder, receipt_file_path: str, validated_by: User) -> Dict[str, Any]:
        """Validate receipt against purchase order."""
        try:
            # Extract text from receipt
            receipt_text = extract_text_from_file(receipt_file_path)
            receipt_data = parse_proforma_text(receipt_text)
            
            # Prepare PO data for comparison
            po_data = {
                'vendor': purchase_order.vendor,
                'total_amount': purchase_order.total_amount,
                'items': [
                    {
                        'description': item.name,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price
                    }
                    for item in purchase_order.purchase_request.items.all()
                ]
            }
            
            # Perform validation
            validation_result = validate_receipt(receipt_data, po_data)
            
            # Create validation record
            receipt_validation = ReceiptValidation.objects.create(
                purchase_order=purchase_order,
                receipt_file=receipt_file_path,
                is_valid=validation_result['valid'],
                discrepancies=validation_result['discrepancies'],
                validated_by=validated_by
            )
            
            logger.info(f"Receipt validation completed for PO {purchase_order.po_number}. "
                       f"Valid: {validation_result['valid']}")
            
            return {
                'success': True,
                'validation_id': str(receipt_validation.id),
                'is_valid': validation_result['valid'],
                'discrepancies': validation_result['discrepancies'],
                'summary': validation_result['summary']
            }
            
        except Exception as e:
            logger.error(f"Error validating receipt for PO {purchase_order.po_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_pending_requests_for_approver(approver: User):
        """Get purchase requests that are pending approval by the given approver."""
        pending_requests = []
        
        if not can_approve(approver):
            return pending_requests
        
        # Get all pending requests
        requests = PurchaseRequest.objects.filter(
            status=PurchaseRequest.Status.PENDING
        ).prefetch_related('approvals', 'created_by', 'items').order_by('-created_at')
        
        for request in requests:
            existing_approvals = request.approvals.all().order_by('level')
            
            # Determine if this approver can act on this request
            if not existing_approvals:
                # No approvals yet, Level 1 approver can approve
                if is_approver_level_1(approver):
                    pending_requests.append(request)
            else:
                last_approval = existing_approvals.last()
                
                # If rejected, skip
                if last_approval.decision == 'rejected':
                    continue
                
                # If Level 1 approved, Level 2 can approve
                if (last_approval.level == 1 and 
                    last_approval.decision == 'approved' and 
                    is_approver_level_2(approver)):
                    pending_requests.append(request)
        
        return pending_requests