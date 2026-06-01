import pandas as pd
import re
from rapidfuzz import fuzz


def clean_value(value):
    """
    Cleans extracted values
    """
    if pd.isna(value):
        return None

    return str(value).strip()


def extract_metadata(df, max_rows=10):
    """
    Extracts unstructured metadata
    from top rows into dictionary
    """

    metadata = {}

    # Read only top section
    top_df = df.iloc[:max_rows]

    for _, row in top_df.iterrows():

        row_values = [
            clean_value(v)
            for v in row.tolist()
            if clean_value(v)
        ]

        if len(row_values) < 2:
            continue

        # Try detecting key-value pattern
        for i in range(len(row_values) - 1):

            key = row_values[i]
            value = row_values[i + 1]

            # Avoid useless keys
            if len(key) > 50:
                continue

            # Normalize key
            normalized_key = (
                key.upper()
                .replace(" ", "_")
                .replace(":", "")
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

    # Optional important columns
    important_columns = [
        "MODEL NUMBER",
        "PRODUCT NAME",
        "QUANTITY",
        "UPHOLSTERY / STONE FINISH",
        "RATE",
        "TOTAL",
        "SPECIFICATIONS",
    ]

    available_columns = [
        col for col in important_columns
        if col in table_df.columns
    ]

    if available_columns:
        table_df = table_df[available_columns]

    return table_df.reset_index(drop=True)


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

        # Skip empty sheets
        if raw_df.dropna(how="all").empty:
            print("Skipped Empty Sheet")
            continue

        # Extract metadata
        metadata = extract_metadata(raw_df)

        # Detect table
        header_row = detect_table_header(raw_df)

        if header_row is None:
            print("No table found")
            continue

        print(f"Table detected at row {header_row}")

        # Extract structured table
        table_df = extract_table(raw_df, header_row)

        final_output.append({
            "sheet_name": sheet_name,
            "metadata": metadata,
            "table_data": table_df
        })

    return final_output


def RefineSalesOrderData(data):

    metadata = data["metadata"]
    table_data = data["table_data"]

    rows = []

    # If table_data is DataFrame
    if isinstance(table_data, pd.DataFrame):

        table_data = table_data.to_dict(
            orient="records"
        )

    for item in table_data:

        product_name = str(
            item.get("PRODUCT NAME", "")
        ).strip().upper()

        model_number = str(
            item.get("MODEL NUMBER", "")
        ).strip().upper()

        rate_value = str(
            item.get("RATE", "")
        ).strip().upper()

        # Skip summary rows
        if (
            product_name in ["NAN", ""]
            or model_number in ["NAN", ""]
            or "TOTAL" in rate_value
            or "GST" in rate_value
        ):
            continue

        row = {

            # Metadata fields
            "Billing_Name":
                metadata.get("BILLING_NAME_"),

            "Billing_Address":
                metadata.get("BILLING_ADDRESS_"),

            "GST":
                metadata.get("GST_"),

            "Delivery_Address":
                metadata.get("DELIVERY_ADDRESS_"),

            "PO_Num":
                metadata.get("PURCHASE_ORDER_NO_"),

            "PO_Valid_Till":
                metadata.get("PO_VALID_TILL"),

            "Order_Type":
                metadata.get("ORDER_TYPE_"),

            # Product fields
            "Product_Name":
                item.get("PRODUCT NAME"),

            "Model_Number":
                item.get("MODEL NUMBER"),

            "QTY":
                item.get("QUANTITY"),

            "Rate":
                item.get("RATE"),

            "Total":
                item.get("TOTAL"),

            "Specifications":
                item.get("SPECIFICATIONS"),
        }

        rows.append(row)

    return rows



import json
from difflib import SequenceMatcher
import os

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