# HD Adjustment Processor - Testing Guide

Use this guide before shipping a client release.

## Local Setup

From the repo root:

```bash
python3 --version
pip3 install -r requirements.txt
python3 -m pytest -q
```

Expected result: all tests pass.

## Source App Smoke Test

Run:

```bash
python3 app.py
```

Confirm:

- Window title is **HD Adjustment Processor**.
- Destination toggle shows **Google Sheets** and **Excel File**.
- Settings opens.
- Drop zone accepts PDF files.
- Status starts as ready.

Save Settings and confirm `config.json` is created in the user config folder, not committed to the repo:

| System | Config location |
| --- | --- |
| Windows | `%APPDATA%/Klear Concepts/HD Adjustment Processor/config.json` |
| Mac | `~/Library/Application Support/Klear Concepts/HD Adjustment Processor/config.json` |

## Google Sheets Route

Use Klear Concepts' Google Cloud project, Sheets API, and service account credentials.

1. Create a blank Google Sheet.
2. Share it with the `client_email` from Klear's `service_account.json` as **Editor**.
3. Open the app.
4. In Settings, paste the Sheet ID.
5. Browse to the Klear-provided `service_account.json`.
6. Save Settings.
7. Select **Google Sheets**.
8. Drop one real Home Depot 812 PDF.

Expected:

- Status shows processing, then done.
- The `Adjustments` worksheet exists.
- Row 1 contains group labels.
- Row 2 contains field names.
- Row 3 contains one invoice.
- `LINE ITEM 1 - Credit` contains only the credit summary fields.
- Debit product rows begin in `LINE ITEM 2 - Debit`.

## Excel Route

1. Open Settings.
2. Browse to a test `.xlsx` output path.
3. Save Settings.
4. Select **Excel File**.
5. Drop one real Home Depot 812 PDF.

Expected:

- Workbook is created if missing.
- Headers are written in rows 1 and 2.
- Data starts on row 3.
- Additional PDFs append new rows.
- More debit line items expand columns without removing existing data.

## Duplicate Test

1. Drop a PDF successfully.
2. Drop the same PDF again.

Expected duplicate dialog options:

- **Skip**
- **Skip All**
- **Add Anyway**
- **Add All**

Verify:

- Skip does not add a new row.
- Add Anyway appends a duplicate row.
- Skip All and Add All apply to remaining duplicates in a batch.

## Batch Test

1. Select 2-3 supported PDFs.
2. Drop them together.

Expected:

- Progress shows each file in sequence.
- The app does not start a second batch while processing.
- Final status reports how many invoices were added and skipped.
- Rows appear in the same order the batch was processed.

## Error Scenarios

Test these paths before release:

| Scenario | Expected result |
| --- | --- |
| Empty Sheet ID | `Sheet ID not configured. Open Settings to add it.` |
| Missing credentials file | `Credentials file not found...` |
| Invalid credentials JSON | `Could not authenticate with Google...` |
| Wrong Sheet ID | `Could not find the Google Sheet...` |
| No internet | `Could not connect to Google Sheets...` |
| Missing Excel path | `Excel file not configured...` |
| Invalid or corrupt PDF | `Could not read <filename>...` |
| Non-PDF file | Ignored by drag-and-drop. |

## Built App Tests

### Windows

1. Build or download `HDProcessor-Setup.exe`.
2. Install it.
3. Open from the Start Menu.
4. Configure Settings using a Sheet ID and Klear credentials.
5. Process one PDF to Google Sheets.
6. Process one PDF to Excel.
7. Restart the app and confirm settings persist.

### Mac

1. Build or download `HDProcessor.dmg`.
2. Drag `HDProcessor.app` to Applications.
3. Open the app.
4. Configure Settings using a Sheet ID and Klear credentials.
5. Process one PDF to Google Sheets.
6. Process one PDF to Excel.
7. Restart the app and confirm settings persist.

For a client release, confirm the DMG is notarized:

```bash
spctl -a -vv -t open --context context:primary-signature dist/HDProcessor.dmg
```

Expected: macOS accepts the DMG without the **Apple could not verify** warning. If Gatekeeper blocks it, the release was not built with Apple Developer signing/notarization secrets.

## Release Workflow Test

Use `workflow_dispatch` for a manual build, or push a tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Expected:

- macOS job runs the full test suite.
- Windows job runs the full test suite.
- Mac artifact is `HDProcessor.dmg`.
- Windows artifact is `HDProcessor-Setup.exe`.
- Tagged releases attach both files.

## Final Release Checklist

- [ ] `python3 -m pytest -q` passes.
- [ ] Google Sheets route tested with Klear service account.
- [ ] Excel route tested.
- [ ] Duplicate handling tested.
- [ ] Batch handling tested.
- [ ] Windows installer tested.
- [ ] Mac DMG tested.
- [ ] Mac DMG notarization verified for client release.
- [ ] GitHub Release assets verified.
- [ ] No `service_account.json` committed.
- [ ] No `config.json` committed.
