# YouTube Downloader

Aplicación profesional para descarga de video y audio de YouTube.  
Stack: **FastAPI + Celery + Redis + yt-dlp + FFmpeg + Vue 3**

## Arquitectura

```
┌─────────┐     ┌──────────┐     ┌───────┐     ┌────────┐
│ Vue 3   │────▶│ FastAPI  │────▶│ Redis │◀────│ Celery │
│ Frontend│◀────│ Backend  │     │Broker │     │ Worker │
│ (Nginx) │ WS  │          │     └───────┘     │ yt-dlp │
└─────────┘     └──────────┘                   │ ffmpeg │
                     │                          └────────┘
                     ▼
               ┌──────────┐
               │ Storage  │
               │ (Volume) │
               └──────────┘
```

### Flujo de datos

1. **Extract** → El usuario envía URL → `yt-dlp --dump-json` extrae metadata sin descargar
2. **Select** → El usuario elige calidad (video/audio) y formato de salida
3. **Download** → Se encola un job en Celery → yt-dlp descarga streams → FFmpeg muxea/convierte
4. **Deliver** → WebSocket notifica progreso en tiempo real → Link temporal de descarga

## Requisitos

- Docker & Docker Compose
- (Para desarrollo local): Python 3.12+, Node.js 20+, Redis, FFmpeg, yt-dlp

## Quick Start (Docker)

```bash
# Clonar y levantar
cp .env.example .env
docker compose up --build

# Acceder a:
# Frontend: http://localhost
# API Docs: http://localhost:8000/docs
```

## Desarrollo Local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Necesitas Redis corriendo
redis-server &

# Iniciar API
uvicorn app.main:app --reload --port 8000

# Iniciar Worker (en otra terminal)
celery -A app.workers.celery_app worker --loglevel=info --concurrency=3
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173 (con proxy a backend)
```

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/extract` | Extrae metadata de un video (formatos, título, etc.) |
| POST | `/api/download` | Encola un job de descarga |
| GET | `/api/jobs/{job_id}` | Consulta estado/progreso de un job |
| GET | `/api/download/{job_id}` | Descarga el archivo resultante |
| WS | `/ws/jobs/{job_id}` | WebSocket para progreso en tiempo real |
| POST | `/api/cleanup` | Fuerza purga de archivos expirados |

## Configuración Avanzada

### Cookies de YouTube (Anti-bot)
Si YouTube bloquea las descargas desde tu IP:

```bash
# En .env
YTDLP_COOKIES_FILE=/path/to/cookies.txt

# Exportar cookies con yt-dlp:
yt-dlp --cookies-from-browser chrome --cookies cookies.txt
```

### Proxy
```bash
YTDLP_PROXY=socks5://user:pass@proxy:1080
```

## Estructura del Proyecto

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── models.py            # Schemas Pydantic
│   │   ├── routes/
│   │   │   ├── videos.py        # REST endpoints
│   │   │   └── websocket.py     # WS para progreso real-time
│   │   ├── services/
│   │   │   ├── ytdlp_service.py # Wrapper de yt-dlp (metadata + comandos)
│   │   │   └── storage.py       # Gestión de archivos + TTL cleanup
│   │   └── workers/
│   │       ├── celery_app.py    # Config Celery
│   │       └── tasks.py         # Task de descarga (progress parsing)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.vue              # Componente principal
│   │   ├── main.js
│   │   └── composables/
│   │       └── useApi.js        # API client + WebSocket
│   ├── nginx.conf               # Reverse proxy config
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```

## Notas Técnicas

- **Streaming adaptativo (DASH)**: YouTube separa video y audio en alta resolución. yt-dlp descarga ambos y FFmpeg los une (`--merge-output-format`).
- **Eficiencia de memoria**: yt-dlp escribe a disco directamente. No se carga nunca el archivo completo en RAM.
- **Worker recycling**: Celery recicla workers cada 50 tasks para prevenir memory leaks.
- **TTL automático**: Los archivos descargados se purgan automáticamente tras `MAX_FILE_AGE_MINUTES`.
- **Concurrencia controlada**: `MAX_CONCURRENT_DOWNLOADS` limita workers simultáneos para evitar throttling de Google.
