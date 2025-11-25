import pdfplumber
import pytesseract
from PIL import Image
import re
import logging
from typing import Dict, List, Any, Tuple
from decimal import Decimal
import os

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from uploaded files (PDF or image).
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text content
    """
    try:
        file_extension = file_path.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension in ['jpg', 'jpeg', 'png', 'tiff', 'bmp']:
            return extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
            
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        raise


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    try:
        text_content = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
        return text_content.strip()
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        raise


def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using pytesseract OCR."""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from image {image_path}: {str(e)}")
        raise


def parse_proforma_text(text: str) -> Dict[str, Any]:
    """
    Parse extracted text from proforma invoice to extract structured data.
    
    Args:
        text: Raw text extracted from the document
        
    Returns:
        Dictionary with extracted fields
    """
    try:
        extracted_data = {
            'vendor': '',
            'vendor_email': '',
            'vendor_phone': '',
            'invoice_number': '',
            'invoice_date': '',
            'items': [],
            'subtotal': None,
            'tax': None,
            'total_amount': None,
            'currency': 'RWF',
            'payment_terms': '',
            'due_date': ''
        }
        
        lines = text.split('\n')
        
        # Extract vendor information (usually at the top)
        vendor_patterns = [
            r'(?:vendor|supplier|company):\s*(.+)',
            r'(?:from|bill\s+to):\s*(.+)',
            r'^([A-Z][a-zA-Z\s&,.-]+(?:Ltd|LLC|Inc|Corp|Co\.?))',
        ]
        
        for line in lines[:10]:  # Check first 10 lines for vendor
            for pattern in vendor_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and not extracted_data['vendor']:
                    extracted_data['vendor'] = match.group(1).strip()
                    break
        
        # Extract contact information
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        for line in lines:
            if not extracted_data['vendor_email']:
                email_match = re.search(email_pattern, line)
                if email_match:
                    extracted_data['vendor_email'] = email_match.group()
            
            if not extracted_data['vendor_phone']:
                phone_match = re.search(phone_pattern, line)
                if phone_match:
                    extracted_data['vendor_phone'] = phone_match.group()
        
        # Extract invoice number and date
        invoice_patterns = [
            r'(?:invoice|inv)[\s#:]*(\w+)',
            r'(?:number|no)[\s#:]*(\w+)',
            r'#(\w+)'
        ]
        
        date_patterns = [
            r'(?:date|dated):\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{1,2}-\d{1,2})'
        ]
        
        for line in lines:
            if not extracted_data['invoice_number']:
                for pattern in invoice_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        extracted_data['invoice_number'] = match.group(1).strip()
                        break
            
            if not extracted_data['invoice_date']:
                for pattern in date_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        extracted_data['invoice_date'] = match.group(1).strip()
                        break
        
        # Extract items and amounts
        extracted_data['items'] = extract_line_items(lines)
        
        # Extract totals
        amount_patterns = [
            r'(?:total|amount\s+due)[\s:$]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:subtotal)[\s:$]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(?:tax|vat)[\s:$]*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for line in lines:
            line_lower = line.lower()
            
            if 'total' in line_lower and not extracted_data['total_amount']:
                match = re.search(amount_patterns[0], line, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        extracted_data['total_amount'] = float(amount_str)
                    except ValueError:
                        pass
            
            if 'subtotal' in line_lower and not extracted_data['subtotal']:
                match = re.search(amount_patterns[1], line, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        extracted_data['subtotal'] = float(amount_str)
                    except ValueError:
                        pass
            
            if any(tax_term in line_lower for tax_term in ['tax', 'vat', 'gst']) and not extracted_data['tax']:
                match = re.search(amount_patterns[2], line, re.IGNORECASE)
                if match:
                    amount_str = match.group(1).replace(',', '')
                    try:
                        extracted_data['tax'] = float(amount_str)
                    except ValueError:
                        pass
        
        # Extract payment terms
        terms_patterns = [
            r'(?:payment\s+terms|terms):\s*(.+)',
            r'(?:net|due)\s+(\d+)\s+days?',
            r'(?:due\s+date):\s*(.+)'
        ]
        
        for line in lines:
            for pattern in terms_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match and not extracted_data['payment_terms']:
                    extracted_data['payment_terms'] = match.group(1).strip()
                    break
        
        # Clean up extracted data
        extracted_data = {k: v for k, v in extracted_data.items() if v}
        
        logger.info(f"Successfully parsed proforma. Extracted {len(extracted_data)} fields.")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error parsing proforma text: {str(e)}")
        return {'error': str(e)}


def extract_line_items(lines: List[str]) -> List[Dict[str, Any]]:
    """Extract line items from text lines."""
    items = []
    
    # Pattern to match item lines: description, quantity, price
    item_pattern = r'(.+?)\s+(\d+)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
    
    for line in lines:
        line = line.strip()
        if not line or len(line.split()) < 3:
            continue
            
        match = re.search(item_pattern, line)
        if match:
            try:
                description = match.group(1).strip()
                quantity = int(match.group(2))
                price = float(match.group(3).replace(',', ''))
                
                items.append({
                    'description': description,
                    'quantity': quantity,
                    'unit_price': price,
                    'total_price': quantity * price
                })
            except (ValueError, IndexError):
                continue
    
    return items


def validate_receipt(receipt_data: Dict[str, Any], po_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate receipt against purchase order data.
    
    Args:
        receipt_data: Extracted data from receipt
        po_data: Purchase order data for comparison
        
    Returns:
        Validation result with discrepancies
    """
    try:
        validation_result = {
            'valid': True,
            'discrepancies': [],
            'summary': {
                'vendor_match': False,
                'amount_match': False,
                'items_match': False,
                'total_discrepancies': 0
            }
        }
        
        # Validate vendor
        if 'vendor' in receipt_data and 'vendor' in po_data:
            if normalize_vendor_name(receipt_data['vendor']) != normalize_vendor_name(po_data['vendor']):
                validation_result['discrepancies'].append({
                    'field': 'vendor',
                    'expected': po_data['vendor'],
                    'actual': receipt_data['vendor'],
                    'severity': 'high'
                })
                validation_result['valid'] = False
            else:
                validation_result['summary']['vendor_match'] = True
        
        # Validate total amount
        receipt_total = receipt_data.get('total_amount', 0)
        po_total = po_data.get('total_amount', 0)
        
        if receipt_total and po_total:
            amount_difference = abs(float(receipt_total) - float(po_total))
            tolerance = float(po_total) * 0.05  # 5% tolerance
            
            if amount_difference > tolerance:
                validation_result['discrepancies'].append({
                    'field': 'total_amount',
                    'expected': po_total,
                    'actual': receipt_total,
                    'difference': amount_difference,
                    'severity': 'high'
                })
                validation_result['valid'] = False
            else:
                validation_result['summary']['amount_match'] = True
        
        # Validate items
        receipt_items = receipt_data.get('items', [])
        po_items = po_data.get('items', [])
        
        if receipt_items and po_items:
            items_validation = validate_items(receipt_items, po_items)
            validation_result['discrepancies'].extend(items_validation['discrepancies'])
            validation_result['summary']['items_match'] = items_validation['match']
            if not items_validation['match']:
                validation_result['valid'] = False
        
        validation_result['summary']['total_discrepancies'] = len(validation_result['discrepancies'])
        
        logger.info(f"Receipt validation completed. Valid: {validation_result['valid']}, "
                   f"Discrepancies: {validation_result['summary']['total_discrepancies']}")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating receipt: {str(e)}")
        return {
            'valid': False,
            'discrepancies': [{'field': 'validation_error', 'error': str(e), 'severity': 'high'}],
            'summary': {'total_discrepancies': 1}
        }


def validate_items(receipt_items: List[Dict], po_items: List[Dict]) -> Dict[str, Any]:
    """Validate items between receipt and PO."""
    discrepancies = []
    item_matches = 0
    
    for po_item in po_items:
        po_desc = normalize_item_description(po_item.get('description', ''))
        found_match = False
        
        for receipt_item in receipt_items:
            receipt_desc = normalize_item_description(receipt_item.get('description', ''))
            
            if similarity_score(po_desc, receipt_desc) > 0.8:  # 80% similarity
                found_match = True
                
                # Check quantity
                po_qty = po_item.get('quantity', 0)
                receipt_qty = receipt_item.get('quantity', 0)
                if po_qty != receipt_qty:
                    discrepancies.append({
                        'field': 'item_quantity',
                        'item': po_item.get('description', ''),
                        'expected': po_qty,
                        'actual': receipt_qty,
                        'severity': 'medium'
                    })
                
                # Check unit price (with tolerance)
                po_price = float(po_item.get('unit_price', 0))
                receipt_price = float(receipt_item.get('unit_price', 0))
                price_difference = abs(po_price - receipt_price)
                tolerance = po_price * 0.1  # 10% tolerance
                
                if price_difference > tolerance:
                    discrepancies.append({
                        'field': 'item_price',
                        'item': po_item.get('description', ''),
                        'expected': po_price,
                        'actual': receipt_price,
                        'difference': price_difference,
                        'severity': 'medium'
                    })
                
                item_matches += 1
                break
        
        if not found_match:
            discrepancies.append({
                'field': 'missing_item',
                'item': po_item.get('description', ''),
                'severity': 'high'
            })
    
    return {
        'match': len(discrepancies) == 0,
        'discrepancies': discrepancies,
        'matched_items': item_matches,
        'total_po_items': len(po_items)
    }


def normalize_vendor_name(vendor_name: str) -> str:
    """Normalize vendor name for comparison."""
    if not vendor_name:
        return ""
    
    # Convert to lowercase and remove common business suffixes
    normalized = vendor_name.lower()
    suffixes = ['ltd', 'llc', 'inc', 'corp', 'co.', 'company', 'limited']
    
    for suffix in suffixes:
        normalized = re.sub(rf'\b{suffix}\b\.?', '', normalized)
    
    # Remove extra whitespace and punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def normalize_item_description(description: str) -> str:
    """Normalize item description for comparison."""
    if not description:
        return ""
    
    # Convert to lowercase and remove extra whitespace
    normalized = description.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity score between two text strings."""
    if not text1 or not text2:
        return 0.0
    
    # Simple word-based similarity
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)