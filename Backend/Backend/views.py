from django.http import JsonResponse
import json
import base64
import os
import io
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .llm import llama4, extract_bank_transactions
from . import prompt as pr
from .sheet import fill_sheet, fill_sheet_bulk
import secrets
from datetime import datetime, timedelta
from .bucketHandling import bucket


def process_purchase_image(base64_image, content_type, SheetID):
    """
    Processes the base64 image using LLM and fills the Google Sheet.
    
    Args:
        base64_image (str): Base64 encoded image data.
        content_type (str): MIME type of the image (e.g., 'image/jpeg').
    
    Returns:
        bool: True if all operations successful, False otherwise.
    """
    try:
        url=bucket(base64_string=base64_image)
        # print("Scceed Url: ", url)
        llm_response = llama4(pr.OCR_PROMPT, base64_image, content_type)
        if llm_response == "unable to parse":
            raise ValueError("LLM failed to parse the invoice image. Check your GROQ_API_KEY and model availability.")
        output = json.loads(llm_response)
        assert output != "unable to parse", "Unable to parse invoice"
        # print("Parsing Succeed",output)
        success = True
        for item in output['items']:
            temp = {
                "MONTH": output['MONTH'],
                "FY": output['FY'],
                "GR_DATE": output['MONTH'],
                "VENDOR_NAME": output['VENDOR_NAME'],
                "PO_NO": output['PO_NO'],
                "INVOICE_NO": output['INVOICE_NO'],
                "INVOICE_DATE": output['INVOICE_DATE'],
                "INTERNAL_REF": output['INTERNAL_REF'],
                "GSTIN/UIN": output['GSTIN/UIN'],
                "ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER": item['ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER'],
                "ITEM_DESCRIPTION_AS_PER_CRAFTED_OAK": item['ITEM_DESCRIPTION_AS_PER_CRAFTED_OAK'],
                "LEDGER_ACCOUNT": item['LEDGER_ACCOUNT'],
                "QTY": item['QTY'],
                "UNIT": item['UNIT'],
                "ITEM_RATE": item['ITEM_RATE'],
                "AMOUNT": item['AMOUNT'],
                "HSN/SAC": item['HSN/SAC'],
                "CGST": item['CGST'] if output['GSTIN/UIN'].startswith("09") else "NA",
                "SGST": item['SGST'] if output['GSTIN/UIN'].startswith("09") else "NA",
                "IGST": f"{item['CGST'] + item['SGST']}" if not output['GSTIN/UIN'].startswith("09") else "NA",
                "TOTAL_TAX": item['TOTAL_TAX'],
                "TOTAL_AMOUNT": item['TOTAL_AMOUNT'],
                "INVOICE_IMAGE": url
            }
            if not fill_sheet_bulk([temp], SheetID=SheetID, sheet_name='Sheet1'):
                success = False
                break  # Stop on first failure, or continue based on requirement
        return success
    except Exception as e:
        print(f"Error in process_image: {e}")
        raise  # Re-raise so the view can return a meaningful error message


