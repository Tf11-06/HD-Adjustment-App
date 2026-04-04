# HD Adjustment Processor — Client Delivery Guide

Everything Tai needs to do to deliver this app to a client, from build to first successful PDF drop.

---

## Overview

There are two phases:
1. **You do first** — build the EXE, set up Google Cloud, create the sheet, test it yourself
2. **Client walkthrough** — walk them through placing the files and entering their Sheet ID

The client does not touch Google Cloud at all. You set that up entirely. They only need to run the app and enter one ID.

---

## Phase 1: Before You Deliver

### Step 1: Build the Windows EXE

You need to be on a Windows machine or have someone build it on one. Run from the project folder:

```bash
pip install -r requirements.txt
pyinstaller build.spec --noconfirm
```

Output: `dist/HDProcessor.exe`

> If you need to build on Mac first for your own testing, use `pyinstaller build_mac.spec --noconfirm` which produces `dist/HDProcessor.app`. The Windows EXE must be built on Windows — PyInstaller produces platform-specific binaries.

---

### Step 2: Create the Google Cloud Project (one-time per client)

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown at the top → **New Project**
3. Name it something like `HD Processor - [Client Name]` → click **Create**
4. Make sure the new project is selected in the top dropdown before continuing

---

### Step 3: Enable the Google Sheets API

1. In the left sidebar: **APIs & Services → Library**
2. Search `Google Sheets API`
3. Click it → click **Enable**

---

### Step 4: Create a Service Account and Download the Key

1. Left sidebar: **IAM & Admin → Service Accounts**
2. Click **+ Create Service Account**
3. Name: something like `hd-processor` → click **Create and Continue** → click **Done**
4. Click the new service account row in the list
5. Go to the **Keys** tab → **Add Key → Create new key → JSON → Create**
6. A `.json` file downloads automatically — **rename it to `service_account.json`**
7. Keep this file safe — this is what authorizes the app to write to the sheet

---

### Step 5: Create the Google Sheet

You have two options:

