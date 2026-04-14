import json
import os
import shutil
import subprocess
import re
from typing import Any

from app.config import settings
from app.models import FormatInfo, VideoMetadata

# Docker Secrets mounts files as read-only in /run/secrets/.
# yt-dlp needs write access to update session tokens, so we
# copy the secret to a writable temp location on first use.
_WRITABLE_COOKIES = "/tmp/.yt_cookies_live.txt"


def _ensure_writable_cookies() -> str | None:
    """Returns path to a writable copy of the cookies file, or None."""
    src = settings.ytdlp_cookies_file
    if not src or not os.path.isfile(src):
        return None
    # Always copy if dest doesn't exist OR source differs (size or mtime)
    needs_copy = not os.path.isfile(_WRITABLE_COOKIES)
    if not needs_copy:
        src_stat = os.stat(src)
        dst_stat = os.stat(_WRITABLE_COOKIES)
        needs_copy = (src_stat.st_size != dst_stat.st_size
                      or src_stat.st_mtime != dst_stat.st_mtime)
    if needs_copy:
        shutil.copy2(src, _WRITABLE_COOKIES)
        os.chmod(_WRITABLE_COOKIES, 0o600)
    return _WRITABLE_COOKIES


def _base_opts() -> list[str]:
    """Opciones base para yt-dlp."""
    opts = ["yt-dlp", "--no-warnings", "--no-check-certificates", "--js-runtimes", "node"]
    cookies_path = _ensure_writable_cookies()
    if cookies_path:
        opts.extend(["--cookies", cookies_path])
    if settings.ytdlp_proxy:
        opts.extend(["--proxy", settings.ytdlp_proxy])
    return opts


def extract_metadata(url: str) -> VideoMetadata:
    """Extrae metadata sin descargar usando --dump-json."""
    cmd = _base_opts() + ["--dump-json", "--no-playlist", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        raise RuntimeError(f"Error extrayendo metadata: {result.stderr.strip()}")

    data: dict[str, Any] = json.loads(result.stdout)

    video_formats: list[FormatInfo] = []
    audio_formats: list[FormatInfo] = []

    for fmt in data.get("formats", []):
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")
        is_video = vcodec not in ("none", None)
        is_audio = acodec not in ("none", None)

        if is_video and not is_audio:
            # Stream de video puro (DASH)
            height = fmt.get("height", 0)
            fps = fmt.get("fps", 0)
            label = f"{height}p{int(fps) if fps and fps > 30 else ''} ({fmt.get('ext', '?')})"
            video_formats.append(
                FormatInfo(
                    format_id=fmt["format_id"],
                    ext=fmt.get("ext", "mp4"),
                    resolution=f"{fmt.get('width', '?')}x{height}",
                    filesize=fmt.get("filesize") or fmt.get("filesize_approx"),
                    fps=fps,
                    vcodec=vcodec,
                    acodec=None,
                    label=label,
                )
            )
        elif is_audio and not is_video:
            # Stream solo audio (DASH)
            abr = fmt.get("abr", 0)
            label = f"{fmt.get('ext', '?').upper()} {int(abr)}kbps" if abr else fmt.get("ext", "?")
            audio_formats.append(
                FormatInfo(
                    format_id=fmt["format_id"],
                    ext=fmt.get("ext", "m4a"),
                    filesize=fmt.get("filesize") or fmt.get("filesize_approx"),
                    acodec=acodec,
                    abr=abr,
                    label=label,
                )
            )

    # Ordenar: video por resolución desc, audio por bitrate desc
    video_formats.sort(key=lambda f: int(re.search(r"(\d+)p", f.label).group(1)) if re.search(r"(\d+)p", f.label) else 0, reverse=True)
    audio_formats.sort(key=lambda f: f.abr or 0, reverse=True)

    # Deduplicar por resolución/ext para video, por abr/ext para audio
    seen_video: set[str] = set()
    deduped_video: list[FormatInfo] = []
    for vf in video_formats:
        key = f"{vf.resolution}-{vf.ext}"
        if key not in seen_video:
            seen_video.add(key)
            deduped_video.append(vf)

    seen_audio: set[str] = set()
    deduped_audio: list[FormatInfo] = []
    for af in audio_formats:
        key = f"{int(af.abr or 0)}-{af.ext}"
        if key not in seen_audio:
            seen_audio.add(key)
            deduped_audio.append(af)

    return VideoMetadata(
        id=data["id"],
        title=data.get("title", "Sin título"),
        duration=data.get("duration", 0),
        thumbnail=data.get("thumbnail", ""),
        channel=data.get("channel", data.get("uploader", "Desconocido")),
        upload_date=data.get("upload_date"),
        view_count=data.get("view_count"),
        video_formats=deduped_video[:10],  # Top 10
        audio_formats=deduped_audio[:6],
    )


def build_download_command(
    url: str,
    format_id: str,
    output_path: str,
    audio_format_id: str | None = None,
    output_format: str | None = None,
) -> list[str]:
    """Construye el comando yt-dlp para descarga."""
    cmd = _base_opts() + [
        "--no-playlist",
        "--newline",  # Progreso línea por línea (parseable)
    ]

    if audio_format_id:
        # Muxear video + audio
        cmd.extend(["-f", f"{format_id}+{audio_format_id}"])
        cmd.extend(["--merge-output-format", output_format or "mp4"])
    elif output_format in ("mp3",):
        # Extracción de audio con conversión
        cmd.extend(["-f", format_id])
        cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
    elif output_format in ("m4a", "opus", "flac"):
        cmd.extend(["-f", format_id])
        cmd.extend(["-x", "--audio-format", output_format])
    else:
        cmd.extend(["-f", format_id])

    cmd.extend(["-o", os.path.join(output_path, "%(title)s.%(ext)s")])
    cmd.append(url)

    return cmd