def process_bank_csv(file_bytes, SheetID):
    """
    Processes a bank statement CSV file and bulk-fills the Google Sheet.

    Args:
        file_bytes (bytes): Raw bytes of the uploaded CSV file.
        SheetID (str): Target Google Sheet ID.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Wrap bytes in an in-memory buffer — no disk I/O, no temp files
        buffer = io.BytesIO(file_bytes)
        records = extract_bank_transactions(buffer)

        if not records:
            raise ValueError("No transaction records extracted from CSV")

        return fill_sheet_bulk(records, SheetID=SheetID)

    except Exception as e:
        print(f"Error in process_bank_csv: {e}")
        raise


def process_sales_image(base64_image, content_type, SheetID):
    """
    Processes the base64 image using LLM and fills the Google Sheet.
    
    Args:
        base64_image (str): Base64 encoded image data.
        content_type (str): MIME type of the image (e.g., 'image/jpeg').
    
    Returns:
        bool: True if all operations successful, False otherwise.
    """
    try:
        url=bucket(base64_string=base64_image)
        # print("Scceed Url: ", url)
        llm_response = llama4(pr.OCR_PROMPT, base64_image, content_type)
        if llm_response == "unable to parse":
            raise ValueError("LLM failed to parse the invoice image. Check your GROQ_API_KEY and model availability.")
        output = json.loads(llm_response)
        assert output != "unable to parse", "Unable to parse invoice"
        # print("Parsing Succeed",output)
        success = True
        for item in output['items']:
            temp = {
                "MONTH": output['MONTH'],
                "FY": output['FY'],
                "GR_DATE": output['MONTH'],
                "VENDOR_NAME": output['VENDOR_NAME'],
                "PO_NO": output['PO_NO'],
                "INVOICE_NO": output['INVOICE_NO'],
                "INVOICE_DATE": output['INVOICE_DATE'],
                "INTERNAL_REF": output['INTERNAL_REF'],
                "GSTIN/UIN": output['GSTIN/UIN'],
                "ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER": item['ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER'],
                "ITEM_DESCRIPTION_AS_PER_CRAFTED_OAK": item['ITEM_DESCRIPTION_AS_PER_CRAFTED_OAK'],
                "LEDGER_ACCOUNT": item['LEDGER_ACCOUNT'],
                "QTY": item['QTY'],
                "UNIT": item['UNIT'],
                "ITEM_RATE": item['ITEM_RATE'],
                "AMOUNT": item['AMOUNT'],
                "HSN/SAC": item['HSN/SAC'],
                "CGST": item['CGST'] if output['GSTIN/UIN'].startswith("09") else "NA",
                "SGST": item['SGST'] if output['GSTIN/UIN'].startswith("09") else "NA",
                "IGST": f"{item['CGST'] + item['SGST']}" if not output['GSTIN/UIN'].startswith("09") else "NA",
                "TOTAL_TAX": item['TOTAL_TAX'],
                "TOTAL_AMOUNT": item['TOTAL_AMOUNT'],
                "INVOICE_IMAGE": url
            }
            if not fill_sheet(temp, SheetID=SheetID):
                success = False
                break  # Stop on first failure, or continue based on requirement
        return success
    except Exception as e:
        print(f"Error in process_image: {e}")
        raise  # Re-raise so the view can return a meaningful error message


@csrf_exempt
def render_csv(request):
    """
    Django view to handle CSV upload, extract bank transactions, and bulk-fill Google Sheet.

    Expects POST request with 'file' containing the CSV.
    Returns JSON with 'status': 'success' or an error message.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    file = request.FILES['file']

    # Basic content-type guard (browsers may send text/csv or application/octet-stream)
    if not file.name.lower().endswith('.csv'):
        return JsonResponse({'error': 'Only CSV files are accepted'}, status=400)

    try:
        file_bytes = file.read()
        success = process_bank_csv(file_bytes, SheetID=os.getenv('GOOGLE_SHEET_ID_BANK'))

        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'error': 'Failed to process CSV or fill sheet'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def render(request):
    """
    Django view to handle image upload, process with LLM, and fill Google Sheet.
    
    Expects POST request with 'file' containing the image.
    Returns JSON with 'status': 'success' or 'error' message.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    key_name = request.POST.get("KeyName")
    
    try:
        # Read and encode image
        image_data = file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        content_type = file.content_type
        
        # Process image and fill sheet
        if key_name=="purchase":
            success = process_purchase_image(base64_image, content_type, SheetID=os.getenv('GOOGLE_SHEET_ID_PURCHASE'), sheet_name="Purchase")
        elif key_name=="sales":
            success = process_sales_image(base64_image, content_type, SheetID=os.getenv('GOOGLE_SHEET_ID_SALES'), sheet_name="Sales")
        else:
            return JsonResponse({'error': 'Wrong KeyName provided'}, status=500)
        
        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'error': 'Failed to process image or fill sheet'}, status=500)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Simple in-memory token storage (for production, use database)
_auth_tokens = {}

def validate_credentials(user_id, password):
    """
    Validates user credentials. 
    Configure valid credentials here or pull from database.
    """
    # Example: Simple hardcoded credentials (replace with database lookup in production)
    VALID_CREDENTIALS = {
        'userid': os.getenv('EMP_ID'),
        'password': os.getenv('PASSWORD'),
    }
    # print(f"Validating credentials for user_id: {user_id}")
    # print(f"Expected password for {user_id}: {VALID_CREDENTIALS.get('password')}")
    # print(f"Provided password for {user_id}: {password}")
    
    return user_id == VALID_CREDENTIALS['userid'] and VALID_CREDENTIALS['password'] == password


@csrf_exempt
def login(request):
    """
    Authentication endpoint. Accepts POST request with user_id and password.
    Returns auth token and success status if credentials are valid.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        password = data.get('password')
        
        if not user_id or not password:
            return JsonResponse({'error': 'user_id and password are required'}, status=400)
        
        if validate_credentials(user_id, password):
            # Generate auth token
            token = secrets.token_urlsafe(32)
            _auth_tokens[token] = {
                'user_id': user_id,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(days=7)
            }
            
            return JsonResponse({
                'status': 'success',
                'token': token,
                'user_id': user_id,
                'message': 'Login successful'
            })
        else:
            return JsonResponse({
                'status': 'failed',
                'error': 'Invalid credentials'
            }, status=401)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def verify_token(request):
    """
    Verifies if the provided token is valid.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({'error': 'token is required'}, status=400)
        
        if token in _auth_tokens:
            token_data = _auth_tokens[token]
            
            # Check if token is expired
            if token_data['expires_at'] < datetime.now():
                del _auth_tokens[token]
                return JsonResponse({
                    'status': 'failed',
                    'error': 'Token expired'
                }, status=401)
            
            return JsonResponse({
                'status': 'valid',
                'user_id': token_data['user_id']
            })
        else:
            return JsonResponse({
                'status': 'invalid',
                'error': 'Invalid token'
            }, status=401)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)