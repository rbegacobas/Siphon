import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models import (
    ExtractRequest,
    DownloadRequest,
    DownloadType,
    JobResponse,
    JobStatus,
    VideoMetadata,
)
from app.services.ytdlp_service import extract_metadata
from app.services.storage import find_output_file, get_job_dir, cleanup_expired_files
from app.workers.tasks import download_video
from app.workers.celery_app import celery_app

router = APIRouter(tags=["videos"])


@router.post("/extract", response_model=VideoMetadata)
async def extract_video_metadata(req: ExtractRequest):
    """Extrae metadata y formatos disponibles sin descargar."""
    try:
        metadata = extract_metadata(req.url)
        return metadata
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {e}")


@router.post("/download", response_model=JobResponse)
async def start_download(req: DownloadRequest):
    """Encola un job de descarga y devuelve el job_id."""
    audio_format_id = None
    if req.download_type == DownloadType.VIDEO and req.audio_format_id:
        audio_format_id = req.audio_format_id

    task = download_video.apply_async(
        kwargs={
            "url": req.url,
            "format_id": req.format_id,
            "audio_format_id": audio_format_id,
            "output_format": req.output_format,
        }
    )

    return JobResponse(
        job_id=task.id,
        status=JobStatus.PENDING,
        progress=0.0,
        message="Job encolado",
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """Consulta el estado de un job de descarga."""
    result = celery_app.AsyncResult(job_id)

    if result.state == "PENDING":
        return JobResponse(job_id=job_id, status=JobStatus.PENDING, progress=0.0, message="En cola...")

    if result.state in ("DOWNLOADING", "PROCESSING", "STARTED"):
        meta = result.info or {}
        return JobResponse(
            job_id=job_id,
            status=meta.get("status", JobStatus.DOWNLOADING),
            progress=meta.get("progress", 0.0),
            message=meta.get("message"),
        )

    if result.state == "SUCCESS":
        data = result.result or {}
        return JobResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            progress=100.0,
            filename=data.get("filename"),
            filesize=data.get("filesize"),
            message="Descarga completada",
        )

    if result.state == "FAILURE":
        meta = result.info
        msg = str(meta) if meta else "Error desconocido"
        return JobResponse(
            job_id=job_id,
            status=JobStatus.FAILED,
            progress=0.0,
            message=msg,
        )

    return JobResponse(job_id=job_id, status=JobStatus.PENDING, progress=0.0)


@router.get("/download/{job_id}")
async def download_file(job_id: str):
    """Descarga el archivo resultante de un job completado."""
    result = celery_app.AsyncResult(job_id)

    if result.state != "SUCCESS":
        raise HTTPException(status_code=404, detail="El job aún no ha terminado o falló")

    output_file = find_output_file(job_id)
    if not output_file or not os.path.isfile(output_file):
        raise HTTPException(status_code=404, detail="Archivo no encontrado (puede haber expirado)")

    filename = os.path.basename(output_file)
    return FileResponse(
        path=output_file,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/cleanup")
async def trigger_cleanup():
    """Fuerza limpieza de archivos expirados."""
    removed = cleanup_expired_files()
    return {"removed": removed}
