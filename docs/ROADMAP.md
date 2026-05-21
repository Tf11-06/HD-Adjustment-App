# HD Adjustment Processor Roadmap

This is the working client-readiness plan for the next polish passes.

## v1.1 Polish

- Fill the native desktop window cleanly.
- Remove mock window controls from the in-app sidebar.
- Show the app version in the UI for support.
- Keep Windows and Mac installers aligned with the same behavior.

## v1.2 Client Support

- Add persistent processing history across app restarts.
- Add a support/debug log file under the user's app config folder.
- Improve user-facing errors for Excel locks, Google Sheet sharing, credentials, quotas, and invalid PDFs.
- Add a clear post-run summary with processed, skipped, and failed counts.
- Add quick actions after success, such as opening the Excel file or Google Sheet.

## Release Quality

- Sign the Windows installer to reduce SmartScreen warnings.
- Sign and notarize the Mac DMG to remove Gatekeeper warnings.
- Keep `service_account.json` and local `config.json` out of GitHub.
- Confirm each tagged release contains `HDProcessor-Setup.exe` and `HDProcessor.dmg`.
