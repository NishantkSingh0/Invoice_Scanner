import threading
import base64
import os
import fitz
from django.core.cache import cache
from datetime import datetime


def process_pdf_background(job_id, pdf_bytes, key_name, start_page=1):
    """
    Background task to process PDF pages asynchronously.
    This function runs in a separate thread to avoid timeout.
    """
    # Import here to avoid circular dependency
    from .views import process_purchase_image, process_sales_image
    
    # Update job status to processing
    cache.set(f"pdf_job_{job_id}", {
        'status': 'processing',
        'total_pages': 0,
        'processed_pages': 0,
        'start_page': start_page,
        'error_message': None,
        'created_at': datetime.now().isoformat(),
    }, timeout=3600)  # 1 hour timeout
    
    try:
        # Open PDF from memory
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_document)
        
        # Adjust start_page to 0-based index
        start_index = max(0, start_page - 1)
        
        # Update total pages
        job_data = cache.get(f"pdf_job_{job_id}")
        job_data['total_pages'] = total_pages
        cache.set(f"pdf_job_{job_id}", job_data, timeout=3600)
        
        print(f"Starting background processing for job {job_id} from page {start_page} to {total_pages}")
        
        all_success = True
        for page_index in range(start_index, total_pages):
            print(f"Processing Page {page_index + 1}/{total_pages} for job {job_id}")
            
            page = pdf_document.load_page(page_index)
            matrix = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=matrix)
            image_bytes = pix.tobytes("png")
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            content_type = "image/png"
            
            # Process page based on key_name
            if key_name == "purchase":
                success = process_purchase_image(
                    base64_image,
                    content_type,
                    SheetID=os.getenv('GOOGLE_SHEET_ID_PURCHASE'),
                    sheet_name="PurchaseSheet",
                    PageNum=page_index + 1
                )
            elif key_name == "sales":
                success = process_sales_image(
                    base64_image,
                    content_type,
                    SheetID=os.getenv('GOOGLE_SHEET_ID_SALES'),
                    sheet_name="SalesSheet"
                )
            else:
                raise ValueError(f"Invalid key_name: {key_name}")
            
            if not success:
                all_success = False
                print(f"Failed on page {page_index + 1} for job {job_id}")
            
            # Update progress (relative to start_page)
            job_data = cache.get(f"pdf_job_{job_id}")
            job_data['processed_pages'] = page_index - start_index + 1
            cache.set(f"pdf_job_{job_id}", job_data, timeout=3600)
        
        pdf_document.close()
        
        # Mark as completed
        job_data = cache.get(f"pdf_job_{job_id}")
        job_data['status'] = 'completed'
        job_data['completed_at'] = datetime.now().isoformat()
        cache.set(f"pdf_job_{job_id}", job_data, timeout=3600)
        
        if all_success:
            print(f"Job {job_id} completed successfully")
        else:
            job_data['error_message'] = "Some pages failed to process"
            cache.set(f"pdf_job_{job_id}", job_data, timeout=3600)
            print(f"Job {job_id} completed with some failures")
            
    except Exception as e:
        # Mark as failed
        job_data = cache.get(f"pdf_job_{job_id}")
        job_data['status'] = 'failed'
        job_data['error_message'] = str(e)
        job_data['completed_at'] = datetime.now().isoformat()
        cache.set(f"pdf_job_{job_id}", job_data, timeout=3600)
        print(f"Job {job_id} failed with error: {e}")


def start_pdf_processing(job_id, pdf_bytes, key_name, start_page=1):
    """
    Start PDF processing in a background thread.
    """
    thread = threading.Thread(
        target=process_pdf_background,
        args=(job_id, pdf_bytes, key_name, start_page),
        daemon=True
    )
    thread.start()
