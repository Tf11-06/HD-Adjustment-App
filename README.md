# HD Adjustment Processor

Desktop app for Klear Concepts. Parses Home Depot Credit/Debit Adjustment PDFs and appends data to a Google Sheet.

## Client Setup (running HDProcessor.exe)

1. Download `HDProcessor.exe` and place it in any folder
2. Go to https://console.cloud.google.com — create a new project
3. Enable the **Google Sheets API** for that project
4. Go to IAM & Admin → Service Accounts → Create Service Account → Download JSON key
5. Rename the key file to `service_account.json` and place it in the same folder as `HDProcessor.exe`
6. Create a new Google Sheet; copy the Sheet ID from the URL (the string between `/d/` and `/edit`)
7. Share the Google Sheet with the service account email (`client_email` field inside `service_account.json`) — give it **Editor** access
8. Run `HDProcessor.exe`, click ⚙ Settings, paste the Sheet ID, verify the credentials path, click Save
9. Drop any Home Depot 812 PDF onto the drop zone to begin

## Developer: Rebuild the .exe

Requirements: Python 3.10+, all packages in `requirements.txt`, `service_account.json` present in the project folder (can be a placeholder `{}` for dev builds).

```bash
pip install -r requirements.txt
# If service_account.json doesn't exist yet:
echo '{}' > service_account.json
pyinstaller build.spec
# Output: dist/HDProcessor.exe
```

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