**Option A (you create it — recommended):**
1. Go to [https://sheets.google.com](https://sheets.google.com) and sign in with *your* Google account or the client's, depending on who will own the data
2. Click **+** (Blank spreadsheet)
3. Name it something clear: `HD Adjustments 2025` or `[Client Name] HD Adjustments`
4. Copy the Sheet ID from the URL — it's the long string between `/d/` and `/edit`:
   ```
   https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
                                          ↑ this part ↑
   ```
5. Save the Sheet ID — you'll need it in Step 7

**Option B (client creates it):**
Send them these instructions:
- Go to sheets.google.com → click **+**
- Name the sheet
- Copy the Sheet ID from the URL (the long string between `/d/` and `/edit`)
- Send you the Sheet ID

---

### Step 6: Share the Sheet with the Service Account

This is what gives the app permission to write data.

1. Open `service_account.json` in any text editor
2. Find the `"client_email"` field — copy the email address next to it
   - It looks like: `hd-processor@your-project-id.iam.gserviceaccount.com`
3. Open the Google Sheet
4. Click **Share** (top right)
5. Paste the service account email into the "Add people" field
6. Set permission to **Editor**
7. Uncheck "Notify people" (the service account doesn't have an inbox)
8. Click **Share**

---

### Step 7: Test the Full Pipeline Yourself First

Before you hand anything to the client, verify it actually works end-to-end.

1. Place `HDProcessor.exe` and `service_account.json` in the same folder on your test machine
2. Run `HDProcessor.exe`
3. Click **⚙ Settings**
4. Paste the Sheet ID → click **Save**
5. Drop a real Home Depot 812 PDF onto the drop zone
6. Verify:
   - Status shows `✓ Done — 1 invoice added to sheet.`
   - Open the Google Sheet — rows 1 and 2 are the header, row 3 is the invoice data
   - Row 1 labels: Invoice #, Order #, Adjustment #, Adjustment Date, Invoice Date, PO Date, Credit/Debit, Total Amount, Handling, Store #, Vendor #, Dept #, then LINE ITEM 1, LINE ITEM 2, etc.
   - Data in all the right columns — verify Invoice #, amounts, SKUs match the PDF
7. Drop the same PDF again → confirm the duplicate dialog appears
8. Drop 2–3 PDFs at once → confirm batch processing works and each invoice goes on its own row

If anything looks wrong, fix it before delivery. Do not hand over an untested build.

---

### Step 8: Prepare the Delivery Package

Create a folder to send to the client containing exactly two files:

```
HD Processor/
├── HDProcessor.exe
└── service_account.json
```

> Do NOT include `config.json` — that gets created automatically when they save their settings the first time.

Send it however is most convenient — a shared Google Drive folder, Dropbox, USB drive, etc.

---

## Phase 2: Client Walkthrough

Walk the client through this either in person, over a screen share, or by sending these steps. It takes about 5 minutes.

---

### Step 1: Create a Folder

Tell the client to create a new folder on their Desktop (or wherever they prefer) named `HD Processor`.

Move both files into it:
```
HD Processor/
├── HDProcessor.exe
└── service_account.json
```

Emphasize: **these two files must always stay in the same folder together**. If they move one, move both.

---

### Step 2: Get the Sheet ID

If you created the sheet (Option A above), you already have the Sheet ID. Skip to Step 3.

If the client created the sheet, have them:
1. Open the Google Sheet in their browser
2. Look at the URL — copy the long string between `/d/` and `/edit`
3. Read it to you or paste it into a message

---

### Step 3: Run the App and Configure Settings

1. Double-click `HDProcessor.exe`

   > **Windows Security Warning** — if they see a blue "Windows protected your PC" screen, tell them: click **More info** → **Run anyway**. This is normal for apps not from the Microsoft Store. It will only happen the first time.

2. The app window opens. Click **⚙ Settings** in the top-right corner

3. In the **Google Sheet ID** field, paste the Sheet ID

4. The **Credentials File** field should already show `service_account.json` — leave it as-is

5. Click **Save** → status bar shows `Settings saved.`

---

### Step 4: Test with Their First PDF

Have the client drop a real Home Depot 812 PDF onto the drop zone.

Tell them what to watch for:
- Status shows `Processing 1 of 1: [filename]...` in blue while it runs
- Then `✓ Done — 1 invoice added to sheet.` in green when complete
- The "Last processed" row at the bottom updates with the invoice number and time

Then have them open the Google Sheet to confirm the data landed correctly.

---

### Step 5: Show Them Day-to-Day Use

Once it's working, show them the two things they'll use every day:

**Single PDF:**
- Drag a PDF onto the drop zone → done

**Multiple PDFs at once:**
- In File Explorer, select multiple PDFs (hold Ctrl and click each one)
- Drag them all onto the drop zone at the same time
- The app processes them one by one

**Duplicate warning:**
- If they drop a PDF whose invoice number is already in the sheet, a popup will ask: Add Anyway or Skip
- Skip = leave the sheet unchanged
- Add Anyway = add it again (useful if they need to re-import corrected data)

---

## Troubleshooting Reference

Keep this handy during the walkthrough. Each error message maps to a specific fix:

| Error message | What it means | Fix |
|---|---|---|
| `Sheet ID not configured` | Settings were never saved | Click ⚙ Settings, paste Sheet ID, click Save |
| `Credentials file not found` | `service_account.json` is in the wrong place | Make sure it's in the same folder as `HDProcessor.exe` |
| `Could not authenticate with Google` | The JSON file is corrupted or invalid | Send them a fresh `service_account.json` |
| `Could not find the Google Sheet` | Sheet ID is wrong | Double-check the ID in Settings — no extra spaces, full string |
| `Could not connect to Google Sheets` | No internet connection | Check their internet and try again |
| `Could not read [filename]` | The PDF is not a valid 812 document | Only 812 Credit/Debit Adjustment PDFs work |
| `Warning: No line items detected` | PDF was read but no line items found | 812 format may be unusual — send Tai the PDF to diagnose |

---

## Checklist Summary

### Before delivery
- [ ] Windows EXE built (`pyinstaller build.spec`)
- [ ] Google Cloud project created
- [ ] Google Sheets API enabled
- [ ] Service account created and `service_account.json` downloaded
- [ ] Google Sheet created and Sheet ID saved
- [ ] Sheet shared with service account email (Editor access)
- [ ] Full pipeline tested end-to-end with a real 812 PDF
- [ ] Sheet output verified: correct columns, correct data, invoices stacking vertically
- [ ] Duplicate detection tested
- [ ] Delivery package prepared: `HDProcessor.exe` + `service_account.json`

### During client walkthrough
- [ ] Client placed both files in same folder
- [ ] Client ran app (Windows security warning handled if it appeared)
- [ ] Sheet ID entered in Settings and saved
- [ ] First PDF dropped successfully
- [ ] Sheet verified open — data in correct columns
- [ ] Client can drag multiple PDFs at once
- [ ] Duplicate dialog shown and explained
