import pandas as pd
import re
import requests
from pathlib import Path
from django.conf import settings
from rapidfuzz import fuzz
from jinja2 import Environment, BaseLoader
from jinja2 import Environment, FileSystemLoader
import base64
import json
import os
import io
from dotenv import load_dotenv
from googleapiclient.http import MediaIoBaseUpload
from weasyprint import HTML
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
load_dotenv()

def clean_value(value):
    """
    Cleans extracted values
    """
    if pd.isna(value):
        return None

    return str(value).strip()


def extract_metadata(df):
    metadata = {}

    for _, row in df.iterrows():

        row_values = [
            clean_value(v)
            for v in row.tolist()
            if clean_value(v)
        ]

        if len(row_values) < 2:
            continue

        for i in range(len(row_values) - 1):

            key = row_values[i]

            if len(str(key)) > 50:
                continue

            value = row_values[i + 1]

            normalized_key = (
                str(key)
                .upper()
                .replace(" ", "_")
                .replace(":", "")
                .strip()
            )

            metadata[normalized_key] = value

    return metadata


def detect_table_header(df):
    """
    Dynamically detects table header row
    """

    keywords = [
        "MODEL NUMBER",
        "PRODUCT NAME",
        "QUANTITY",
        "RATE",
        "TOTAL",
    ]

    for idx, row in df.iterrows():

        row_values = [
            str(v).strip().upper()
            for v in row.tolist()
        ]

        matched = sum(
            keyword in row_values
            for keyword in keywords
        )

        # At least 2 keywords matched
        if matched >= 2:
            return idx

    return None


def extract_table(df, header_row):
    """
    Extracts structured product table
    """

    table_df = df.iloc[header_row:].copy()

    # Set header
    table_df.columns = table_df.iloc[0]

    # Remove header row
    table_df = table_df.iloc[1:]

    # Clean columns
    table_df.columns = [
        str(col).strip().upper()
        for col in table_df.columns
    ]

    # Remove empty rows/cols
    table_df = table_df.dropna(how="all")
    table_df = table_df.dropna(axis=1, how="all")

    table_df.columns = [
        str(col)
        .strip()
        .replace("\n", " ")
        .replace("\r", " ")
        .upper()
        for col in table_df.columns
    ]
    return table_df.reset_index(drop=True)



def generate_job_card_pdf(data: dict) -> str:
    template_dir = Path(settings.BASE_DIR) / "template"

    if data.get("ref_image"):
        image = data["ref_image"]

        if not image.startswith("data:image"):
            image = f"data:image/png;base64,{image}"

        data["ref_image"] = image

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True
    )

    rendered_html = env.get_template("jobcard.html").render(**data)

    pdf_bytes = HTML(
        string=rendered_html,
        base_url=str(template_dir)
    ).write_pdf()

    return base64.b64encode(pdf_bytes).decode("utf-8")


def _drive_service():
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(os.environ["GOOGLE_DRIVE_CREDENTIAL"]),
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    return build("drive", "v3", credentials=credentials)


def drive_image_to_base64(drive_url: str) -> str:
    """
    Read image from Google Drive URL and return Base64 string.
    """
    if not drive_url or not isinstance(drive_url, str):
        return None

    try:
        service = _drive_service()

        file_id = re.search(
            r"/file/d/([^/]+)|id=([^&]+)",
            drive_url
        )
        if not file_id:
            print(f"No Google Drive file ID found in URL: {drive_url}")
            return None

        file_id = next(g for g in file_id.groups() if g)

        request = service.files().get_media(fileId=file_id)

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"Error in drive_image_to_base64: {e}")
        return None


def upload_pdf_to_drive(pdf_base64: str, folder_id: str, file_name: str = "document.pdf") -> str:
    """
    Upload a Base64 PDF directly to Google Drive.
    Returns the Drive view URL.
    """

    service = _drive_service()

    pdf_bytes = base64.b64decode(pdf_base64)

    media = MediaIoBaseUpload(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        resumable=True
    )

    file = service.files().create(
        body={
            "name": file_name,
            "parents": [folder_id]
        },
        media_body=media,
        fields="id"
    ).execute()

    return f"https://drive.google.com/file/d/{file['id']}/view"


def process_excel(file_path):

    excel = pd.ExcelFile(file_path)
    final_output = []

    for sheet_name in excel.sheet_names:
        print(f"\nProcessing Sheet: {sheet_name}")

        raw_df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=None
        )

        if raw_df.dropna(how="all").empty:
            print("Skipped Empty Sheet")
            continue

        header_row = detect_table_header(raw_df)

        if header_row is None:
            print("No table found")
            continue

        print(f"Table detected at row {header_row}")

        # Only read metadata above header row
        metadata = extract_metadata(
            raw_df.iloc[:header_row]
        )

        table_df = extract_table(
            raw_df,
            header_row
        )

        print("Detected Columns:")
        print(table_df.columns.tolist())

        final_output.append(
            {
                "sheet_name": sheet_name,
                "metadata": metadata,
                "table_data": table_df
            }
        )

    return final_output


def get_value(data, *keys):
    for key in keys:
        if key in data and data[key] not in [None, ""]:
            return data[key]
    return None


