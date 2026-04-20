#!/bin/bash
# Package HDProcessor.app into a distributable DMG.
# Run from the repo root after: pyinstaller build_mac.spec

set -e

APP="dist/HDProcessor.app"
DMG="dist/HDProcessor.dmg"
VOL="HD Adjustment Processor"
TMP_DIR=$(mktemp -d)

echo "▸ Packaging $APP → $DMG"

if [ ! -d "$APP" ]; then
  echo "ERROR: $APP not found. Run: pyinstaller build_mac.spec first."
  exit 1
fi

# Create staging directory with app + Applications symlink
cp -r "$APP" "$TMP_DIR/HDProcessor.app"
ln -s /Applications "$TMP_DIR/Applications"

# Create DMG from staging directory
hdiutil create \
  -volname "$VOL" \
  -srcfolder "$TMP_DIR" \
  -ov \
  -format UDZO \
  "$DMG"

rm -rf "$TMP_DIR"
echo "✓ DMG created: $DMG"
