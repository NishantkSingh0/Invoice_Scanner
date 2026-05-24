from django.http import JsonResponse
import json
import base64
import os
import re
import fitz  # pymupdf
from difflib import SequenceMatcher
import io
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .llm import llama4, extract_bank_transactions, Gemini2Pro
from . import utils as ut
from . import prompt as pr
from .sheet import fill_sheet, fill_sheet_bulk
import secrets
from datetime import datetime, timedelta
from .bucketHandling import bucket

PURCHASE_SHEET_NAME="HOMEANDINDL"
SALES_SHEET_NAME="sales"
BANK_SHEET_NAME="Bank"
SALES_ORDER_SHEET_NAME="Sheet1"

def detectAnomalyCells(json_Data, ProductCounts):
    columns=[]
    if SequenceMatcher(None, json_Data['GSTIN/UIN'], '09AAMCC1953B1ZS').ratio() >0.9 or len(json_Data['GSTIN/UIN'])!=15:
        columns.append("GSTIN/UIN")
    if SequenceMatcher(None, json_Data['VENDOR_NAME'], 'Crafted Oak & Ore pvt ltd').ratio() >0.8:
        columns.append("VENDOR_NAME")
    if ProductCounts>6:
        columns.append("ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER")
    if str(json_Data['MONTH']).strip()=="NA":
        columns.append("MONTH")
    if len(str(json_Data['INVOICE_NO']))>18:
        columns.append("INVOICE_NO")
    if str(json_Data['FY']).strip()=="NA":
        columns.append("FY")
    if str(json_Data['AMOUNT']).strip()=="NA":
        columns.append("AMOUNT")
    if str(json_Data['HSN/SAC']).strip()=="NA":
        columns.append("HSN/SAC")
    if str(json_Data['TOTAL_TAX']).strip().startswith("NA"):
        columns.append("TOTAL_TAX")
    if str(json_Data['TOTAL_AMOUNT']).strip()=="Imp Details Missing":
        columns.append("TOTAL_AMOUNT")
        columns.append("ITEM_RATE")
        columns.append("QTY")

    return list(set(columns))