def clean_cell(value, default=""):
    if pd.isna(value) or value is None:
        return default
    if isinstance(value, (int, float)):
        return value
    return str(value).strip()


def RefineSalesOrderData(data):
    metadata = data["metadata"]
    table_data = data["table_data"]
    rows = []

    # If table_data is DataFrame
    if isinstance(table_data, pd.DataFrame):
        table_data = table_data.to_dict(orient="records")

    delivery_address = clean_cell(metadata.get("Delivery_Address")).replace("\n", " ").replace("\r", " ").strip()
    for item in table_data:
        product_name = str(item.get("PRODUCT_NAME")).strip().upper()
        model_number = str(item.get("MODEL_NUMBER")).strip().upper()
        rate_value = str(item.get("RATE", "")).strip().upper()

        # Skip summary rows
        if product_name in ["NAN", ""] or model_number in ["NAN", ""] or "TOTAL" in rate_value or "GST" in rate_value:
            continue

        drive_url = item.get("LAYOUT_RENDER_URL")
        # Handle nan / None / non-string / empty values
        if pd.isna(drive_url) or not isinstance(drive_url, str) or not drive_url.strip():
            base64 = None
        else:
            try:
                base64 = drive_image_to_base64(drive_url=drive_url.strip())
            except Exception as e:
                print(f"Error converting drive image to base64: {e}")
                base64 = None

        jobCardUrl = "NA"
        try:
            JobCard = generate_job_card_pdf(data={
                "client_name": get_value(metadata, "Billing_Name", "BILLING_NAME"),
                "po_number": get_value(metadata, "Purchase_Order_No", "PURCHASE_ORDER_NO"),
                "item_name": item.get("PRODUCT_NAME"),
                "quantity": item.get("QUANTITY"),
                "card_date": get_value(metadata, "PO_Valid_Till", "PO_VALID_TILL"),
                "Specifications": item.get("SPECIFICATIONS"),
                "ref_image": base64
            })
            jobCardUrl = upload_pdf_to_drive(pdf_base64=JobCard, folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID_JOB_CARDS"))
        except Exception as e:
            print(f"Error generating/uploading Job Card for product {product_name}: {e}")
            jobCardUrl = f"Error: {e}"

        row = {
            "Billing_Name": get_value(metadata, "Billing_Name", "BILLING_NAME"),
            "Billing_Address": get_value(metadata, "Billing_Address", "BILLING_ADDRESS"),
            "GST": get_value(metadata, "GST"),
            "Delivery_Address": delivery_address,
            "RENDER_URL": clean_cell(item.get("RENDER_URL")),
            "PO_Num": get_value(metadata, "Purchase_Order_No", "PURCHASE_ORDER_NO"),
            "PO_Valid_Till": get_value(metadata, "PO_Valid_Till", "PO_VALID_TILL"),
            "Order_Type": get_value(metadata, "Order_Type", "ORDER_TYPE"),
            "Product_Name": clean_cell(item.get("PRODUCT_NAME")),
            "Model_Number": clean_cell(item.get("MODEL_NUMBER")),
            "QTY": clean_cell(item.get("QUANTITY")),
            "Rate": clean_cell(item.get("RATE")),
            "Total": clean_cell(item.get("TOTAL")),
            "Specifications": clean_cell(item.get("SPECIFICATIONS")),
            "LAYOUT_RENDER_URL": clean_cell(item.get("LAYOUT_RENDER_URL")),
            "UPHOLSTERY/STONE_FINISH": clean_cell(item.get("UPHOLSTERY/STONE_FINISH")).replace("\n", " ").replace("\r", " "),
            "CAD_urls": get_value(item, "CAD_urls", "CAD_URLS"),
            "Job_Card_Url": jobCardUrl
        }
        rows.append(row)
    return rows



def find_gst_by_vendor(sample_vendor_name, GSTNum, threshold=94):
    """
    Reads vendor->GST JSON mapping
    and returns GST if vendor name matches > threshold.

    Args:
        json_path (str)
        sample_vendor_name (str)
        threshold (float)

    Returns:
        GST Number or "NA"
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "vendor_gst_mapping.json")

    # Load JSON
    with open(json_path, "r") as f:
        vendor_mapping = json.load(f)

    sample_vendor_name = sample_vendor_name.upper().strip().replace("&", "AND").replace(",", "").replace(".", "")

    best_match = None
    best_score = 0
    Vendor_Name = "NA"

    for vendor_name, gst in vendor_mapping.items():

        cleaned_vendor = vendor_name.upper().strip().replace("&", "AND").replace(",", "").replace(".", "")
        cleanedvendowNameLen=len(cleaned_vendor)
        score = fuzz.ratio(sample_vendor_name[:cleanedvendowNameLen], cleaned_vendor)

        if score > best_score:
            best_score = score
            best_match = gst
            Vendor_Name=vendor_name

        if score >= 98:
            print(f"Exact match found for vendor name: `{vendor_name}` with score {score}. Returning early")
            return gst, vendor_name

    print(f"Best Match Score: `{best_score}`, with vendor name: `{Vendor_Name}`")

    if best_score >= threshold:
        print(f"Vendor name matched with score {best_score}.")
        return best_match, Vendor_Name
    else:
        print(f"No matching vendor found with score >= {threshold}.")
        return GSTNum, sample_vendor_name
    
