import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models import JobStatus
from app.workers.celery_app import celery_app

router = APIRouter()


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(websocket: WebSocket, job_id: str):
    """
    WebSocket que pushea el progreso de un job cada 500ms.
    El frontend se conecta aquí para actualizaciones en tiempo real.
    """
    await websocket.accept()

    try:
        while True:
            result = celery_app.AsyncResult(job_id)

            if result.state == "PENDING":
                payload = {
                    "job_id": job_id,
                    "status": JobStatus.PENDING,
                    "progress": 0.0,
                    "message": "En cola...",
                }

            elif result.state in ("DOWNLOADING", "PROCESSING", "STARTED"):
                meta = result.info or {}
                payload = {
                    "job_id": job_id,
                    "status": meta.get("status", JobStatus.DOWNLOADING),
                    "progress": meta.get("progress", 0.0),
                    "speed": meta.get("speed"),
                    "eta": meta.get("eta"),
                    "message": meta.get("message"),
                }

            elif result.state == "SUCCESS":
                data = result.result or {}
                payload = {
                    "job_id": job_id,
                    "status": JobStatus.COMPLETED,
                    "progress": 100.0,
                    "filename": data.get("filename"),
                    "filesize": data.get("filesize"),
                    "message": "Descarga completada",
                }
                await websocket.send_text(json.dumps(payload))
                break  # Job terminado, cerramos el socket

            elif result.state == "FAILURE":
                payload = {
                    "job_id": job_id,
                    "status": JobStatus.FAILED,
                    "progress": 0.0,
                    "message": str(result.info),
                }
                await websocket.send_text(json.dumps(payload))
                break

            else:
                payload = {
                    "job_id": job_id,
                    "status": "unknown",
                    "progress": 0.0,
                }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
