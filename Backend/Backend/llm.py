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
    Parse bank statement CSV from either a file path or an in-memory BytesIO buffer.
    No temporary files are written to disk.
    """
    # Normalise input — always work with a decoded text buffer
    if isinstance(csv_source, (str, bytes.__class__)):
        # File path string
        with open(csv_source, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
    else:
        # BytesIO / file-like object
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

    # Build an in-memory text buffer from the relevant lines only
    csv_text = "".join(lines[start_idx:])
    text_buffer = io.StringIO(csv_text)

    # Parse with pandas — no file path needed
    df = pd.read_csv(
        text_buffer,
        engine="python",
        on_bad_lines="skip"
    )

    # Clean columns
    df.columns = [str(col).strip() for col in df.columns]

    # Remove empty rows
    df = df.dropna(how="all")

    # Detect Dr/Cr columns
    drcr_cols = [c for c in df.columns if "Dr / Cr" in c]

    amount_drcr_col = drcr_cols[0] if len(drcr_cols) > 0 else None

    # Final dataframe
    final_df = pd.DataFrame()

    # Convert to datetime first
    transaction_dates = pd.to_datetime(
        df["Transaction Date"],
        format="%d-%m-%Y %H:%M:%S",
        errors="coerce"
    )

    # Month column -> Apr-26
    final_df["Month"] = transaction_dates.dt.strftime("%b-%y")

    # Date column -> April 1, 2026
    final_df["Date"] = transaction_dates.dt.strftime("%B %-d, %Y")
    final_df["Remarks"] = df.get("Description")

    amounts = (
        df.get("Amount", 0)
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    if amount_drcr_col:
        amounts = amounts.where(
            df[amount_drcr_col].str.strip().str.upper() != "DR",
            -amounts
        )

    final_df["Amount (Rs.)"] = amounts

    final_df["Balance"] = (
        df.get("Balance", "")
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    final_df["Transection Type"] = (
        df[amount_drcr_col].apply(
            lambda x: "Payment" if str(x).strip().upper() == "DR" else "Receipts"
        )
        if amount_drcr_col
        else ""
    )

    # Remove invalid rows
    final_df = final_df[transaction_dates.notna()]

    # Clean values
    final_df = final_df.fillna("")

    # Convert to list of dicts directly usable for Google Sheets
    records = final_df.to_dict(orient="records")

    return records