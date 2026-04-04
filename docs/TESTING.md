# HD Adjustment Processor — Mac Testing Guide

Complete step-by-step guide to test the app on your Mac before shipping the Windows version to the client. Follow every section in order.

---

## Part 1: Prerequisites

### 1.1 Confirm Python and dependencies are installed

Open Terminal and run:

```bash
cd "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor"
python3 --version
```

Expected: `Python 3.13.x` (or 3.10+).

```bash
pip3 install -r requirements.txt
```

Expected: All packages install without errors.

### 1.2 Run the unit test suite

```bash
cd "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor"
pytest tests/ -v
```

Expected output:
```
40 passed in X.XXs
```

If any tests fail, stop here and fix before continuing.

---

## Part 2: Google Cloud Setup (one-time)

You need a real Google service account to test the full pipeline. Skip to Part 3 if you already have `service_account.json`.

### 2.1 Create a Google Cloud project

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top-left) → **New Project**
3. Name it `HD Processor Test` → click **Create**
4. Make sure the new project is selected in the dropdown

### 2.2 Enable the Google Sheets API

1. In the left sidebar: **APIs & Services → Library**
2. Search `Google Sheets API` → click it → click **Enable**

### 2.3 Create a service account and download the key

1. Left sidebar: **IAM & Admin → Service Accounts**
2. Click **+ Create Service Account**
3. Name: `hd-processor-test` → click **Create and Continue** → click **Done**
4. Click the new service account email in the list
5. Go to the **Keys** tab → **Add Key → Create new key → JSON → Create**
6. A `.json` file downloads automatically — rename it to `service_account.json`

### 2.4 Create the test Google Sheet

