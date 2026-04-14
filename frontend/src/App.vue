<template>
  <div class="app">
    <header>
      <h1>📥 YouTube Downloader</h1>
      <p class="subtitle">Descarga video y audio en la mejor calidad</p>
    </header>

    <main>
      <!-- Step 1: URL Input -->
      <section class="url-section">
        <div class="input-group">
          <input
            v-model="url"
            type="url"
            placeholder="https://www.youtube.com/watch?v=..."
            :disabled="loading"
            @keyup.enter="handleExtract"
          />
          <button @click="handleExtract" :disabled="loading || !url.trim()" class="btn-primary">
            {{ loading ? 'Analizando...' : 'Analizar' }}
          </button>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
      </section>

      <!-- Step 2: Video Info & Format Selection -->
      <section v-if="metadata" class="metadata-section">
        <div class="video-info">
          <img :src="metadata.thumbnail" :alt="metadata.title" class="thumbnail" />
          <div class="info">
            <h2>{{ metadata.title }}</h2>
            <p class="channel">{{ metadata.channel }}</p>
            <p class="duration">{{ formatDuration(metadata.duration) }}</p>
          </div>
        </div>

        <!-- Tab: Video / Audio -->
        <div class="tabs">
          <button
            :class="{ active: tab === 'video' }"
            @click="tab = 'video'"
          >🎬 Video</button>
          <button
            :class="{ active: tab === 'audio' }"
            @click="tab = 'audio'"
          >🎵 Audio</button>
        </div>

        <!-- Video Formats -->
        <div v-if="tab === 'video'" class="formats">
          <h3>Calidad de video</h3>
          <div class="format-list">
            <label
              v-for="f in metadata.video_formats"
              :key="f.format_id"
              class="format-option"
              :class="{ selected: selectedVideo === f.format_id }"
            >
              <input type="radio" v-model="selectedVideo" :value="f.format_id" />
              <span class="label">{{ f.label }}</span>
              <span v-if="f.filesize" class="size">{{ formatSize(f.filesize) }}</span>
            </label>
          </div>

          <h3>Pista de audio</h3>
          <div class="format-list">
            <label
              v-for="f in metadata.audio_formats"
              :key="f.format_id"
              class="format-option"
              :class="{ selected: selectedAudioForVideo === f.format_id }"
            >
              <input type="radio" v-model="selectedAudioForVideo" :value="f.format_id" />
              <span class="label">{{ f.label }}</span>
              <span v-if="f.filesize" class="size">{{ formatSize(f.filesize) }}</span>
            </label>
          </div>

          <div class="output-format">
            <label>Formato de salida:</label>
            <select v-model="videoOutputFormat">
              <option value="mp4">MP4</option>
              <option value="mkv">MKV</option>
              <option value="webm">WebM</option>
            </select>
          </div>

          <button
            @click="handleDownload('video')"
            :disabled="!selectedVideo || !selectedAudioForVideo || downloading"
            class="btn-download"
          >
            ⬇️ Descargar Video
          </button>
        </div>

        <!-- Audio Formats -->
        <div v-if="tab === 'audio'" class="formats">
          <h3>Calidad de audio</h3>
          <div class="format-list">
            <label
              v-for="f in metadata.audio_formats"
              :key="f.format_id"
              class="format-option"
              :class="{ selected: selectedAudio === f.format_id }"
            >
              <input type="radio" v-model="selectedAudio" :value="f.format_id" />
              <span class="label">{{ f.label }}</span>
              <span v-if="f.filesize" class="size">{{ formatSize(f.filesize) }}</span>
            </label>
          </div>

          <div class="output-format">
            <label>Convertir a:</label>
            <select v-model="audioOutputFormat">
              <option value="mp3">MP3</option>
              <option value="m4a">M4A</option>
              <option value="opus">Opus</option>
              <option value="flac">FLAC</option>
            </select>
          </div>

          <button
            @click="handleDownload('audio')"
            :disabled="!selectedAudio || downloading"
            class="btn-download"
          >
            ⬇️ Descargar Audio
          </button>
        </div>
      </section>

      <!-- Step 3: Download Progress -->
      <section v-if="job" class="progress-section">
        <div class="progress-card" :class="job.status">
          <div class="progress-header">
            <span class="status-badge">{{ statusLabel(job.status) }}</span>
            <span v-if="job.speed" class="speed">{{ job.speed }}</span>
            <span v-if="job.eta" class="eta">ETA: {{ job.eta }}</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar" :style="{ width: job.progress + '%' }"></div>
          </div>
          <p class="progress-text">{{ job.message || 'Procesando...' }}</p>

          <!-- Download Link -->
          <a
            v-if="job.status === 'completed'"
            :href="downloadUrl"
            class="btn-download-file"
            download
          >
            📁 Descargar archivo {{ job.filename ? `(${formatSize(job.filesize)})` : '' }}
          </a>
        </div>
      </section>
    </main>

    <footer>
      <p>Powered by yt-dlp + FFmpeg + FastAPI + Vue 3</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useApi } from './composables/useApi.js'

