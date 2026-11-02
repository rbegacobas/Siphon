#!/usr/bin/env bash
# ============================================================
# refresh_cookies.sh
# Exporta cookies de YouTube desde el navegador local
# y las coloca en secrets/ con permisos restrictivos.
#
# Uso: ./scripts/refresh_cookies.sh [chrome|firefox|brave|edge]
# ============================================================
set -euo pipefail

BROWSER="${1:-firefox}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="$PROJECT_ROOT/secrets"
COOKIES_FILE="$SECRETS_DIR/yt_cookies.txt"

mkdir -p "$SECRETS_DIR"

echo "→ Exportando cookies de YouTube desde $BROWSER..."
python3 -m yt_dlp \
    --cookies-from-browser "$BROWSER" \
    --cookies "$COOKIES_FILE" \
    --skip-download \
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 2>&1 | tail -3

# yt-dlp guarda TODAS las cookies del navegador (bancos, gobierno, etc.).
# Nos quedamos solo con YouTube/Google; el resto nunca debe salir de esta máquina.
TMP_FILE="$(mktemp)"
awk -F'\t' '/^# Netscape/ || $1 ~ /(^|\.)(youtube\.com|google\.com)$/' "$COOKIES_FILE" > "$TMP_FILE"
mv "$TMP_FILE" "$COOKIES_FILE"

chmod 600 "$COOKIES_FILE"

echo ""
echo "✓ Cookies exportadas a: $COOKIES_FILE"
echo "  Permisos: $(stat -f '%A' "$COOKIES_FILE" 2>/dev/null || stat -c '%a' "$COOKIES_FILE")"
echo "  Tamaño: $(du -h "$COOKIES_FILE" | cut -f1)"
echo ""
echo "→ Reiniciando containers para aplicar..."
cd "$PROJECT_ROOT"
docker compose restart backend worker
echo ""
echo "✓ Listo. Las cookies se cargarán automáticamente."
echo ""
echo "⚠  RECOMENDACIÓN DE SEGURIDAD:"
echo "   Usa una cuenta de Google DEDICADA para este servicio."
echo "   No uses tu cuenta personal."
