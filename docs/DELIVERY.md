# HD Adjustment Processor - Delivery Guide

This guide is for Klear Concepts when preparing a client delivery. The client-facing setup lives in the main `README.md`.

## Release Build

Use GitHub Releases as the official client download location.

1. Confirm tests pass:

   ```bash
   python3 -m pytest -q
   ```

2. Create a version tag:

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. GitHub Actions builds and attaches:
   - `HDProcessor-Setup.exe`
   - `HDProcessor.dmg`

4. Open the Release in GitHub and confirm both assets are present before sending the link.

Manual build commands remain available:

```bash
pip install -r requirements.txt
pyinstaller build.spec --noconfirm
pyinstaller build_mac.spec --noconfirm
bash installer/mac_dmg.sh
```

Windows installers must be built on Windows. Mac DMGs must be built on macOS.

## Klear Google Setup

For Google Sheets output, Klear Concepts owns and manages the Google Cloud setup. The client does not create the Cloud project or API credentials.

1. Create or select Klear's Google Cloud project for this client.
2. Enable the Google Sheets API.
3. Create a service account.
4. Download the service account JSON key.
5. Rename the file to `service_account.json`.
6. Store it securely outside the Git repo.
7. Send the file to the client through an approved secure channel when they need Google Sheets output.

Never commit `service_account.json`, `.env` files, or real client config files.

## Client Sheet Setup

The client may create the Google Sheet, or Klear may create it for them.

1. Create a blank Google Sheet.
2. Copy the Sheet ID from the URL.
3. Open Klear's `service_account.json`.
4. Copy the `client_email`.
5. Share the Google Sheet with that email as **Editor**.
6. Give the client the Sheet ID and the `service_account.json` file.

The app creates the `Adjustments` worksheet headers on first write.

## Delivery Package

For GitHub-based delivery, send the client:

- Link to the latest GitHub Release.
- Klear-provided `service_account.json`, if they will use Google Sheets.
- The Sheet ID, if Klear created the sheet.

Do not send or include `config.json`. The app creates it after the user saves Settings.

## Client Walkthrough

1. Download the correct release asset:
   - Windows: `HDProcessor-Setup.exe`
   - Mac: `HDProcessor.dmg`
2. Install the app.
3. Open **Settings**.
4. Paste the Sheet ID.
5. Browse to the Klear-provided `service_account.json`.
6. Choose an Excel file path too, if Excel output will be used.
7. Save Settings.
8. Drop one real Home Depot 812 PDF.
9. Confirm the row appears in Google Sheets or Excel.
10. Drop the same PDF again and explain duplicate options.

Settings are saved under the user's profile:

| System | Config location |
| --- | --- |
| Windows | `%APPDATA%/Klear Concepts/HD Adjustment Processor/config.json` |
| Mac | `~/Library/Application Support/Klear Concepts/HD Adjustment Processor/config.json` |

## Pre-Delivery Checklist

- [ ] Full test suite passes locally.
- [ ] GitHub Actions build succeeds.
- [ ] Release contains `HDProcessor-Setup.exe`.
- [ ] Release contains `HDProcessor.dmg`.
- [ ] Klear service account is active.
- [ ] Target Google Sheet is shared with the service account as Editor.
- [ ] Sheet ID has been copied accurately.
- [ ] A real 812 PDF has been tested through Google Sheets.
- [ ] A real 812 PDF has been tested through Excel.
- [ ] Duplicate dialog has been tested.
- [ ] `service_account.json` is not committed.
- [ ] `config.json` is not committed.

## Troubleshooting

| Error message | Likely cause | Fix |
| --- | --- | --- |
| `Sheet ID not configured` | Settings were not saved | Paste the Sheet ID in Settings and save. |
| `Excel file not configured` | Excel destination has no file path | Choose an `.xlsx` path in Settings. |
| `Credentials file not found` | The saved credentials path is wrong | Browse to the Klear-provided `service_account.json` again. |
| `Could not authenticate with Google` | Bad or wrong JSON key | Provide a fresh Klear service account key. |
| `Could not find the Google Sheet` | Wrong Sheet ID or missing share permission | Confirm Sheet ID and Editor access for the service account. |
| `Could not connect to Google Sheets` | Network or Google API issue | Check internet, API status, and retry. |
| `Could not read <file>` | Not a valid supported PDF | Test with a real Home Depot 812 adjustment PDF. |
