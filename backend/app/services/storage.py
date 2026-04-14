import os
import time
import glob
from app.config import settings


def get_job_dir(job_id: str) -> str:
    """Directorio aislado por job para evitar colisiones."""
    path = os.path.join(settings.download_dir, job_id)
    os.makedirs(path, exist_ok=True)
    return path


def find_output_file(job_id: str) -> str | None:
    """Busca el archivo resultante dentro del directorio del job."""
    job_dir = get_job_dir(job_id)
    files = [
        f
        for f in glob.glob(os.path.join(job_dir, "*"))
        if not f.endswith((".part", ".ytdl", ".temp"))
    ]
    if files:
        return max(files, key=os.path.getmtime)
    return None


def cleanup_expired_files() -> int:
    """Purga archivos más viejos que MAX_FILE_AGE_MINUTES. Retorna cantidad eliminados."""
    cutoff = time.time() - (settings.max_file_age_minutes * 60)
    removed = 0
    for entry in os.scandir(settings.download_dir):
        if entry.is_dir():
            try:
                mtime = max(
                    (os.path.getmtime(os.path.join(entry.path, f)) for f in os.listdir(entry.path)),
                    default=entry.stat().st_mtime,
                )
                if mtime < cutoff:
                    import shutil
                    shutil.rmtree(entry.path)
                    removed += 1
            except OSError:
                continue
    return removed
