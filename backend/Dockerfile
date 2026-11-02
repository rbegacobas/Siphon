FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# ponytail: remote ADD busts the layer cache whenever PyPI publishes a new yt-dlp
ADD https://pypi.org/pypi/yt-dlp/json /tmp/ytdlp-version.json
RUN pip install --no-cache-dir --upgrade "yt-dlp[default]"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
