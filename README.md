# HD Adjustment Processor
### Klear Concepts — Home Depot Vendor Tool

Automatically reads your Home Depot Credit/Debit Adjustment PDFs and logs every line item into a Google Sheet — no manual data entry.

---

## What You Need Before Starting

- The two files Tai sent you:
  - `HDProcessor.exe`
  - `service_account.json`
- A Google account
- An internet connection

---

## Step 1: Create a Folder for the App

Create a new folder anywhere on your computer — for example on your Desktop named `HD Processor`.

Place **both files** in that folder:

```
HD Processor/
├── HDProcessor.exe
└── service_account.json
```

> These two files must always stay in the same folder together. If you move one, move both.

---

## Step 2: Create Your Google Sheet

This is the spreadsheet where all your adjustment data will be saved.

1. Go to [https://sheets.google.com](https://sheets.google.com) and sign in with your Google account
2. Click the + button (Blank spreadsheet) to create a new sheet
3. Name it something recognizable — for example: `HD Adjustments 2025`

---

## Step 3: Copy Your Sheet ID

The Sheet ID is a unique code in the URL of your spreadsheet. You'll need it in Step 5.

1. Look at the URL in your browser — it looks like this:
   ```
   https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
   ```
2. The Sheet ID is the long string of letters and numbers **between `/d/` and `/edit`**
   ```
   1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
   ```
3. Copy it and keep it handy (paste it into Notepad if needed)

---

## Step 4: Share Your Sheet with the App

The app connects to Google Sheets using a special service account. You need to give it access to your sheet.

1. Open `service_account.json` in Notepad (right-click the file → Open with → Notepad)
2. Look for the line that says `"client_email"` — copy the email address next to it
   - It looks like: `hd-processor@your-project.iam.gserviceaccount.com`
3. Go back to your Google Sheet
4. Click the **Share** button in the top-right corner
5. Paste that email address into the "Add people" field
6. Make sure permission is set to **Editor**
7. Click **Send**

> You only need to do Steps 2–7 once. After that, the app has permanent access to this sheet.

---

## Step 5: Run the App and Enter Your Settings

1. Double-click `HDProcessor.exe` to open the app

   > **Windows Security Warning:** If Windows shows a blue "Windows protected your PC" message, click **More info** → **Run anyway**. This is normal for apps that aren't from the Microsoft Store.

2. Click the **⚙ Settings** button in the top-right corner of the app

3. In the **Google Sheet ID** field, paste the Sheet ID you copied in Step 3

4. The **Credentials File** field should already say `service_account.json` — leave it as-is as long as both files are in the same folder

5. Click **Save**

The status bar at the bottom will say **"Settings saved."**

---

## Step 6: Process Your First PDF

1. Locate a Home Depot Credit/Debit Adjustment PDF on your computer
2. Drag and drop the PDF file onto the drop zone in the app

   **Or** click the drop zone to browse and select a file manually

3. The status bar will show the progress and then:
   ```
   ✓ Done — 1 invoice added to sheet.
   ```

4. Open your Google Sheet — you will see:
   - A new tab called **Adjustments** has been created automatically
   - Two header rows: one with the column names, one labeling the LINE ITEM groups
   - One data row per invoice, with line items extending to the right as column groups

---

## Day-to-Day Use

Once setup is complete, using the app is simple:

1. Open `HDProcessor.exe`
2. Drag and drop one or more PDF files onto the drop zone
3. The app processes them in order and adds the rows to your sheet
4. Close the app when done

**Processing multiple PDFs at once:** You can select several PDFs in File Explorer (hold Ctrl and click each one) and drag them all onto the drop zone at the same time. The app will process them one by one.

---

## Duplicate Invoice Warning

If you drop a PDF whose invoice number is already in your sheet, the app will ask:

> **Invoice #XXXXX already exists in the sheet.**
> Add anyway or skip?

- Click **Skip** to leave the sheet unchanged
- Click **Add Anyway** to add the rows again (useful if you need to re-import corrected data)

---

## What Gets Logged

Every PDF produces **one row** in the sheet. Each row starts with 12 invoice-level columns, then line item groups extend to the right:

**Invoice columns (always present):**

| Column | What it is |
|--------|-----------|
| Invoice # | Your invoice number |
| Order # | HD order number |
| Adjustment # | The HD adjustment document number |
| Adjustment Date | Date the adjustment was issued |
| Invoice Date | Your invoice date |
| PO Date | HD purchase order date |
| Credit/Debit | Whether this is a credit or debit |
| Total Amount | Total adjustment amount |
| Handling | Handling charges |
| Store # | HD store number |
| Vendor # | Your vendor number |
| Dept # | HD department number |

**Line item columns (one group per line item, labeled LINE ITEM 1, LINE ITEM 2, etc.):**

| Column | What it is |
|--------|-----------|
| SKU | Home Depot SKU |
| Vendor PN | Your part number |
| UPC/GTIN | Product barcode |
| Sellers Inv # | Your sellers invoice reference |
| Line C/D | Line-level credit or debit |
| QTY | Quantity |
| Unit | Unit of measure (EA, etc.) |
| Unit Price | Unit cost price |
| Item Total | Total for this line item |

If a PDF has 3 line items, the row will have 12 + (9 × 3) = 39 columns. The sheet header expands automatically if a future invoice has more line items than any previous one.

---

## Troubleshooting

**"Sheet ID not configured"**
Open ⚙ Settings and make sure you've pasted your Sheet ID and clicked Save.

**"Credentials file not found"**
Make sure `service_account.json` is in the same folder as `HDProcessor.exe`. If you moved the exe, copy the json file there too.

**"Could not authenticate with Google"**
The `service_account.json` file may be corrupted or invalid. Contact Klear Concepts for a replacement file.

**"Could not find the Google Sheet"**
Double-check the Sheet ID in Settings — make sure you copied the full ID from the URL with no extra spaces.

**"Could not connect to Google Sheets"**
Check your internet connection and try again. If the problem persists, contact Klear Concepts.

**"No line items detected"**
The PDF was processed but no line item data could be read. A row was still added with the header information. This may mean the PDF format is different from a standard Home Depot 812 document — contact Klear Concepts with the PDF attached.

**Windows shows a security warning when opening the app**
Click **More info** → **Run anyway**. This is expected for unsigned apps distributed outside the Microsoft Store.

---

## Need Help?

Contact Tai and include:
- A description of what happened
- The name of the PDF you were trying to process (attach it if possible)
- A screenshot of any error message in the app

