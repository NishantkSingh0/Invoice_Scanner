from groq import Groq
from dotenv import load_dotenv
import io
import os
import pandas as pd
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def llama4Test(prompt="Hello"):
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            temperature=1,
            max_completion_tokens=6000,
            top_p=1,
            stream=False,
        )

        print(completion.choices[0].message.content)

    except Exception as e:
        print("Error in reading sheet", str(e))
        print("Unable to call llama4")



def llama4(prompt, base64_image, content_type='image/jpeg'):

    try:
        # print("llama Called")
        image_data_url = f"data:{content_type};base64,{base64_image}"

        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            temperature=1,
            max_completion_tokens=6000,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"}
        )
        # print("parsed successfully")
        return completion.choices[0].message.content

    except Exception as e:
        print("Error in reading sheet", str(e))
        return "unable to parse"



def extract_bank_transactions(csv_source):
    """
    Parse bank statement CSV from either:
    - file path
    - BytesIO / uploaded file object

    Returns sorted transaction records in ascending date order.
    All rows remain aligned correctly after sorting.
    """

    # Read CSV content
    if isinstance(csv_source, str):
        with open(csv_source, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
    else:
        raw_text = csv_source.read().decode("utf-8", errors="ignore")

    lines = raw_text.splitlines(keepends=True)

    # Find transaction table start
    start_idx = None

    for i, line in enumerate(lines):
        if "Sl. No." in line:
            start_idx = i
            break

    if start_idx is None:
        raise ValueError("Transaction table not found")

    # Create in-memory CSV
    csv_text = "".join(lines[start_idx:])
    text_buffer = io.StringIO(csv_text)

    # Read dataframe
    df = pd.read_csv(
        text_buffer,
        engine="python",
        on_bad_lines="skip"
    )

    # Clean dataframe
    df.columns = [str(col).strip() for col in df.columns]

    # Remove fully empty rows
    df = df.dropna(how="all")

    # Detect Dr/Cr column
    drcr_cols = [c for c in df.columns if "Dr / Cr" in c]

    amount_drcr_col = drcr_cols[0] if drcr_cols else None

    # Parse transaction dates
    transaction_dates = pd.to_datetime(
        df["Transaction Date"],
        format="%d-%m-%Y %H:%M:%S",
        errors="coerce"
    )

    # Remove invalid dates first
    valid_mask = transaction_dates.notna()

    df = df[valid_mask].copy()
    transaction_dates = transaction_dates[valid_mask]

    # Create final dataframe
    final_df = pd.DataFrame()

    # Keep original datetime for accurate sorting
    final_df["_sort_date"] = transaction_dates

    # Month -> Apr-26
    final_df["Month"] = transaction_dates.dt.strftime("%b-%y")

    # Date -> April 1, 2026
    final_df["Date"] = transaction_dates.dt.strftime("%B %-d, %Y")

    # Remarks
    final_df["Remarks"] = df.get("Description", "")

    # Amount processing
    amounts = (
        df.get("Amount", 0)
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    # Convert DR amounts to negative
    if amount_drcr_col:
        amounts = amounts.where(
            df[amount_drcr_col]
            .astype(str)
            .str.strip()
            .str.upper() != "DR",
            -amounts
        )

    final_df["Amount (Rs.)"] = amounts

    # Balance
    final_df["Balance"] = (
        df.get("Balance", "")
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    # Transaction Type
    if amount_drcr_col:
        final_df["Transection Type"] = df[amount_drcr_col].apply(
            lambda x: (
                "Payment"
                if str(x).strip().upper() == "DR"
                else "Receipts"
            )
        )
    else:
        final_df["Transection Type"] = ""

    # Sort by actual datetime
    final_df = final_df.sort_values(
        by="_sort_date",
        ascending=True
    )

    # Remove helper column
    final_df = final_df.drop(columns=["_sort_date"])

    # Clean NaN values
    final_df = final_df.fillna("")

    # Convert to records
    records = final_df.to_dict(orient="records")

    return records