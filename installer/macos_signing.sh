#!/bin/bash
# Sign and notarize the macOS app/DMG when Apple Developer credentials are
# available in CI. If no signing secrets are present, this script exits
# successfully so internal/test builds can still be produced.

set -euo pipefail

MODE="${1:-}"
APP="dist/HDProcessor.app"
DMG="dist/HDProcessor.dmg"
ENTITLEMENTS="installer/macos_entitlements.plist"
KEYCHAIN_PATH="${RUNNER_TEMP:-/tmp}/hdprocessor-signing.keychain-db"
KEYCHAIN_PASSWORD="${KEYCHAIN_PASSWORD:-$(uuidgen)}"

required_vars=(
  APPLE_CERTIFICATE_BASE64
  APPLE_CERTIFICATE_PASSWORD
  APPLE_DEVELOPER_ID_APPLICATION
  APPLE_ID
  APPLE_TEAM_ID
  APPLE_APP_SPECIFIC_PASSWORD
)

_has_any_secret() {
  for name in "${required_vars[@]}"; do
    if [ -n "${!name:-}" ]; then
      return 0
    fi
  done
  return 1
}

_has_all_secrets() {
  for name in "${required_vars[@]}"; do
    if [ -z "${!name:-}" ]; then
      echo "ERROR: Missing required Apple signing secret: $name"
      return 1
    fi
  done
  return 0
}

_skip_if_unsigned_build() {
  if ! _has_any_secret; then
    echo "Apple signing secrets are not configured; skipping macOS signing/notarization."
    echo "The DMG will build, but Gatekeeper will warn that Apple cannot verify it."
    exit 0
  fi
  _has_all_secrets
}

_prepare_keychain() {
  if security find-identity -v -p codesigning "$KEYCHAIN_PATH" >/dev/null 2>&1; then
    return
  fi

  CERT_PATH="${RUNNER_TEMP:-/tmp}/hdprocessor-certificate.p12"
  echo "$APPLE_CERTIFICATE_BASE64" | base64 --decode > "$CERT_PATH"

  security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
  security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
  security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
  security import "$CERT_PATH" \
    -P "$APPLE_CERTIFICATE_PASSWORD" \
    -A \
    -t cert \
    -f pkcs12 \
    -k "$KEYCHAIN_PATH"
  security list-keychains -d user -s "$KEYCHAIN_PATH"
  security set-key-partition-list \
    -S apple-tool:,apple: \
    -s \
    -k "$KEYCHAIN_PASSWORD" \
    "$KEYCHAIN_PATH"
}

case "$MODE" in
  sign-app)
    _skip_if_unsigned_build
    _prepare_keychain
    echo "Signing $APP"
    codesign \
      --force \
      --deep \
      --options runtime \
      --timestamp \
      --entitlements "$ENTITLEMENTS" \
      --sign "$APPLE_DEVELOPER_ID_APPLICATION" \
      "$APP"
    codesign --verify --deep --strict --verbose=2 "$APP"
    ;;

  notarize-dmg)
    _skip_if_unsigned_build
    _prepare_keychain
    echo "Signing $DMG"
    codesign \
      --force \
      --timestamp \
      --sign "$APPLE_DEVELOPER_ID_APPLICATION" \
      "$DMG"
    codesign --verify --verbose=2 "$DMG"

    echo "Submitting $DMG for notarization"
    xcrun notarytool submit "$DMG" \
      --apple-id "$APPLE_ID" \
      --team-id "$APPLE_TEAM_ID" \
      --password "$APPLE_APP_SPECIFIC_PASSWORD" \
      --wait

    xcrun stapler staple "$DMG"
    spctl -a -vv -t open --context context:primary-signature "$DMG"
    ;;

  *)
    echo "Usage: $0 sign-app|notarize-dmg"
    exit 2
    ;;
esac
