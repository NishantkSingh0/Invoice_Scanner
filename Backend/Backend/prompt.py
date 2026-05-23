OCR_PROMPT="""You are an Account Manager, Read All invoices Correctly, And Keep balance Structured


Extract These ACCURATELY from Invoices

{
  "VENDOR_NAME": "",
  "GSTIN/UIN": "",            (The GTSTIN Number EXCEPT OF `09AAMCC1953B1ZS`)
  "INVOICE_NO": "",          (Accuracy require! RECHECK)
  "INVOICE_DATE": "",          (Accuracy require!)
  "PO_NO": "",                (Can be written in Top of Invoice with pencil, only If not mentioned You can keep it NA)

  "items": [      (List all products even if it is 15, Fetch Their Details Accurately & ROW-WISE, NO LAZINESS, NO SHORTCUTS)
    {
      "ITEM_DESCRIPTION_AS_PER_INVOICE_OF_SUPPLIER": "",            (The Product Name/Description Should be 100% Same as mentioned, Accuracy require! RECHECK)
      "LEDGER_ACCOUNT": "",
      "QUANTITY": "",         (Accuracy require! RECHECK)
      "UNIT": "",            
      "ITEM_RATE": "",        (Per Unit Cost of Product, Accuracy require! RECHECK)
      "DISCOUNT": "",         (in Percentage only, If not mentioned, keep it NA)
      "HSN/SAC": "",       (Accuracy require!)
      "CGST": "",         (Accuracy require!)
      "SGST": ""         (Accuracy require!)
    }
  ]
}

SMART FIELD MAPPING
- (List all products even if it is 15, MISSING OF ANY SINGLE PRODUCT BECOME A VERY SERIOUS PROBLEM, Fetch Their Details Accurately & ROW-WISE, NO LAZINESS, NO SHORTCUTS),
- The QUANTITY And UnitRate SHOULD BE 100% ACCURATE,
- “VENDOR_NAME”: The supplier/seller/company issuing the invoice, NEVER BE `Crafted Oak & Ore Pvt Ltd`
- "CGST" / "SGST"   (Should be in Percentage Only)
    If only IGST/GST percentage is present:
      CGST = IGST% / 2
      SGST = IGST% / 2
- The Product Description Should be 100% Same as mentioned in Invoice.
- "LEDGER_ACCOUNT" -> PURCHASE / FREIGHT INWARD / LABOUR CHARGES / INSURANCE / PACKING / CREDIT NOTE / NA
- “Purchase Order No” can be written as `PO No`, `Purchase Order No`, `Pur Order No.`, `PO_NO` or something similar
- "ITEM_RATE" can be written as Rate, Price, or something similar
- "Formate Dates in `DD/MM/YYYY` or `DD-MM-YYYY` format.
- If any value is missing, Just put `NA`, don't make guess in critical Fields

ITEM RULES
1. Even on So much products mentioned, Fetch Their Details Accurately, NO LAZINESS, NO SHORTCUTS
2. Each product row becomes one object inside `items`.
3. Freight/service rows should also be included as items.

FINAL RULE
Return ONLY pure valid JSON."""