const { extractMetadata, startDownload, getDownloadUrl, connectWebSocket } = useApi()

const url = ref('')
const loading = ref(false)
const error = ref('')
const metadata = ref(null)
const tab = ref('video')
const downloading = ref(false)

// Video selections
const selectedVideo = ref(null)
const selectedAudioForVideo = ref(null)
const videoOutputFormat = ref('mp4')

// Audio selections
const selectedAudio = ref(null)
const audioOutputFormat = ref('mp3')

// Job tracking
const job = ref(null)
const downloadUrl = ref('')
let ws = null

async function handleExtract() {
  if (!url.value.trim()) return
  error.value = ''
  metadata.value = null
  job.value = null
  loading.value = true
  selectedVideo.value = null
  selectedAudioForVideo.value = null
  selectedAudio.value = null

  try {
    metadata.value = await extractMetadata(url.value.trim())

    // Auto-select best options
    if (metadata.value.video_formats.length) {
      selectedVideo.value = metadata.value.video_formats[0].format_id
    }
    if (metadata.value.audio_formats.length) {
      selectedAudioForVideo.value = metadata.value.audio_formats[0].format_id
      selectedAudio.value = metadata.value.audio_formats[0].format_id
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleDownload(type) {
  downloading.value = true
  error.value = ''

  const payload = {
    url: url.value.trim(),
    download_type: type,
  }

  if (type === 'video') {
    payload.format_id = selectedVideo.value
    payload.audio_format_id = selectedAudioForVideo.value
    payload.output_format = videoOutputFormat.value
  } else {
    payload.format_id = selectedAudio.value
    payload.output_format = audioOutputFormat.value
  }

  try {
    const result = await startDownload(payload)
    job.value = {
      job_id: result.job_id,
      status: 'pending',
      progress: 0,
      message: 'Job encolado...',
    }

    // Connect WebSocket for real-time progress
    if (ws) ws.close()
    ws = connectWebSocket(
      result.job_id,
      (data) => {
        job.value = data
        if (data.status === 'completed') {
          downloadUrl.value = getDownloadUrl(result.job_id)
          downloading.value = false
        }
        if (data.status === 'failed') {
          downloading.value = false
        }
      },
      () => {
        downloading.value = false
      }
    )
  } catch (e) {
    error.value = e.message
    downloading.value = false
  }
}

function formatDuration(seconds) {
  if (!seconds) return '0:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatSize(bytes) {
  if (!bytes) return ''
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

function statusLabel(status) {
  const labels = {
    pending: '⏳ En cola',
    extracting: '🔍 Extrayendo',
    downloading: '⬇️ Descargando',
    processing: '⚙️ Procesando',
    completed: '✅ Completado',
    failed: '❌ Error',
  }
  return labels[status] || status
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f0f0f;
  color: #e0e0e0;
  min-height: 100vh;
}

.app {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

header {
  text-align: center;
  margin-bottom: 2rem;
}

header h1 {
  font-size: 2rem;
  color: #ff4444;
  margin-bottom: 0.25rem;
}

.subtitle {
  color: #888;
  font-size: 0.95rem;
}

/* URL Input */
.url-section {
  margin-bottom: 1.5rem;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

.input-group input {
  flex: 1;
  padding: 0.85rem 1rem;
  border: 2px solid #333;
  border-radius: 8px;
  background: #1a1a1a;
  color: #fff;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.input-group input:focus {
  border-color: #ff4444;
}

.btn-primary {
  padding: 0.85rem 1.5rem;
  border: none;
  border-radius: 8px;
  background: #ff4444;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.btn-primary:hover:not(:disabled) {
  background: #ff6666;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  color: #ff6b6b;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

/* Video Info */
.metadata-section {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.video-info {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.thumbnail {
  width: 200px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.info h2 {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  line-height: 1.3;
}

.channel {
  color: #aaa;
  font-size: 0.9rem;
}

.duration {
  color: #888;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #333;
}

.tabs button {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: transparent;
  color: #888;
  font-size: 1rem;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tabs button.active {
  color: #ff4444;
  border-bottom-color: #ff4444;
}

.tabs button:hover {
  color: #ccc;
}

/* Formats */
.formats h3 {
  font-size: 0.95rem;
  color: #aaa;
  margin-bottom: 0.75rem;
  margin-top: 1rem;
}

.formats h3:first-child {
  margin-top: 0;
}

.format-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 200px;
  overflow-y: auto;
}

.format-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid #333;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.format-option:hover {
  border-color: #555;
  background: #222;
}

.format-option.selected {
  border-color: #ff4444;
  background: rgba(255, 68, 68, 0.1);
}

.format-option input[type="radio"] {
  accent-color: #ff4444;
}

.format-option .label {
  flex: 1;
  font-size: 0.9rem;
}

.format-option .size {
  color: #888;
  font-size: 0.8rem;
}

.output-format {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
}

.output-format label {
  color: #aaa;
  font-size: 0.9rem;
}

.output-format select {
  padding: 0.4rem 0.75rem;
  border: 1px solid #333;
  border-radius: 6px;
  background: #222;
  color: #fff;
  font-size: 0.9rem;
}

.btn-download {
  width: 100%;
  padding: 0.85rem;
  margin-top: 1.25rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #ff4444, #cc0033);
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-download:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-download:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Progress */
.progress-section {
  margin-bottom: 1.5rem;
}

.progress-card {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #333;
}

.progress-card.completed {
  border-color: #4caf50;
}

.progress-card.failed {
  border-color: #ff4444;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.status-badge {
  font-weight: 600;
  font-size: 0.95rem;
}

.speed, .eta {
  color: #888;
  font-size: 0.85rem;
  margin-left: auto;
}

.eta {
  margin-left: 0;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #ff4444, #ff8800);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  color: #888;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.btn-download-file {
  display: block;
  text-align: center;
  margin-top: 1rem;
  padding: 0.85rem;
  background: #4caf50;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  transition: background 0.2s;
}

.btn-download-file:hover {
  background: #66bb6a;
}

/* Footer */
footer {
  text-align: center;
  color: #555;
  font-size: 0.8rem;
  margin-top: 3rem;
  padding-top: 1rem;
  border-top: 1px solid #222;
}

/* Responsive */
@media (max-width: 600px) {
  .video-info {
    flex-direction: column;
  }

  .thumbnail {
    width: 100%;
    max-height: 200px;
  }

  .input-group {
    flex-direction: column;
  }

  .progress-header {
    flex-wrap: wrap;
  }
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: #1a1a1a;
}

::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 3px;
}
</style>
