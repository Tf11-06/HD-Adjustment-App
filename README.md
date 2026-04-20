# HD Adjustment Processor
**By Klear Concepts — Home Depot Vendor Tool**

Automatically reads your Home Depot Credit/Debit Adjustment PDFs and logs every invoice into a Google Sheet or Excel file — no manual data entry, no spreadsheet formulas, no copy-paste.

Drop up to 20 PDFs at once. Each invoice becomes one row. Line items expand to the right automatically.

---

## What You Need Before Starting

Before you open the app for the first time, make sure you have:

| Item | Where to get it |
|------|----------------|
| `HDProcessor.exe` (Windows) **or** `HDProcessor.app` (Mac) | Download from the [Releases page](../../releases/latest) |
| `service_account.json` | Sent to you by Klear Concepts |
| A Google account (for Google Sheets output) | [google.com](https://google.com) |
| Internet connection | — |

---

## Step 1 — Download the App

1. Go to the [**Releases page**](../../releases/latest)
2. Under **Assets**, download the file for your computer:
   - **Windows** → `HDProcessor-Setup.exe`
   - **Mac** → `HDProcessor.dmg`

---

## Step 2 — Install the App

### Windows

1. Double-click `HDProcessor-Setup.exe`
2. If Windows shows a blue **"Windows protected your PC"** warning:
   - Click **More info**
   - Click **Run anyway**
3. Follow the installer (click Next → Install → Finish)
4. The app will be in your Start Menu as **HD Adjustment Processor**

### Mac

1. Double-click `HDProcessor.dmg` to open it
2. Drag **HDProcessor** into the **Applications** folder
3. The first time you open it, Mac may say *"can't be opened because it's from an unidentified developer"*
   - Open **System Settings → Privacy & Security**
   - Scroll down and click **Open Anyway**
   - Click **Open** on the confirmation dialog
   - You only need to do this once

---

## Step 3 — Place Your Files Together

Create a folder anywhere on your computer — for example a folder called `HD Processor` on your Desktop.

Place both files in that folder:

```
HD Processor/
├── HDProcessor.exe        ← the app (Windows)
│   or HDProcessor.app     ← the app (Mac)
└── service_account.json   ← sent by Klear Concepts
```

> These two files must always stay in the same folder. If you ever move the app, move `service_account.json` with it.

---

## Step 4 — Choose Your Output (Google Sheets or Excel)

The app can write to **Google Sheets** or an **Excel file**. You can switch between them anytime with the toggle in the app. Follow the setup steps for whichever you want to use.

---

### Option A — Google Sheets Setup

#### 4A-1. Create a New Spreadsheet

1. Go to [sheets.google.com](https://sheets.google.com) and sign in
2. Click **+** (Blank spreadsheet)
3. Name it something like `HD Adjustments 2025`
4. **The sheet must be blank** — the app will set up all the columns automatically on first use

#### 4A-2. Copy Your Sheet ID

1. Look at the URL in your browser — it looks like:
   ```
   https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
   ```
2. The Sheet ID is the long string **between `/d/` and `/edit`**:
   ```
   1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
   ```
3. Copy it — you'll paste it into the app in Step 5

#### 4A-3. Share the Sheet with the App

The app connects to Google Sheets using a special service account. You need to give it permission to edit your sheet.

1. Open `service_account.json` in Notepad (Windows) or TextEdit (Mac)
2. Find the line that says `"client_email"` — copy the email address next to it
   - It looks like: `hd-processor@your-project.iam.gserviceaccount.com`
3. Go back to your Google Sheet
4. Click **Share** (top-right corner)
5. Paste that email address into the **"Add people"** field
6. Set permission to **Editor**
7. Click **Send** (ignore the warning that this email can't receive notifications)

> You only need to do this once per spreadsheet.

---

### Option B — Excel File Setup

No extra accounts or sharing needed. Just decide where you want the Excel file to live on your computer. The app will create it automatically on first use.

A good location: `Desktop/HD Adjustments 2025.xlsx`

You'll point the app to this path in Step 5.

---

## Step 5 — Configure the App

1. Open **HD Adjustment Processor**
2. Click **⚙ Settings** in the top-right corner
3. Fill in the fields for the output(s) you want to use:

   **Google Sheets section:**
   - **Sheet ID** — paste the ID you copied in Step 4A-2
   - **Credentials File** — click Browse and select your `service_account.json`
   - **Worksheet Name** — leave as `Adjustments` (or type a custom tab name)

   **Excel File section:**
   - **Excel File Path** — click Browse, navigate to where you want the file, type a filename like `HD Adjustments 2025.xlsx`, and click Save

4. Click **Save Settings**

The status bar will confirm: *Settings saved.*

---

## Step 6 — Select Your Destination

In the main app window, use the toggle at the top to choose where invoices go:

- **☁ Google Sheets** — rows are added to your Google Sheet in real time
- **📊 Excel File** — rows are added to your local `.xlsx` file

You can switch this at any time — your settings for both are always saved.

---

## Step 7 — Process Your First Invoice

1. Locate a Home Depot Credit/Debit Adjustment PDF on your computer
2. **Drag and drop** the PDF file onto the drop zone in the app

   **Or** click the drop zone to browse and select files manually

3. The progress bar will appear while it processes
4. When done, the status bar shows:
   ```
   ✓ Done — invoice added to sheet.
   ```
5. Open your Google Sheet or Excel file — you'll see:
   - Row 1: color-coded column group headers (Invoice Details | LINE ITEM 1 · Credit | LINE ITEM 2 · Debit | …)
   - Row 2: field names
   - Row 3+: one row per invoice

---

## Processing Multiple PDFs at Once

You can drop up to **20 PDFs at once**:

1. Open File Explorer (Windows) or Finder (Mac)
2. Hold **Ctrl** (Windows) or **⌘ Command** (Mac) and click each PDF to select multiple
3. Drag them all onto the drop zone at the same time
4. The app processes them one by one and shows progress: *Processing 3 of 20…*

---

## Duplicate Invoice Warning

If you drop a PDF whose invoice number is already in your sheet, the app asks what to do:

| Button | What it does |
|--------|-------------|
| **Skip** | Leave the sheet unchanged for this invoice |
| **Skip All** | Skip this and all remaining duplicates in the batch |
| **Add Anyway** | Add this invoice again (useful for re-importing corrected data) |
| **Add All** | Add this and all remaining duplicates |

---

## What Gets Logged

Every PDF produces **one row**. Each row has:

**Invoice columns (always present — cols A–L):**

| Column | What it is |
|--------|-----------|
| Invoice # | Your invoice number |
| Order # | HD order number |
| Adjustment # | HD adjustment document number |
| Adjustment Date | Date the adjustment was issued |
| Invoice Date | Your invoice date |
| PO Date | HD purchase order date |
| Credit/Debit | Whether this is a credit or debit |
| Total Amount | Total adjustment amount |
| Handling | Handling charges |
| Store # | HD store number |
| Vendor # | Your vendor number |
| Dept # | HD department number |

**LINE ITEM 1 · Credit (cols M–U)** — the net credit summary line:

| Column | What it is |
|--------|-----------|
| Adj Reason | Always `24` (EDI credit summary code) |
| Sellers Inv # | Your invoice number |
| Line C/D | `C - Credit` or `D - Debit` |
| Item Total | Net credit/debit total |
| SKU, Vendor PN, QTY, Unit, Unit Price | Always blank (summary line has no product data) |

**LINE ITEM 2 · Debit, LINE ITEM 3 · Debit, … (cols V onward)** — one group per product line:

| Column | What it is |
|--------|-----------|
| SKU | Home Depot SKU |
| Vendor PN | Your part number |
| Adj Reason | Adjustment reason code (e.g. `06`) |
| Sellers Inv # | Your invoice number |
| Line C/D | `D - Debit` |
| QTY | Quantity |
| Unit | Unit of measure (`EA`) |
| Unit Price | Unit cost price |
| Item Total | Total for this line item |

> If a PDF has 4 debit line items, the row will have 12 + (9 × 5) = 57 columns. The sheet expands automatically when a new invoice has more line items than any previous one.

---

## Troubleshooting

**"Sheet ID not configured"**
Open ⚙ Settings and paste your Google Sheet ID into the Sheet ID field, then click Save.

**"Excel file not configured"**
Open ⚙ Settings, click Browse next to Excel File Path, choose a location and filename, then click Save.

**"Credentials file not found"**
Make sure `service_account.json` is in the same folder as the app. Click Browse in Settings to locate it manually.

**"Could not authenticate with Google"**
Your `service_account.json` file may be corrupted or from the wrong project. Contact Klear Concepts for a replacement.

**"Could not find the Google Sheet"**
Double-check the Sheet ID in Settings — copy it fresh from the browser URL. Make sure there are no extra spaces.

**"Could not connect to Google Sheets"**
Check your internet connection. If the problem persists, contact Klear Concepts.

**Windows shows a security warning when opening the app**
Click **More info** → **Run anyway**. This is expected for apps distributed outside the Microsoft Store.

**Mac says the app can't be opened**
Go to System Settings → Privacy & Security → scroll down → click **Open Anyway**.

**The app processed a PDF but the row looks incomplete**
The PDF may be in a format the app doesn't fully recognize. Contact Klear Concepts and attach the PDF — we can update the app to handle it.

---

## Day-to-Day Use

Once setup is complete:

1. Open **HD Adjustment Processor**
2. Check the destination toggle (Sheets or Excel)
3. Drag and drop your adjustment PDFs
4. Done — close the app when finished

---

## Need Help?

Contact **Tai at Klear Concepts** and include:
- A description of what happened
- The name of the PDF you were processing (attach it if possible)
- A screenshot of any error message shown in the app
