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
# Lee las cookies del navegador SIN conectarse a YouTube: una petición real
# hace que YouTube rote/borre LOGIN_INFO y SID antes de guardarlas.
# Solo se guardan YouTube/Google; el resto (bancos, gobierno...) nunca sale de esta máquina.
python3 - "$BROWSER" "$COOKIES_FILE" <<'PY'
import sys
from yt_dlp.cookies import YoutubeDLCookieJar, extract_cookies_from_browser

jar = YoutubeDLCookieJar(sys.argv[2])
for c in extract_cookies_from_browser(sys.argv[1]):
    d = c.domain.lstrip(".")
    if d in ("youtube.com", "google.com") or d.endswith((".youtube.com", ".google.com")):
        jar.set_cookie(c)
jar.save(ignore_discard=True, ignore_expires=True)
PY

for name in LOGIN_INFO SID SAPISID; do
    awk -F'\t' -v n="$name" '$1 ~ /youtube\.com$/ && $6 == n {f=1} END {exit !f}' "$COOKIES_FILE" \
        || { echo "ERROR: falta $name de youtube.com. ¿Sesión iniciada en YouTube y navegador cerrado?"; exit 1; }
done

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