1. Go to [https://sheets.google.com](https://sheets.google.com) → click **+** (Blank spreadsheet)
2. Name it `HD Processor Test`
3. Copy the Sheet ID from the URL: it's the long string between `/d/` and `/edit`
   - Example URL: `https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit`
   - Sheet ID: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms`
4. Save the Sheet ID — you'll need it in the app Settings

### 2.5 Share the sheet with the service account

1. In the Google Sheet, click **Share** (top-right)
2. Open `service_account.json` in a text editor — find the `client_email` field
   - It looks like: `hd-processor-test@hd-processor-test.iam.gserviceaccount.com`
3. Paste that email into the Share dialog
4. Set permission to **Editor** → click **Send**

---

## Part 3: Run the App from Source (python3)

This confirms the app works before testing the built `.app`.

### 3.1 Place the credentials file

Put `service_account.json` in the project folder:
```
hd-adjustment-processor/
├── app.py
├── service_account.json   ← here
├── ...
```

### 3.2 Launch the app

```bash
cd "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor"
python3 app.py
```

Expected: The HD Adjustment Processor window opens. No errors in Terminal.

Visually confirm:
- [ ] Title reads "HD Adjustment Processor"
- [ ] Subtitle reads "Klear Concepts — Home Depot Vendor Tool"
- [ ] Drop zone visible with down-arrow icon
- [ ] Status shows "Ready — drop a PDF to begin"
- [ ] ⚙ Settings button visible in top-right
- [ ] Font looks clean (Helvetica, not pixelated)

### 3.3 Configure settings

1. Click **⚙ Settings**
2. Paste your Sheet ID into the **Google Sheet ID** field
3. Confirm **Credentials File** shows `service_account.json`
4. Click **Save**

Expected: Status changes to "Settings saved."

### 3.4 Confirm config.json was written

In Terminal:
```bash
cat "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/config.json"
```

Expected output (your Sheet ID in place):
```json
{
  "sheet_id": "YOUR_SHEET_ID_HERE",
  "credentials_file": "service_account.json",
  "worksheet_name": "Adjustments"
}
```

Quit the app (Cmd+Q or close window) before moving to the next section.

---

## Part 4: Error Scenario Tests

Test all 7 error paths. Each should show a clear error message in the status bar — **no crashes, no silent failures**.

### Error Test 1: No Sheet ID configured

1. Open `config.json` and set `"sheet_id": ""`
2. Launch the app: `python3 app.py`
3. Drop any PDF onto the drop zone (or click to browse and select one)

Expected status: `Sheet ID not configured. Open Settings to add it.`

Restore the Sheet ID in Settings before continuing.

### Error Test 2: Missing credentials file

1. Temporarily rename `service_account.json` → `service_account.json.bak`
2. Launch the app and drop a PDF

Expected status: `Credentials file not found: .../service_account.json. Check the path in Settings.`

Rename it back before continuing.

### Error Test 3: Wrong credentials file (invalid JSON)

1. Create a fake credentials file:
   ```bash
   echo '{"bad": "data"}' > "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/service_account.json"
   ```
2. Launch the app and drop a PDF

Expected status: `Could not authenticate with Google: ...`

Restore the real `service_account.json` before continuing.

### Error Test 4: Wrong Sheet ID

1. In Settings, change the Sheet ID to `INVALID_SHEET_ID_12345` → Save
2. Drop a PDF

Expected status: `Could not find the Google Sheet. Verify the Sheet ID in Settings.`

Restore the correct Sheet ID in Settings before continuing.

### Error Test 5: Drop a non-PDF or corrupt file

1. Create a fake PDF:
   ```bash
   echo "this is not a pdf" > /tmp/fake.pdf
   ```
2. Drop `/tmp/fake.pdf` onto the drop zone

Expected status: `Could not read fake.pdf. Make sure it's a valid Home Depot adjustment document.`

### Error Test 6: Drop a non-PDF file extension

1. Drag a `.jpg`, `.txt`, or `.png` file onto the drop zone

Expected: Nothing happens (the app silently ignores non-PDF drops). Status stays unchanged.

### Error Test 7: Drop a valid PDF that has no line items

This requires a real PDF that pdfplumber can open but that contains no recognizable 812 line items. Use any generic PDF (a resume, receipt, etc.):

1. Rename any non-812 PDF to something ending in `.pdf`
2. Drop it onto the app

Expected status: `Warning: No line items detected in <filename>. Row added with blank item columns.`
And verify a row was still added to the Google Sheet (with the header fields that could be parsed, line item columns blank).

---

## Part 5: Happy Path Test (Real 812 PDF)

This is the core test. You need at least one real Home Depot 812 Credit/Debit Adjustment PDF.

### 5.1 Drop a single 812 PDF

1. Drag a real 812 PDF onto the drop zone
2. Watch the status bar while it processes

Expected status sequence:
- `Processing 1 of 1: <filename>...` (blue)
- `✓ Done — X row(s) added to sheet.` (green)
- "Last processed:" row updates with invoice number, row count, and timestamp

### 5.2 Verify the Google Sheet

Open your Google Sheet. Confirm:

- [ ] A tab named **Adjustments** was created
- [ ] Row 1 is the header with all 22 columns in this exact order:

| Col | Header |
|-----|--------|
| A | Adjustment # |
| B | Adjustment Date |
| C | Invoice # |
| D | Order # |
| E | Invoice Date |
| F | PO Date |
| G | Credit/Debit |
| H | SKU |
| I | Vendor PN |
| J | UPC/GTIN |
| K | Adjustment Reason |
| L | Sellers Invoice # |
| M | Line C/D |
| N | QTY |
| O | Unit |
| P | Unit Price |
| Q | Item Total |
| R | Store # |
| S | Vendor # |
| T | Dept # |
| U | Total Amount |
| V | Handling |

- [ ] One data row per line item in the PDF (if the PDF has 3 line items, there are 3 rows)
- [ ] Columns A–G and R–V (header fields) are identical across all rows from the same PDF
- [ ] Columns H–Q (line item fields) differ per row with actual SKU, QTY, Unit Price, etc.
- [ ] No empty rows, no duplicate header rows

### 5.3 Verify timestamp in "Last processed"

The "Last processed" row at the bottom of the app should show:
```
Invoice #<number> · X row(s) added · <time>
```
- Time should be in 12-hour format (e.g., `9:41 AM` not `09:41 AM`)
- No leading zero on the hour

---

## Part 6: Duplicate Detection Test

### 6.1 Drop the same PDF again

Drag the same 812 PDF you used in Part 5 onto the drop zone.

Expected: A modal dialog appears titled "Duplicate Invoice" with the message:
```
Invoice #<number> already exists in the sheet.
Add anyway or skip?
```
And two buttons: **Add Anyway** and **Skip**

### 6.2 Test the Skip button

Click **Skip**.

Expected:
- Status: `Skipped (duplicate or error).`
- Google Sheet: no new rows added (row count unchanged)

### 6.3 Test the Add Anyway button

Drop the same PDF again → modal appears → click **Add Anyway**.

Expected:
- Status: `✓ Done — X row(s) added to sheet.`
- Google Sheet: same rows now appear twice (the duplicate was added)

Clean up: manually delete the duplicate rows from the sheet before continuing.

---

## Part 7: Batch Processing Test

### 7.1 Drop multiple PDFs at once

Hold Cmd and select 2–3 different 812 PDFs in Finder, then drag them all onto the drop zone at once.

Expected status sequence:
- `Processing 1 of 3: <file1>...`
- `Processing 2 of 3: <file2>...`
- `Processing 3 of 3: <file3>...`
- `Batch complete — 3 of 3 processed, X rows added.`

Expected in Google Sheet: rows from all 3 PDFs appended in order.

### 7.2 Confirm concurrent protection

While a batch is processing, try to click the drop zone or Settings button.

Expected: Nothing happens — the app ignores clicks while processing. The UI does not freeze.

---

## Part 8: Test the Built .app

Repeat the happy path test using the PyInstaller bundle instead of `python3 app.py`.

### 8.1 Confirm the .app exists

```bash
ls "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/dist/"
```

Expected: `HDProcessor.app` is listed. If not, build it first:

```bash
cd "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor"
pyinstaller build_mac.spec --noconfirm
```

### 8.2 Place credentials next to the .app

```bash
cp "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/service_account.json" \
   "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/dist/service_account.json"
```

### 8.3 Open the built .app

```bash
open "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/dist/HDProcessor.app"
```

**If macOS blocks it with "cannot be opened because the developer cannot be verified":**
```bash
xattr -rd com.apple.quarantine "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/dist/HDProcessor.app"
open "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/dist/HDProcessor.app"
```

Expected: App window opens — no Terminal window, no dock Python icon. The app icon in the Dock will be the PyInstaller placeholder for now.

### 8.4 Configure settings in the built .app

1. Click **⚙ Settings**
2. Paste your Sheet ID → click **Save**

### 8.5 Verify config.json writes next to the .app (not inside it)

```bash
ls "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor/dist/"
```

Expected: `config.json` appears here — next to `HDProcessor.app`, NOT inside `HDProcessor.app/Contents/`.

### 8.6 Drop a real 812 PDF onto the built .app

Drag a 812 PDF onto the drop zone of the running `.app`.

Expected: Same behavior as Part 5 — rows appear in the Google Sheet.

### 8.7 Test drag-and-drop (tkinterdnd2 check)

Dragging a file onto the app window must work. If you see "Ready — drop a PDF to begin" stays after dropping a valid PDF with no status change at all, drag-and-drop is broken in the bundle.

Expected: Status updates to "Processing..." immediately after drop.

---

## Part 9: Settings Persistence Test

This confirms config.json survives app restarts.

1. Quit the built `.app` (Cmd+Q)
2. Reopen it: `open dist/HDProcessor.app`
3. Click **⚙ Settings**

Expected: Your Sheet ID and credentials path are pre-filled — they persisted from the previous session.

---

## Part 10: Rebuild Test (clean build)

Confirm a fresh build works end-to-end.

```bash
cd "/Users/tai/Documents/Claude/Projects/Klear Projects/hd-adjustment-processor"
rm -rf dist/ build/
pyinstaller build_mac.spec --noconfirm
```

Expected: Build completes successfully, `dist/HDProcessor.app` created fresh.

Copy credentials back:
```bash
cp service_account.json dist/service_account.json
```

Open and drop a PDF — same result as Part 5.

---

## Test Checklist Summary

### Source (`python3 app.py`)
- [ ] 40 unit tests pass
- [ ] Window opens with correct title, font, layout
- [ ] Settings saves Sheet ID and credentials path
- [ ] config.json written in project folder
- [ ] Error: no Sheet ID → correct message
- [ ] Error: missing credentials → correct message
- [ ] Error: bad credentials → correct message
- [ ] Error: wrong Sheet ID → correct message
- [ ] Error: corrupt PDF → correct message
- [ ] Error: non-PDF extension → silently ignored
- [ ] Error: no line items → warning + blank row added to sheet
- [ ] Happy path: rows appended, 22 columns in correct order
- [ ] Header fields identical across rows from same PDF
- [ ] Line item fields differ per row
- [ ] Timestamp shows correct 12-hr time (no leading zero)
- [ ] Duplicate: modal appears with "Add Anyway" / "Skip" buttons
- [ ] Skip: nothing added to sheet
- [ ] Add Anyway: duplicate row added
- [ ] Batch: multiple PDFs processed in sequence, batch complete message
- [ ] Concurrent lock: clicking during processing does nothing

### Built `.app` (`dist/HDProcessor.app`)
- [ ] App opens without Terminal window
- [ ] Gatekeeper cleared if needed
- [ ] Settings saves and persists after restart
- [ ] config.json lands in `dist/` not inside bundle
- [ ] Drag-and-drop works (tkinterdnd2 functional)
- [ ] Happy path: rows appended to sheet
- [ ] Clean rebuild from scratch succeeds