def process_purchase_image(base64_image, content_type, SheetID, sheet_name=PURCHASE_SHEET_NAME, PageNum=None):
    """
    Processes the base64 image using LLM and fills the Google Sheet.
    
    Args:
        base64_image (str): Base64 encoded image data.
        content_type (str): MIME type of the image (e.g., 'image/jpeg').
    
    Returns:
        bool: True if all operations successful, False otherwise.
    """
    try:
        print("Processing image")
        # print("Scceed Url: ", url)
        llm_response = llama4(pr.OCR_PROMPT, base64_image, content_type)
        if llm_response == "unable to parse":
            raise ValueError("LLM failed to parse the invoice image. Check your GROQ_API_KEY and model availability.")
        output = json.loads(llm_response)
        url=bucket(base64_string=base64_image)
        assert output != "unable to parse", "Unable to parse invoice"
        # print("Parsing Succeed",output)

        success = True
        ProductCounts=len(output['items'])
        GSTNum=ut.find_gst_by_vendor(output['VENDOR_NAME'], output['GSTIN/UIN'])

        for item in output['items']:
            try: 
                itemRate=item['ITEM_RATE'].replace(',','').replace('₹','').strip()
                text=f"{item['CGST']} + {item['SGST']}"
                DiscountedRate = str(itemRate).replace("'", ".") if item['DISCOUNT']=="NA" else str(float(itemRate) * (1 - float(item['DISCOUNT'].replace("'", ".").replace('%','').strip())/100))
                GSTTOTAL = str(sum(map(float, re.findall(r'\d+(?:\.\d+)?', str(text))))) if re.findall(r'\d+(?:\.\d+)?', str(text)) else "NA"
                Amount = str(float(str(item['QUANTITY'].split(" ")[0]).strip().replace("'", ".").replace(',','')) * float(str(DiscountedRate))) if not str(item['QUANTITY'].split(" ")[0]).strip().replace(',','').startswith("NA") and not str(DiscountedRate).strip().startswith("NA") else "NA"

                temp = {
                    "MONTH": re.split(r"[-/]", output['INVOICE_DATE'])[1] if len(re.split(r"[-/]", output['INVOICE_DATE'])) > 1 else "NA",
                    "FY": re.split(r"[-/]", output['INVOICE_DATE'])[2] if len(re.split(r"[-/]", output['INVOICE_DATE'])) > 2 else "NA",
                    "GR_DATE": output['INVOICE_DATE'],
                    "VENDOR_NAME": output['VENDOR_NAME'],
                    "PO_NO": output['PO_NO'],
                    "INVOICE_NO": output['INVOICE_NO'],
                    "INVOICE_DATE": output['INVOICE_DATE'],
                    "GSTIN/UIN": GSTNum,
                    "ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER": item['ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER'],
                    "LEDGER_ACCOUNT": item['LEDGER_ACCOUNT'],
                    "QTY": item['QUANTITY'],
                    "UNIT": item['UNIT'],
                    "ITEM_RATE": itemRate,
                    "AMOUNT": Amount,
                    "DISCOUNT": item['DISCOUNT'],
                    "HSN/SAC": item['HSN/SAC'],
                    "CGST": item['CGST'] if GSTNum.startswith("09") else "NA",
                    "SGST": item['SGST'] if GSTNum.startswith("09") else "NA",
                    "IGST": f"{item['CGST']} + {item['SGST']}" if not GSTNum.startswith("09") else "NA",
                    "TOTAL_TAX": GSTTOTAL if GSTTOTAL.startswith("NA") or Amount.startswith("NA") else float(Amount)*float(GSTTOTAL)/100,
                    "TOTAL_AMOUNT": "Imp Details Missing" if GSTTOTAL.startswith("NA") or Amount.startswith("NA") else float(Amount)*(1 + float(GSTTOTAL)/100),
                    "INVOICE_IMAGE": url
                }
                print(f"calling fill_sheet to update Data, Sheet Name: {sheet_name}")
                if not fill_sheet(temp, SheetID=SheetID, sheet_name=sheet_name, header_row=2, highlight_columns=detectAnomalyCells(temp, ProductCounts)):
                    success = False
                    print(f"Failed to fill sheet for item: {item}")
                    break  # Stop on first failure, or continue based on requirement
            except Exception as e:
                tempxvc={
                        "MONTH": "error" if PageNum is None else f"Page: {PageNum}",
                        "FY": "error",
                        "GR_DATE": output['INVOICE_DATE'],
                        "VENDOR_NAME": output['VENDOR_NAME'],
                        "PO_NO": output['PO_NO'],
                        "INVOICE_NO": output['INVOICE_NO'],
                        "INVOICE_DATE": output['INVOICE_DATE'],
                        "GSTIN/UIN": GSTNum,
                        "ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER": item['ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER'],
                        "LEDGER_ACCOUNT": item['LEDGER_ACCOUNT'],
                        "QTY": item['QUANTITY'],
                        "UNIT": item['UNIT'],
                        "ITEM_RATE": item['ITEM_RATE'],
                        "AMOUNT": "Error",
                        "DISCOUNT": item['DISCOUNT'],
                        "HSN/SAC": item['HSN/SAC'],
                        "CGST": item['CGST'] if GSTNum.startswith("09") else "NA",
                        "SGST": item['SGST'] if GSTNum.startswith("09") else "NA",
                        "IGST": f"{item['CGST']} + {item['SGST']}" if not GSTNum.startswith("09") else "NA",
                        "TOTAL_TAX": "error",
                        "TOTAL_AMOUNT": "error",
                        "INVOICE_IMAGE": url
                    }
                _=fill_sheet(tempxvc, SheetID=SheetID, sheet_name=sheet_name, header_row=2, highlight_columns=["MONTH","FY","GR_DATE","VENDOR_NAME","PO_NO","INVOICE_NO","INVOICE_DATE","GSTIN/UIN","ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER","LEDGER_ACCOUNT","QTY","UNIT","ITEM_RATE","AMOUNT","DISCOUNT","HSN/SAC","CGST","SGST","IGST","TOTAL_TAX","TOTAL_AMOUNT"])
                print(f"Error processing item: {e}")
                continue
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
        print("Processing CSV")
        # Wrap bytes in an in-memory buffer — no disk I/O, no temp files
        buffer = io.BytesIO(file_bytes)
        records = extract_bank_transactions(buffer)

        if not records:
            raise ValueError("No transaction records extracted from CSV")
        print("calling fill_sheet_bulk to update Data")
        return fill_sheet_bulk(records, SheetID=SheetID, sheet_name=BANK_SHEET_NAME, header_row=2)

    except Exception as e:
        print(f"Error in process_bank_csv: {e}")
        raise


