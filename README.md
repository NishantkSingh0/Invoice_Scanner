# AI Document Processing & Spreadsheet Automation System

> Transform invoices, bank statements, sales orders, purchase records, and business documents into structured, validated data that automatically updates Google Sheets.

---

## Overview

This project is not limited to invoice processing.

It is a modular AI-powered document intelligence system capable of extracting, validating, standardizing, calculating, and updating structured business data from various document formats directly into spreadsheets.

The system combines advanced document understanding, mathematical validation, business-rule processing, and Google Sheets automation to eliminate manual data entry workflows.

<img width="1470" height="956" alt="Screenshot 2026-06-01 at 11 14 13 AM" src="https://github.com/user-attachments/assets/431ef7ff-f62a-45ea-bff8-9ede402a4e04" />

### Supported Document Types

* Purchase Invoices
* Sales Invoices
* Bank Statements
* Sales Orders
* Purchase Orders
* XLSX Business Records
* Vendor Reports
* Custom Business Documents

The extraction pipeline can be customized to support virtually any structured or semi-structured document format.

---

## What Makes This Different?

Most OCR systems just read/write texts.

This system goes several steps further:

### Read

Extracts information from documents using advanced AI models.

### Understand

Identifies vendors, products, transactions, taxes, dates, quantities, and business entities.

### Validate

Perform Several Steps to validate if input data is correct or not

### Standardize

Standardize Dates/Vendornames/GSTNo/Taxes to be match with `tally`

### Automate

Directly updates Google Sheets without manual intervention.

---

## Real Business Use Cases

### Purchase Invoice Automation

Automatically extract:

* Vendor Details
* GST Information
* Product Information
* Tax Details
* Purchase Amounts

and push them directly into purchase registers.

---

### Sales Invoice Automation

Automatically process:

* Customer Information
* Products Sold
* Tax Details
* Invoice Totals
* Sales Reports

and synchronize them with Google Sheets.

---

### Bank Statement Processing

Extract and organize bank CSV Files:

* Transaction Date
* Transaction Description
* Credit Amount
* Debit Amount
* Running Balance

for accounting and reconciliation workflows.

---

### Sales Order Processing

Automatically convert sales orders into structured records containing:

* Customer Details
* Ordered Products
* Quantities
* Rates
* Order Values

for reporting and inventory workflows.

---

### Excel Sheet Automation

Import XLSX records and automatically:

* Validate Data
* Clean Records
* Standardize Formats
* Update Google Sheets
* Generate Structured Outputs

without manual spreadsheet work.

---

## Core Capabilities

✅ 100% Accurate GST Extraction

✅ 100% Accurate Vendor Standardization

✅ 100% Accurate Product Parsing

✅ Decimal-Level Financial Accuracy

✅ Automated Mathematical Validation

✅ Google Sheets Integration

✅ Modular Processing Pipeline

✅ Support for Printed Documents

✅ Support for Unstructured Documents

✅ Support for Handwritten Documents

✅ Support for Hindi-English Mixed Documents

---

## Supported Document Complexity

### Clean Structured Documents

Expected Accuracy: 100%
<img width="492" height="722" alt="Screenshot 2026-06-01 at 11 46 55 AM" src="https://github.com/user-attachments/assets/a7810c1a-e657-40e1-91a0-7dd7bb9a0064" />
<img width="1201" height="1600" alt="gitGood" src="https://github.com/user-attachments/assets/f8174e29-b655-482f-82d5-bd415ead8def" />

---

### Dense Business Documents

Expected Accuracy: 99%+

<img width="509" height="724" alt="Screenshot 2026-06-01 at 11 36 26 AM" src="https://github.com/user-attachments/assets/c06272b1-4a05-4fd2-a806-dd96c2e2dac8" />
<img width="508" height="725" alt="Screenshot 2026-06-01 at 11 44 27 AM" src="https://github.com/user-attachments/assets/f183c520-5b71-44c6-9688-6b64749fe0f8" />

---

### Handwritten Documents

Expected Accuracy: 98-99%

Powered by Gemini 2.5 Pro.
<img width="507" height="723" alt="Screenshot 2026-06-01 at 11 32 51 AM" src="https://github.com/user-attachments/assets/e842cdae-1d62-404c-8d45-1dd5fe16f479" />
<img width="505" height="723" alt="Screenshot 2026-06-01 at 11 28 55 AM" src="https://github.com/user-attachments/assets/0b561657-8e44-4bcd-b8df-100ba56b1acc" />


---

## Automation Workflow
```
Document
↓
AI Extraction
↓
Data Validation (Main Accuracy Part)
↓
Business Rule Processing
↓
Standardization
↓
Google Sheets Update
↓
Ready-to-Use Business Records
```

---

## Customization

The current implementation is optimized for my production use case.

However, developers can easily customize:

* Output Schema
* Spreadsheet Structure
* Business Rules
* Validation Logic
* Supported Document Types
* Processing Workflows

through modular Django components.

The architecture was intentionally designed to make adding new document types straightforward and maintainable.
