# HD Adjustment Processor - Delivery Guide

This guide is for preparing a Klear Concepts release. The public setup instructions live in the main `README.md`.

## Release Build

Use GitHub Releases as the official Klear Concepts download location.

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
   - `HDProcessor-Intel.dmg`
   - `HDProcessor-AppleSilicon.dmg`

4. Open the Release in GitHub and confirm all three assets are present before sending the link.

Manual build commands remain available:

```bash
pip install -r requirements.txt
pyinstaller build.spec --noconfirm
pyinstaller build_mac.spec --noconfirm
bash installer/mac_dmg.sh
```

Windows installers must be built on Windows. Mac DMGs must be built on macOS.
The Windows installer is per-user and installs under `%LOCALAPPDATA%/Programs/HD Adjustment Processor` so users do not need admin access.
The released Mac assets are separate native builds: `HDProcessor-Intel.dmg` for Intel Macs and `HDProcessor-AppleSilicon.dmg` for Apple Silicon Macs.

## Mac Gatekeeper Fix

If macOS shows **Apple could not verify "HDProcessor" is free of malware**, the DMG was not notarized by Apple. The reliable release-ready fix is Apple Developer ID signing and notarization.

Add these GitHub Actions secrets before cutting a Mac release:

| Secret | Value |
| --- | --- |
| `APPLE_CERTIFICATE_BASE64` | Base64-encoded `.p12` export of Klear's **Developer ID Application** certificate |
| `APPLE_CERTIFICATE_PASSWORD` | Password used when exporting the `.p12` certificate |
| `APPLE_DEVELOPER_ID_APPLICATION` | Full signing identity, for example `Developer ID Application: Klear Concepts (TEAMID)` |
| `APPLE_ID` | Apple ID email used for notarization |
| `APPLE_TEAM_ID` | Apple Developer Team ID |
| `APPLE_APP_SPECIFIC_PASSWORD` | App-specific password for the Apple ID |

After these secrets are configured, push a new version tag. The macOS workflow signs `HDProcessor.app`, builds the Intel and Apple Silicon DMGs, signs each DMG, submits them to Apple's notary service, staples the notarization tickets, and uploads the notarized release files.

Unsigned internal builds can still be opened with **System Settings -> Privacy & Security -> Open Anyway**, but do not treat that as the final delivery path.

## Klear Google Setup

For Google Sheets output, Klear Concepts owns and manages the Google Cloud setup. End users do not create the Cloud project or API credentials.

1. Create or select Klear Concepts' Google Cloud project for this app.
2. Enable the Google Sheets API.
3. Create a service account.
4. Download the service account JSON key.
5. Rename the file to `service_account.json`.
6. Store it securely outside the Git repo.
7. Share the file through an approved secure channel when Google Sheets output is needed.

Never commit `service_account.json`, `.env` files, or real config files.

## Google Sheet Setup

Create a new Google Sheet or use an existing Klear Concepts sheet.

1. Create a blank Google Sheet.
2. Copy the Sheet ID from the URL.
3. Open the `service_account.json` file.
4. Copy the `client_email`.
5. Share the Google Sheet with that email as **Editor**.
6. Keep the Sheet ID and `service_account.json` available for app setup.

The app creates the `Adjustments` worksheet headers on first write.

## Delivery Package

For GitHub-based delivery, provide:

- Link to the latest GitHub Release.
- `service_account.json`, if Google Sheets output will be used.
- The Sheet ID for the target Google Sheet.

Do not send or include `config.json`. The app creates it after the user saves Settings.

## Setup Walkthrough

1. Download the correct release asset:
   - Windows: `HDProcessor-Setup.exe`
   - Intel Mac: `HDProcessor-Intel.dmg`
   - Apple Silicon Mac: `HDProcessor-AppleSilicon.dmg`
2. Install the app.
3. Open **Settings**.
4. Paste the Sheet ID.
5. Browse to the `service_account.json` file.
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
- [ ] Release contains `HDProcessor-Intel.dmg`.
- [ ] Release contains `HDProcessor-AppleSilicon.dmg`.
- [ ] Intel Mac workflow log confirms the app binary includes `x86_64`.
- [ ] Apple Silicon Mac workflow log confirms the app binary includes `arm64`.
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
| `Credentials file not found` | The saved credentials path is wrong | Browse to the `service_account.json` file again. |
| `Could not authenticate with Google` | Bad or wrong JSON key | Use a fresh service account key from Klear Concepts' Google Cloud setup. |
| `Could not find the Google Sheet` | Wrong Sheet ID or missing share permission | Confirm Sheet ID and Editor access for the service account. |
| `Could not connect to Google Sheets` | Network or Google API issue | Check internet, API status, and retry. |
| `Could not read <file>` | Not a valid supported PDF | Test with a real Home Depot 812 adjustment PDF. |
| `Could not save the Excel workbook` | Workbook is open or locked by Excel/Windows | Close Excel and run the PDFs again. |
