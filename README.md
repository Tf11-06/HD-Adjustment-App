# HD Adjustment Processor

<p align="center">
  <img src="assets/app_logo.png" alt="HD Adjustment Processor logo" width="150">
</p>

HD Adjustment Processor is a desktop app built for Klear Concepts to process Home Depot 812 adjustment PDFs. It reads each PDF, pulls out the invoice and line-item details, and adds the results to either Google Sheets or a local Excel workbook.

The app is built for Windows and macOS. No coding or command line setup is required for normal use.

## Download the App

Installers are published on the [latest GitHub Release](../../releases/latest).

| Computer | File to download |
| --- | --- |
| Windows | `HDProcessor-Setup.exe` |
| Mac with an Intel processor | `HDProcessor-Intel.dmg` |
| Mac with Apple Silicon | `HDProcessor-AppleSilicon.dmg` |

On a Mac, open **Apple menu -> About This Mac** if you are not sure which version you need. The chip/processor line will say either Intel or Apple Silicon, such as M1, M2, M3, or M4.

## What You Need

For Excel output, all you need is the app and a place to save the workbook.

For Google Sheets output, you also need:

- A blank Google Sheet.
- The Sheet ID from that Google Sheet.
- The `service_account.json` credentials file for Klear Concepts' Google Sheets connection.
- Internet access.

Google Sheets access runs through Klear Concepts' Google account setup, including the Google Cloud project, Google Sheets API, and service account credentials. End users do not need to create their own Google Cloud project.

## Install

### Windows

1. Download `HDProcessor-Setup.exe` from the latest Release.
2. Double-click the installer.
3. If Windows shows a security warning, click **More info**, then **Run anyway**.
4. Finish the installer.
5. Open **HD Adjustment Processor** from the Start Menu.

The Windows installer is per-user, so it does not require admin access.

### Mac

1. Download the correct DMG for the Mac:
   - Intel Mac: `HDProcessor-Intel.dmg`
   - Apple Silicon Mac: `HDProcessor-AppleSilicon.dmg`
2. Open the DMG.
3. Drag **HDProcessor** into **Applications**.
4. Open the app from Applications.

If macOS says Apple cannot verify the app, use the latest notarized release build. For internal testing only, you can open **System Settings -> Privacy & Security** and choose **Open Anyway**.

## Set Up Google Sheets

Use this option when invoice results should go into a shared Google Sheet.

1. Create a blank Google Sheet.
2. Give it a clear name, such as `HD Adjustments 2026`.
3. Copy the Sheet ID from the URL. It is the long value between `/d/` and `/edit`.

Example URL:

```text
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
```

Sheet ID:

```text
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```

Next, share the sheet with the app:

1. Open the `service_account.json` file in a text editor.
2. Copy the `client_email` value.
3. Open the Google Sheet and click **Share**.
4. Add the service account email.
5. Set permission to **Editor**.
6. Click **Share** or **Send**.

Google may say the service account cannot receive notifications. That is expected.

## Set Up Excel

Use this option when invoice results should go into a local `.xlsx` file.

In the app settings, choose where the workbook should be created or updated. For example:

```text
Desktop/HD Adjustments 2026.xlsx
```

The app creates the workbook and headers automatically the first time it writes an invoice.

Close the workbook before processing PDFs. Excel, especially on Windows, can lock the file while it is open.

## Configure the App

1. Open **HD Adjustment Processor**.
2. Click **Settings**.
3. For Google Sheets:
   - Paste the Sheet ID.
   - Browse to the `service_account.json` file.
   - Leave the worksheet name as `Adjustments` unless instructed otherwise.
4. For Excel:
   - Browse to the `.xlsx` file path you want to use.
5. Click **Save Settings**.

Settings are saved locally on the computer:

| System | Settings location |
| --- | --- |
| Windows | `%APPDATA%/Klear Concepts/HD Adjustment Processor/config.json` |
| Mac | `~/Library/Application Support/Klear Concepts/HD Adjustment Processor/config.json` |

Do not put credentials inside Program Files, inside the Mac app bundle, or in this GitHub repository. Select the credentials file from Settings.

## Process PDFs

1. Choose **Google Sheets** or **Excel File** at the top of the app.
2. Drag up to 20 Home Depot 812 adjustment PDFs into the drop zone.
3. Wait for the status to show that the batch is complete.
4. Open the Google Sheet or Excel workbook and confirm the rows were added.

The app supports standard Home Depot 812 adjustment invoices and RM returned-goods invoices.

## Duplicate Invoices

If an invoice already exists in the destination, the app asks what to do:

| Option | What it does |
| --- | --- |
| Skip | Leaves this invoice out |
| Skip All | Skips this invoice and any other duplicates in the batch |
| Add Anyway | Adds this invoice again |
| Add All | Adds all duplicates in the batch |

RM returned-goods invoices use the adjustment number as the invoice number for duplicate checks.

## Spreadsheet Layout

Each PDF creates one row.

The first columns contain the invoice details:

- Invoice #
- Order #
- Adjustment Date
- Invoice Date
- PO Date
- Credit/Debit
- Total Amount
- Handling
- Store #
- Vendor #
- Dept #

Line-item groups are added to the right. `LINE ITEM 1` is the credit summary when one exists. Debit product rows begin at `LINE ITEM 2` and continue as needed.

RM returned-goods invoices do not have a credit summary, so `LINE ITEM 1` stays blank and RM items begin at `LINE ITEM 2`.

## Troubleshooting

| Issue | What to check |
| --- | --- |
| `Sheet ID not configured` | Open Settings, paste the Sheet ID, and save. |
| `Excel file not configured` | Open Settings, choose an Excel path, and save. |
| `Credentials file not found` | Browse to the `service_account.json` file again. |
| Google authentication fails | Confirm the credentials file is the correct service account file for Klear Concepts' Google Sheets setup. |
| Google Sheet cannot be found | Check the Sheet ID and confirm the sheet is shared with the service account as Editor. |
| Google write quota error | Wait a minute and try the batch again, or process fewer PDFs at once. |
| PDF cannot be read | Confirm it is a valid Home Depot 812 adjustment PDF. |
| Excel write error | Close the workbook in Excel and run the PDFs again. |
| Windows security warning | Click **More info**, then **Run anyway**. |
| Mac security warning | Use the latest notarized release build. Internal testers can use **System Settings -> Privacy & Security -> Open Anyway**. |

## Project Docs

Release, testing, and delivery notes are kept in:

- [docs/DELIVERY.md](docs/DELIVERY.md)
- [docs/TESTING.md](docs/TESTING.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)

Local test command:

```bash
python3 -m pytest -q
```
