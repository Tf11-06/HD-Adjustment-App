# Changelog

## Unreleased

- Prepared the repository for client-facing GitHub Releases.
- Moved app settings to a user-writable config folder.
- Clarified that Klear Concepts manages Google Cloud, Sheets API access, and service account credentials.
- Updated install, delivery, testing, installer, and release documentation for Windows and Mac.
- Added a polished Mac DMG layout with drag-to-Applications styling.
- Added the HD Adjustment Processor logo across the app, README, and installers.
- Added optional Apple Developer ID signing and notarization for Mac releases.
- Updated the Windows installer to install per-user and avoid Program Files permission issues.
- Added a clearer Excel workbook locked/open error for Windows users.
- Polished the v1.1 UI so the app fills the native window, removed mock traffic-light controls, and added an in-app version label.
- Split Mac releases into native Intel and Apple Silicon DMGs with CI architecture checks.
- Fixed RM returned-goods invoice parsing so adjustment numbers deduplicate correctly and RM lines export into LI2+.
