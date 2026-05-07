# HD Adjustment Processor

**By Klear Concepts - Home Depot Vendor Tool**

HD Adjustment Processor reads Home Depot 812 Credit/Debit Adjustment PDFs and logs each invoice into either Google Sheets or a local Excel workbook. Drop up to 20 PDFs at once; each invoice becomes one row, and line item columns expand automatically.

## Download

Download the latest installer from the [Releases page](../../releases/latest).

| Computer | Download |
| --- | --- |
| Windows | `HDProcessor-Setup.exe` |
| Mac | `HDProcessor.dmg` |

Klear Concepts provides Google Sheets access through Klear's Google Cloud project, Google Sheets API setup, and service account credentials. The client does not need to create a Google Cloud project.

## Before You Start

You will need:

| Item | Notes |
| --- | --- |
| The app installer | Download from GitHub Releases |
| `service_account.json` | Provided by Klear Concepts if you will use Google Sheets |
| A blank Google Sheet | Used for Google Sheets output |
| An internet connection | Required for Google Sheets output |

Excel output does not need a Google account or credentials file.

## Install

### Windows

1. Download `HDProcessor-Setup.exe`.
2. Double-click the installer.
3. If Windows shows **Windows protected your PC**, click **More info**, then **Run anyway**.
4. Finish the installer.
5. Open **HD Adjustment Processor** from the Start Menu.

### Mac

1. Download `HDProcessor.dmg`.
2. Open the DMG.
3. Drag **HDProcessor** into **Applications**.
4. On first launch, macOS may block the app because it is not from the App Store. Open **System Settings -> Privacy & Security**, then choose **Open Anyway**.

## Google Sheets Setup

Use this route when invoices should go into a shared Google Sheet.

### 1. Create or Open the Sheet

1. Go to [sheets.google.com](https://sheets.google.com).
2. Create a blank spreadsheet.
3. Name it something clear, such as `HD Adjustments 2026`.
4. Keep the first worksheet blank. The app creates the headers automatically.

### 2. Copy the Sheet ID

Copy the long value between `/d/` and `/edit` in the sheet URL.

Example:

```text
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
```

Sheet ID:

```text
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

### 3. Share the Sheet with Klear's Service Account

Klear Concepts supplies a `service_account.json` file for this app.

1. Open `service_account.json` in Notepad, TextEdit, or another text editor.
2. Find the `client_email` value.
3. Open the Google Sheet.
4. Click **Share**.
5. Add the service account email.
6. Set permission to **Editor**.
7. Click **Share** or **Send**. It is fine if Google says the account cannot receive notifications.

This only needs to be done once per spreadsheet.

## Excel Setup

Use this route when invoices should go into a local `.xlsx` file.

Choose where the file should live, for example:

```text
Desktop/HD Adjustments 2026.xlsx
```

The app creates the workbook automatically the first time it writes an invoice.

## Configure the App

1. Open **HD Adjustment Processor**.
2. Click **Settings**.
3. For Google Sheets:
   - Paste the **Sheet ID**.
   - Click **Browse** beside **Credentials File** and select the Klear-provided `service_account.json`.
   - Leave **Worksheet Name** as `Adjustments` unless Klear tells you otherwise.
4. For Excel:
   - Click **Browse** beside **Excel File Path**.
   - Choose where the workbook should be created or updated.
5. Click **Save Settings**.

The app stores settings in your user profile:

| System | Settings location |
| --- | --- |
| Windows | `%APPDATA%/Klear Concepts/HD Adjustment Processor/config.json` |
| Mac | `~/Library/Application Support/Klear Concepts/HD Adjustment Processor/config.json` |

Do not place credentials inside Program Files or inside the Mac `.app` bundle. Use **Settings -> Browse** to select the credentials file.

## Process PDFs

1. Choose the destination at the top of the app:
   - **Google Sheets**
   - **Excel File**
2. Drag one or more Home Depot 812 adjustment PDFs onto the drop zone.
3. Wait for the progress bar to finish.
4. Open the Google Sheet or Excel workbook to confirm the invoice row was added.

You can drop up to 20 PDFs at once. The app processes them one by one.

## Duplicate Invoices

If an invoice number already exists in the destination, the app asks what to do.

| Button | Result |
| --- | --- |
| Skip | Do not add this invoice |
| Skip All | Skip this and all remaining duplicates in the batch |
| Add Anyway | Add this invoice again |
| Add All | Add this and all remaining duplicates in the batch |

## What Gets Logged

Every PDF produces one spreadsheet row.

Invoice details use the first 12 columns:

| Field | Description |
| --- | --- |
| Invoice # | Vendor invoice number |
| Order # | Home Depot order number |
| Adjustment # | Home Depot adjustment document number |
| Adjustment Date | Adjustment issue date |
| Invoice Date | Vendor invoice date |
| PO Date | Purchase order date |
| Credit/Debit | Credit or debit indicator |
| Total Amount | Total adjustment amount |
| Handling | Handling value |
| Store # | Home Depot store number |
| Vendor # | Vendor number |
| Dept # | Department number |

Line item groups appear to the right:

| Group | Description |
| --- | --- |
| `LINE ITEM 1 · Credit` | Credit summary row. Only adjustment reason, seller invoice, credit/debit, and item total are populated. |
| `LINE ITEM 2+ · Debit` | Product debit rows with SKU, vendor part number, quantity, unit, unit price, and item total. |

If a PDF has 4 debit line items, the output has 12 invoice columns plus 5 line item groups: one credit summary group and four debit groups.

## Troubleshooting

| Message or issue | Fix |
| --- | --- |
| `Sheet ID not configured` | Open Settings, paste the Sheet ID, and save. |
| `Excel file not configured` | Open Settings, choose an Excel path, and save. |
| `Credentials file not found` | Open Settings and browse to the Klear-provided `service_account.json`. |
| `Could not authenticate with Google` | The credentials file is invalid or not the Klear-provided file. Contact Klear Concepts. |
| `Could not find the Google Sheet` | Check the Sheet ID and confirm the sheet was shared with Klear's service account as Editor. |
| `Could not connect to Google Sheets` | Check the internet connection and try again. |
| PDF cannot be read | Confirm the file is a valid Home Depot 812 adjustment PDF. |
| Windows security warning | Click **More info**, then **Run anyway**. |
| Mac cannot open app | Use **System Settings -> Privacy & Security -> Open Anyway**. |

## Developer Notes

Developer build, testing, and delivery details live in:

- [docs/DELIVERY.md](docs/DELIVERY.md)
- [docs/TESTING.md](docs/TESTING.md)

Run the local test suite with:

```bash
python3 -m pytest -q
```