def process_sales_image(base64_image, content_type, SheetID, sheet_name=SALES_SHEET_NAME):
    """
    Processes the base64 image using LLM and fills the Google Sheet.
    
    Args:
        base64_image (str): Base64 encoded image data.
        content_type (str): MIME type of the image (e.g., 'image/jpeg').
    
    Returns:
        bool: True if all operations successful, False otherwise.
    """
    try:
        print("Processing image")
        # print("Scceed Url: ", url)
        llm_response = llama4(pr.OCR_PROMPT, base64_image, content_type)
        if llm_response == "unable to parse":
            raise ValueError("LLM failed to parse the invoice image. Check your GROQ_API_KEY and model availability.")
        
        url=bucket(base64_string=base64_image)
        output = json.loads(llm_response)
        assert output != "unable to parse", "Unable to parse invoice"
        # print("Parsing Succeed",output)

        success = True
        ProductCounts=len(output['items'])
        GSTNum=ut.find_gst_by_vendor(output['VENDOR_NAME'], output['GSTIN/UIN'])

        for item in output['items']:
            try:
                itemRate=item['ITEM_RATE'].replace(',','').replace('₹','').strip()
                text=f"{item['CGST']} + {item['SGST']}"
                DiscountedRate = str(itemRate).replace("'", ".") if item['DISCOUNT']=="NA" else str(float(itemRate) * (1 - float(item['DISCOUNT'].replace("'", ".").replace('%','').strip())/100))
                GSTTOTAL = str(sum(map(float, re.findall(r'\d+(?:\.\d+)?', str(text))))) if re.findall(r'\d+(?:\.\d+)?', str(text)) else "NA"
                Amount = str(float(str(item['QUANTITY'].split(" ")[0]).strip().replace("'", ".").replace(',','')) * float(str(DiscountedRate))) if not str(item['QUANTITY'].split(" ")[0]).strip().replace(',','').startswith("NA") and not str(DiscountedRate).strip().startswith("NA") else "NA"

                temp = {
                    "MONTH": re.split(r"[-/]", output['INVOICE_DATE'])[1] if len(re.split(r"[-/]", output['INVOICE_DATE'])) > 1 else "NA",
                    "FY": re.split(r"[-/]", output['INVOICE_DATE'])[2] if len(re.split(r"[-/]", output['INVOICE_DATE'])) > 2 else "NA",
                    "GR_DATE": output['INVOICE_DATE'],
                    "VENDOR_NAME": output['VENDOR_NAME'],
                    "PO_NO": output['PO_NO'],
                    "INVOICE_NO": output['INVOICE_NO'],
                    "INVOICE_DATE": output['INVOICE_DATE'],
                    "GSTIN/UIN": GSTNum,
                    "ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER": item['ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER'],
                    "LEDGER_ACCOUNT": item['LEDGER_ACCOUNT'],
                    "QTY": item['QUANTITY'],
                    "UNIT": item['UNIT'],
                    "ITEM_RATE": itemRate,
                    "AMOUNT": Amount,
                    "HSN/SAC": item['HSN/SAC'],
                    "CGST": item['CGST'] if GSTNum.startswith("09") else "NA",
                    "SGST": item['SGST'] if GSTNum.startswith("09") else "NA",
                    "IGST": f"{item['CGST']} + {item['SGST']}" if not GSTNum.startswith("09") else "NA",
                    "TOTAL_TAX": GSTTOTAL if GSTTOTAL.startswith("NA") or Amount.startswith("NA") else float(Amount)*float(GSTTOTAL)/100,
                    "TOTAL_AMOUNT": "Imp Details Missing" if GSTTOTAL.startswith("NA") or Amount.startswith("NA") else float(Amount)*(1 + float(GSTTOTAL)/100),
                    "INVOICE_IMAGE": url
                }
                print(f"calling fill_sheet to update Data, Sheet Name: {sheet_name}")
                if not fill_sheet(temp, SheetID=SheetID, sheet_name=sheet_name, header_row=2, highlight_columns=detectAnomalyCells(temp, ProductCounts)):
                    success = False
                    print(f"Failed to fill sheet for item: {item}")
                    break  # Stop on first failure, or continue based on requirement
            except Exception as e:
                tempxvc={
                        "MONTH": "error",
                        "FY": "error",
                        "GR_DATE": output['INVOICE_DATE'],
                        "VENDOR_NAME": output['VENDOR_NAME'],
                        "PO_NO": output['PO_NO'],
                        "INVOICE_NO": output['INVOICE_NO'],
                        "INVOICE_DATE": output['INVOICE_DATE'],
                        "GSTIN/UIN": GSTNum,
                        "ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER": item['ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER'],
                        "LEDGER_ACCOUNT": item['LEDGER_ACCOUNT'],
                        "QTY": item['QUANTITY'],
                        "UNIT": item['UNIT'],
                        "ITEM_RATE": item['ITEM_RATE'],
                        "AMOUNT": "Error",
                        "DISCOUNT": item['DISCOUNT'],
                        "HSN/SAC": item['HSN/SAC'],
                        "CGST": item['CGST'] if GSTNum.startswith("09") else "NA",
                        "SGST": item['SGST'] if GSTNum.startswith("09") else "NA",
                        "IGST": f"{item['CGST']} + {item['SGST']}" if not GSTNum.startswith("09") else "NA",
                        "TOTAL_TAX": "error",
                        "TOTAL_AMOUNT": "error",
                        "INVOICE_IMAGE": url
                    }
                _=fill_sheet(tempxvc, SheetID=SheetID, sheet_name=sheet_name, header_row=2, highlight_columns=["MONTH","FY","GR_DATE","VENDOR_NAME","PO_NO","INVOICE_NO","INVOICE_DATE","GSTIN/UIN","ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER","LEDGER_ACCOUNT","QTY","UNIT","ITEM_RATE","AMOUNT","DISCOUNT","HSN/SAC","CGST","SGST","IGST","TOTAL_TAX","TOTAL_AMOUNT"])
                print(f"Error processing item: {e}")
                continue
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
            return JsonResponse({"success": True, "message": "Bank transactions uploaded successfully"})
        else:
            return JsonResponse({'error': 'Failed to process CSV or fill sheet'}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def render_pdf(request):

    print("Backend Called!")

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    file = request.FILES['file']
    key_name = request.POST.get("KeyName")

    try:

        pdf_bytes = file.read()

        # Open PDF from memory
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_document)
        print(f"Total Pages: {total_pages}")
        all_success = True
        for page_index in range(total_pages):

            print(f"Processing Page {page_index + 1}")
            page = pdf_document.load_page(page_index)
            # Increase quality if needed
            matrix = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=matrix)
            # Convert page image to bytes
            image_bytes = pix.tobytes("png")
            # Base64 encode
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            content_type = "image/png"
            # Process page
            if key_name == "purchase":

                print("Navigating to Purchase")
                success = process_purchase_image(
                    base64_image,
                    content_type,
                    SheetID=os.getenv('GOOGLE_SHEET_ID_PURCHASE'),
                    sheet_name=PURCHASE_SHEET_NAME,
                    PageNum=page_index + 1
                )

            elif key_name == "sales":
                print("Navigating to Sales")
                success = process_sales_image(
                    base64_image,
                    content_type,
                    SheetID=os.getenv('GOOGLE_SHEET_ID_SALES'),
                    sheet_name=SALES_SHEET_NAME
                )

            else:
                return JsonResponse(
                    {'error': 'Wrong KeyName provided'},
                    status=500
                )

            if not success:
                all_success = False
                print(f"Failed on page {page_index + 1}")

        pdf_document.close()
        if all_success:
            return JsonResponse({
                "success": True,
                "message": f"All pages processed successfully. Total pages: {total_pages}"
            })

        return JsonResponse({
            'error': 'Some pages failed processing'
        }, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def render(request):
    """
    Django view to handle image upload, process with LLM, and fill Google Sheet.
    
    Expects POST request with 'file' containing the image.
    Returns JSON with 'status': 'success' or 'error' message.
    """
    print("Backend Called! ")
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
            print("Navigating to Purchase")
            success = process_purchase_image(base64_image, content_type, SheetID=os.getenv('GOOGLE_SHEET_ID_PURCHASE'), sheet_name=PURCHASE_SHEET_NAME)
        elif key_name=="sales":
            print("Navigating to Sales")
            success = process_sales_image(base64_image, content_type, SheetID=os.getenv('GOOGLE_SHEET_ID_SALES'), sheet_name=SALES_SHEET_NAME)
        else:
            return JsonResponse({'error': 'Wrong KeyName provided'}, status=500)
        
        if success:
            return JsonResponse({"success": True, "message": "Image processed and sheet updated successfully"})
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
    

@api_view(["POST"])
def upload_excel(request):

    try:

        # Get uploaded file
        excel_file = request.FILES.get("file")

        if not excel_file:

            return Response(
                {
                    "success": False,
                    "message": "No file uploaded"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Read fully in RAM
        file_bytes = io.BytesIO(
            excel_file.read()
        )

        # Parse Excel
        parsed_data = ut.process_excel(
            file_path=file_bytes
        )

        all_success = True

        for i in range(len(parsed_data)):

            # Process SINGLE sheet
            processedData = ut.RefineSalesOrderData(
                parsed_data[i]
            )

            # Write to Google Sheet
            is_success = fill_sheet_bulk(processedData,SheetID=os.getenv("GOOGLE_SHEET_ID_SALES_ORDER"),header_row=8, sheet_name=SALES_ORDER_SHEET_NAME)

            print(
                f"Sheet {i} write success: "
                f"{is_success}"
            )

            if not is_success:
                all_success = False

        # FINAL SUCCESS
        if all_success:

            return Response(
                {
                    "success": True,
                    "message":
                        "Sales Order Uploaded Successfully"
                },
                status=status.HTTP_200_OK
            )

        # PARTIAL FAILURE
        return Response(
            {
                "success": False,
                "message":
                    "Some sheets failed to upload"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    except Exception as e:

        return Response(
            {
                "success": False,
                "message": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )