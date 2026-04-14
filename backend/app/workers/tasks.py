import os
import re
import subprocess

from celery import Task
from celery.utils.log import get_task_logger

from app.models import JobStatus
from app.services.storage import get_job_dir, find_output_file
from app.services.ytdlp_service import build_download_command
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


def _parse_progress(line: str) -> dict:
    """Parsea una línea de output de yt-dlp para extraer progreso."""
    info: dict = {}

    # [download]  45.2% of ~120.00MiB at  5.30MiB/s ETA 00:12
    match = re.search(r"\[download\]\s+([\d.]+)%\s+of\s+~?([\d.]+\w+)\s+at\s+([\d.]+\w+/s)\s+ETA\s+(\S+)", line)
    if match:
        info["progress"] = float(match.group(1))
        info["speed"] = match.group(3)
        info["eta"] = match.group(4)
        return info

    # [download] 100% of 120.00MiB
    match = re.search(r"\[download\]\s+100%\s+of", line)
    if match:
        info["progress"] = 100.0
        return info

    # [Merger] Merging formats into ...
    if "[Merger]" in line or "[ffmpeg]" in line or "[ExtractAudio]" in line:
        info["status"] = "processing"
        info["message"] = "Procesando con FFmpeg..."
        return info

    return info


@celery_app.task(bind=True, name="download_video")
def download_video(
    self: Task,
    url: str,
    format_id: str,
    audio_format_id: str | None = None,
    output_format: str | None = None,
) -> dict:
    """
    Task principal de descarga. Ejecuta yt-dlp como subprocess
    y reporta progreso via state updates (polling desde API/WebSocket).
    """
    job_id = self.request.id
    job_dir = get_job_dir(job_id)

    self.update_state(
        state="DOWNLOADING",
        meta={"progress": 0, "status": JobStatus.DOWNLOADING, "message": "Iniciando descarga..."},
    )

    cmd = build_download_command(
        url=url,
        format_id=format_id,
        output_path=job_dir,
        audio_format_id=audio_format_id,
        output_format=output_format,
    )

    logger.info(f"Job {job_id}: Ejecutando {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        last_progress = 0.0
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            parsed = _parse_progress(line)

            if "progress" in parsed:
                last_progress = parsed["progress"]
                self.update_state(
                    state="DOWNLOADING",
                    meta={
                        "progress": last_progress,
                        "status": JobStatus.DOWNLOADING,
                        "speed": parsed.get("speed"),
                        "eta": parsed.get("eta"),
                        "message": f"Descargando... {last_progress:.1f}%",
                    },
                )
            elif parsed.get("status") == "processing":
                self.update_state(
                    state="PROCESSING",
                    meta={
                        "progress": last_progress,
                        "status": JobStatus.PROCESSING,
                        "message": parsed.get("message", "Procesando..."),
                    },
                )

        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"yt-dlp falló con código {process.returncode}")

        output_file = find_output_file(job_id)
        if not output_file:
            raise RuntimeError("Descarga completada pero no se encontró el archivo de salida")

        filename = os.path.basename(output_file)
        filesize = os.path.getsize(output_file)

        logger.info(f"Job {job_id}: Completado - {filename} ({filesize} bytes)")

        return {
            "status": JobStatus.COMPLETED,
            "progress": 100.0,
            "filename": filename,
            "filesize": filesize,
            "message": "Descarga completada",
        }

    except subprocess.TimeoutExpired:
        process.kill()
        raise RuntimeError("Timeout: la descarga tardó demasiado")
    except Exception as exc:
        logger.error(f"Job {job_id}: Error - {exc}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": JobStatus.FAILED,
                "progress": 0,
                "message": str(exc),
            },
        )
        raise
