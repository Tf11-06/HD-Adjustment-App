#!/bin/bash
# Package HDProcessor.app into a distributable DMG.
# Run from the repo root after: pyinstaller build_mac.spec

set -e

APP="dist/HDProcessor.app"
DMG="${DMG_PATH:-dist/HDProcessor.dmg}"
RW_DMG="${RW_DMG_PATH:-${DMG%.dmg}-rw.dmg}"
VOL="HD Adjustment Processor"
TMP_DIR=$(mktemp -d)
MOUNT_DIR=$(mktemp -d)

echo "▸ Packaging $APP → $DMG"

if [ ! -d "$APP" ]; then
  echo "ERROR: $APP not found. Run: pyinstaller build_mac.spec first."
  exit 1
fi

if python3 -m dmgbuild --help >/dev/null 2>&1; then
  echo "▸ Building polished DMG layout with dmgbuild"
  rm -f "$DMG"
  python3 -m dmgbuild \
    -s installer/dmg_settings.py \
    "$VOL" \
    "$DMG"
  echo "✓ DMG created: $DMG"
  exit 0
fi

echo "▸ dmgbuild not found; using hdiutil/Finder fallback"

cleanup() {
  if mount | grep -q "$MOUNT_DIR"; then
    hdiutil detach "$MOUNT_DIR" -quiet || true
  fi
  rm -rf "$TMP_DIR" "$MOUNT_DIR" "$RW_DMG"
}
trap cleanup EXIT

rm -f "$DMG" "$RW_DMG"

# Create staging directory with app + Applications symlink.
cp -r "$APP" "$TMP_DIR/HDProcessor.app"
ln -s /Applications "$TMP_DIR/Applications"

# Create a temporary read/write DMG so Finder layout metadata can be saved.
hdiutil create \
  -volname "$VOL" \
  -srcfolder "$TMP_DIR" \
  -ov \
  -format UDRW \
  "$RW_DMG"

echo "▸ Styling DMG Finder window"
hdiutil attach "$RW_DMG" \
  -mountpoint "$MOUNT_DIR" \
  -noverify \
  -quiet

# Make the installer feel like a polished drag-to-Applications DMG.
# If Finder scripting is unavailable in CI, keep the DMG valid and continue.
if osascript <<OSA
tell application "Finder"
  tell disk "$VOL"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set bounds of container window to {100, 100, 860, 560}

    set viewOptions to icon view options of container window
    set arrangement of viewOptions to not arranged
    set icon size of viewOptions to 136
    set text size of viewOptions to 14
    set background color of viewOptions to {62194, 62451, 63222}

    set position of item "HDProcessor.app" to {210, 235}
    set position of item "Applications" to {585, 235}

    update without registering applications
    delay 1
    close
    open
    delay 1
    close
  end tell
end tell
OSA
then
  echo "✓ Finder layout saved"
else
  echo "WARNING: Could not style Finder window; continuing with plain DMG."
fi

bless --folder "$MOUNT_DIR" --openfolder "$MOUNT_DIR" 2>/dev/null || true

sync
hdiutil detach "$MOUNT_DIR" -quiet

# Convert the styled image to the compressed read-only DMG clients download.
hdiutil convert "$RW_DMG" \
  -format UDZO \
  -imagekey zlib-level=9 \
  -o "$DMG" \
  -quiet

echo "✓ DMG created: $DMG"
