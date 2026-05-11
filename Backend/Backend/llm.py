from groq import Groq
from dotenv import load_dotenv
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



def extract_bank_transactions(csv_file):
    # Read raw file
    with open(csv_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Find transaction table start
    start_idx = None

    for i, line in enumerate(lines):
        if "Sl. No." in line:
            start_idx = i
            break

    if start_idx is None:
        raise ValueError("Transaction table not found")

    # Parse CSV
    df = pd.read_csv(
        csv_file,
        skiprows=start_idx,
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

    final_df["Transaction Date"] = df.get("Transaction Date")
    final_df["Description"] = df.get("Description")

    final_df["Amount"] = (
        df.get("Amount", "")
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    final_df["Balance"] = (
        df.get("Balance", "")
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    final_df["Dr / Cr"] = (
        df.get(amount_drcr_col)
        if amount_drcr_col
        else ""
    )

    # Remove invalid rows
    final_df = final_df.dropna(subset=["Transaction Date"])

    # Clean values
    final_df = final_df.fillna("")

    # Convert to list of dicts directly usable for Google Sheets
    records = final_df.to_dict(orient="records")

    return records