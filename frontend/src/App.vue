<template>
  <div class="app">
    <!-- Navigation -->
    <nav class="nav">
      <a href="#" class="logo" @click.prevent="scrollTop">Siphon</a>
      <div class="nav-links" :class="{ open: menuOpen }">
        <a href="#how" class="nav-link" @click.prevent="scrollTo('how')">How it Works</a>
        <a href="#faq" class="nav-link" @click.prevent="scrollTo('faq')">FAQ</a>
        <a href="#about" class="nav-link" @click.prevent="scrollTo('about')">About</a>
        <a href="https://ko-fi.com/rbegacobas" target="_blank" rel="noopener" class="nav-donate">
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" x2="6" y1="1" y2="4"/><line x1="10" x2="10" y1="1" y2="4"/><line x1="14" x2="14" y1="1" y2="4"/></svg>
          Donate
        </a>
      </div>
      <button class="menu-toggle" @click="menuOpen = !menuOpen" aria-label="Menu">
        <svg v-if="!menuOpen" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="6" y1="6" y2="18"/><line x1="6" x2="18" y1="6" y2="18"/></svg>
      </button>
    </nav>

    <!-- Hero / Home View (no metadata yet) -->
    <main v-if="!metadata" class="hero">
      <h1 class="heading">Download YouTube Videos</h1>
      <p class="subheading">Paste a YouTube URL to get started. Fast, free, and no ads.</p>

      <div class="input-bar">
        <svg class="play-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FF0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>
        <input
          v-model="url"
          type="url"
          placeholder="Paste YouTube URL here..."
          :disabled="loading"
          @keyup.enter="handleExtract"
        />
        <button @click="handleExtract" :disabled="loading || !url.trim()" class="btn-process">
          {{ loading ? 'Processing...' : 'Process Video' }}
        </button>
      </div>

      <p class="helper-text">Supports youtube.com and youtu.be links</p>
      <p v-if="error" class="error-text">{{ error }}</p>
    </main>

    <!-- Discovery / Download View -->
    <main v-if="metadata" class="content">
      <!-- URL Input Bar (compact) -->
      <div class="input-bar compact">
        <svg class="play-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FF0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>
        <input
          v-model="url"
          type="url"
          :disabled="loading"
          @keyup.enter="handleExtract"
        />
        <button @click="handleExtract" :disabled="loading || !url.trim()" class="btn-process">
          {{ loading ? 'Processing...' : 'Process Video' }}
        </button>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>

      <!-- Media Preview Card -->
      <div class="media-card">
        <div class="thumb-wrapper">
          <img :src="metadata.thumbnail" :alt="metadata.title" class="thumb" />
          <span class="duration-badge">{{ formatDuration(metadata.duration) }}</span>
        </div>
        <div class="video-info">
          <h2 class="video-title">{{ metadata.title }}</h2>
          <p class="channel-name">{{ metadata.channel }}</p>
          <div class="meta-row">
            <span v-if="metadata.view_count">{{ formatViews(metadata.view_count) }} views</span>
            <span v-if="metadata.view_count && metadata.upload_date" class="dot">·</span>
            <span v-if="metadata.upload_date">{{ formatDate(metadata.upload_date) }}</span>
          </div>
        </div>
      </div>

      <!-- Format Section -->
      <div class="format-section">
        <!-- Tabs -->
        <div class="tabs">
          <button :class="['tab', { active: tab === 'video' }]" @click="tab = 'video'">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect width="15" height="14" x="1" y="5" rx="2" ry="2"/></svg>
            Video
          </button>
          <button :class="['tab', { active: tab === 'audio' }]" @click="tab = 'audio'">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
            Audio Only
          </button>
        </div>

        <!-- Video Formats Table -->
        <div v-if="tab === 'video'">
          <div class="list-header">
            <span class="col-quality">Quality</span>
            <span class="col-format">Format</span>
            <span class="col-size">File Size</span>
            <span class="col-action"></span>
          </div>
          <div
            v-for="(f, idx) in metadata.video_formats"
            :key="f.format_id"
            :class="['format-row', { 'row-active': activeFormatId === f.format_id }]"
            :ref="el => { if (activeFormatId === f.format_id) activeRowEl = el }"
          >
            <div class="row-main">
              <div class="col-quality" :data-meta="(f.ext || 'mp4').toUpperCase() + (f.filesize ? ' · ~' + formatSize(f.filesize) : '')">
                <span :class="['quality-badge', { 'badge-accent': idx === 0 }]">
                  {{ extractRes(f.label) }}
                </span>
                <span v-if="idx === 0" class="best-badge">BEST</span>
              </div>
              <span class="col-format">{{ (f.ext || 'mp4').toUpperCase() }}</span>
              <span class="col-size">{{ f.filesize ? '~' + formatSize(f.filesize) : '—' }}</span>
              <div class="col-action">
                <button
                  v-if="activeFormatId !== f.format_id"
                  :class="['btn-dl', { primary: idx === 0 }]"
                  :disabled="downloading"
                  @click="handleVideoDownload(f)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                  Download
                </button>
                <span v-else-if="job && job.status !== 'completed' && job.status !== 'failed'" class="inline-status">
                  <span class="spinner"></span>
                  <span class="inline-pct">{{ Math.round(job.progress) }}%</span>
                </span>
              </div>
            </div>
            <!-- Inline progress for active row -->
            <div v-if="activeFormatId === f.format_id && job" class="inline-progress">
              <div class="progress-label">
                <span class="prog-text">{{ job.message || 'Processing...' }}</span>
                <span class="prog-pct">{{ Math.round(job.progress) }}%</span>
              </div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" :style="{ width: job.progress + '%' }"></div>
              </div>
              <div v-if="job.speed || job.eta" class="progress-meta">
                <span v-if="job.speed">{{ job.speed }}</span>
                <span v-if="job.eta">ETA: {{ job.eta }}</span>
              </div>
              <a
                v-if="job.status === 'completed'"
                :href="downloadUrl"
                class="btn-download-ready"
                download
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                Save File {{ job.filesize ? `(${formatSize(job.filesize)})` : '' }}
              </a>
              <p v-if="job.status === 'failed'" class="error-text" style="margin-top: 8px;">
                {{ job.message }}
              </p>
            </div>
          </div>
        </div>

        <!-- Audio Formats Table -->
        <div v-if="tab === 'audio'">
          <div class="list-header">
            <span class="col-quality">Quality</span>
            <span class="col-format">Format</span>
            <span class="col-size">File Size</span>
            <span class="col-action"></span>
          </div>
          <div
            v-for="(f, idx) in metadata.audio_formats"
            :key="f.format_id"
            :class="['format-row', { 'row-active': activeFormatId === f.format_id }]"
            :ref="el => { if (activeFormatId === f.format_id) activeRowEl = el }"
          >
            <div class="row-main">
              <div class="col-quality" :data-meta="(f.ext || 'm4a').toUpperCase() + (f.filesize ? ' · ~' + formatSize(f.filesize) : '')">
                <span :class="['quality-badge', { 'badge-accent': idx === 0 }]">
                  {{ f.abr ? Math.round(f.abr) + 'kbps' : f.ext?.toUpperCase() }}
                </span>
                <span v-if="idx === 0" class="best-badge">BEST</span>
              </div>
              <span class="col-format">{{ (f.ext || 'm4a').toUpperCase() }}</span>
              <span class="col-size">{{ f.filesize ? '~' + formatSize(f.filesize) : '—' }}</span>
              <div class="col-action">
                <button
                  v-if="activeFormatId !== f.format_id"
                  :class="['btn-dl', { primary: idx === 0 }]"
                  :disabled="downloading"
                  @click="handleAudioDownload(f)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                  Download
                </button>
                <span v-else-if="job && job.status !== 'completed' && job.status !== 'failed'" class="inline-status">
                  <span class="spinner"></span>
                  <span class="inline-pct">{{ Math.round(job.progress) }}%</span>
                </span>
              </div>
            </div>
            <!-- Inline progress for active row -->
            <div v-if="activeFormatId === f.format_id && job" class="inline-progress">
              <div class="progress-label">
                <span class="prog-text">{{ job.message || 'Processing...' }}</span>
                <span class="prog-pct">{{ Math.round(job.progress) }}%</span>
              </div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" :style="{ width: job.progress + '%' }"></div>
              </div>
              <div v-if="job.speed || job.eta" class="progress-meta">
                <span v-if="job.speed">{{ job.speed }}</span>
                <span v-if="job.eta">ETA: {{ job.eta }}</span>
              </div>
              <a
                v-if="job.status === 'completed'"
                :href="downloadUrl"
                class="btn-download-ready"
                download
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
                Save File {{ job.filesize ? `(${formatSize(job.filesize)})` : '' }}
              </a>
              <p v-if="job.status === 'failed'" class="error-text" style="margin-top: 8px;">
                {{ job.message }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Sections (visible when no metadata / scrolled down) -->
    <section id="how" class="section">
      <div class="section-inner">
        <h2 class="section-title">How it Works</h2>
        <div class="steps">
          <div class="step">
            <div class="step-num">1</div>
            <h3>Paste a URL</h3>
            <p>Copy any YouTube video link and paste it into the input field above.</p>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <h3>Choose a Format</h3>
            <p>We extract all available qualities. Pick video (up to 4K) or audio only (MP3).</p>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <h3>Download</h3>
            <p>Click download, wait for processing, and save the file directly to your device.</p>
          </div>
        </div>
      </div>
    </section>

    <section id="faq" class="section section-alt">
      <div class="section-inner">
        <h2 class="section-title">Frequently Asked Questions</h2>
        <div class="faq-list">
          <details class="faq-item">
            <summary>Is Siphon free to use?</summary>
            <p>Yes. Siphon is completely free with no ads, no tracking, and no account required.</p>
          </details>
          <details class="faq-item">
            <summary>What formats and qualities are supported?</summary>
            <p>Video downloads are available from 360p up to 4K (when available) in MP4 format. Audio downloads are available in MP3 at the highest bitrate the source provides.</p>
          </details>
          <details class="faq-item">
            <summary>Why does the download take a moment?</summary>
            <p>High-quality videos require merging separate video and audio streams on the server. This takes a few seconds depending on the file size.</p>
          </details>
          <details class="faq-item">
            <summary>Is there a download limit?</summary>
            <p>To keep the service available for everyone, there is a fair-use limit per IP address. Normal usage is never affected.</p>
          </details>
          <details class="faq-item">
            <summary>Do you store my downloads?</summary>
            <p>No. Files are temporarily stored on the server for a short period to allow you to save them, then automatically deleted. We do not log URLs or keep any user data.</p>
          </details>
        </div>
      </div>
    </section>

    <section id="about" class="section">
      <div class="section-inner">
        <h2 class="section-title">About &amp; Legal</h2>
        <div class="about-content">
          <p>Siphon is an independent tool built by an indie developer. It is <strong>not</strong> affiliated with, authorized, maintained, sponsored, or endorsed by YouTube, Google Inc., or any of its affiliates.</p>
          <div class="disclaimer-box">
            <h4>Terms of Use</h4>
            <ul>
              <li><strong>Personal use only.</strong> This tool is intended for personal, non-commercial, and educational purposes.</li>
              <li><strong>Copyright compliance.</strong> You are solely responsible for ensuring you have the right or permission to download any media.</li>
              <li><strong>Limitation of liability.</strong> The developer is not responsible for any misuse of the application or intellectual property infringement by the user.</li>
            </ul>
            <p class="disclaimer-accept">By pasting a URL and clicking "Process", you confirm that you accept these terms.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <p>Built with care. No tracking. No ads.</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useApi } from './composables/useApi.js'

const { extractMetadata, startDownload, getDownloadUrl, connectWebSocket } = useApi()

const url = ref('')
const loading = ref(false)
const error = ref('')
const metadata = ref(null)
const tab = ref('video')
const downloading = ref(false)
const menuOpen = ref(false)
const activeFormatId = ref(null)
const activeRowEl = ref(null)

const job = ref(null)
const downloadUrl = ref('')
let ws = null

async function handleExtract() {
  if (!url.value.trim()) return
  error.value = ''
  metadata.value = null
  job.value = null
  activeFormatId.value = null
  loading.value = true

  try {
    metadata.value = await extractMetadata(url.value.trim())
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function handleVideoDownload(format) {
  activeFormatId.value = format.format_id
  const bestAudio = metadata.value.audio_formats[0]
  doDownload({
    url: url.value.trim(),
    download_type: 'video',
    format_id: format.format_id,
    audio_format_id: bestAudio?.format_id,
    output_format: 'mp4',
  })
}

function handleAudioDownload(format) {
  activeFormatId.value = format.format_id
  doDownload({
    url: url.value.trim(),
    download_type: 'audio',
    format_id: format.format_id,
    output_format: 'mp3',
  })
}

async function doDownload(payload) {
  downloading.value = true
  error.value = ''
  job.value = { status: 'pending', progress: 0, message: 'Queued...' }

  nextTick(() => {
    if (activeRowEl.value) {
      activeRowEl.value.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })

  try {
    const result = await startDownload(payload)
    job.value.job_id = result.job_id

    if (ws) ws.close()
    ws = connectWebSocket(
      result.job_id,
      (data) => {
        job.value = data
        if (data.status === 'completed') {
          downloadUrl.value = getDownloadUrl(result.job_id)
          downloading.value = false
        }
        if (data.status === 'failed') downloading.value = false
      },
      () => { downloading.value = false }
    )
  } catch (e) {
    error.value = e.message
    downloading.value = false
    job.value = null
  }
}

function formatDuration(s) {
  if (!s) return '0:00'
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  return `${m}:${String(sec).padStart(2, '0')}`
}

function formatSize(bytes) {
  if (!bytes) return ''
  const u = ['B', 'KB', 'MB', 'GB']
  let i = 0, sz = bytes
  while (sz >= 1024 && i < u.length - 1) { sz /= 1024; i++ }
  return `${sz.toFixed(1)} ${u[i]}`
}

function formatViews(n) {
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B'
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K'
  return n.toString()
}

function formatDate(d) {
  if (!d || d.length !== 8) return d
  const y = d.slice(0, 4), m = d.slice(4, 6), day = d.slice(6, 8)
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return `${months[parseInt(m) - 1]} ${parseInt(day)}, ${y}`
}

function extractRes(label) {
  const m = label.match(/(\d+p\d*)/)
  return m ? m[1] : label
}

function scrollTo(id) {
  menuOpen.value = false
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

function scrollTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style>
/* ============================
   Design Tokens from diseno.pen
   ============================ */
:root {
  --accent: #4F46E5;
  --accent-hover: #4338CA;
  --accent-light: #EEF2FF;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F3F4F6;
  --bg-tertiary: #E5E7EB;
  --border: #E5E7EB;
  --success: #059669;
  --success-light: #ECFDF5;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --text-tertiary: #9CA3AF;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Nav */
.nav {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  padding: 0 48px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  text-decoration: none;
  cursor: pointer;
}

.nav-links {
  display: flex;
  gap: 32px;
  align-items: center;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.15s;
}

.nav-link:hover {
  color: var(--text-primary);
}

.nav-donate {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.15s;
}

.nav-donate:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* Hero */
.hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 24px;
  padding: 0 48px;
}

.heading {
  font-size: 40px;
  font-weight: 700;
  color: var(--text-primary);
}

.subheading {
  font-size: 18px;
  color: var(--text-secondary);
}

.helper-text {
  font-size: 13px;
  color: var(--text-tertiary);
}

.error-text {
  font-size: 13px;
  color: #DC2626;
}

/* Input Bar */
.input-bar {
  display: flex;
  align-items: center;
  width: 720px;
  max-width: 100%;
  height: 56px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0 4px 0 16px;
  gap: 12px;
}

.input-bar.compact {
  width: 720px;
  height: 52px;
}

.play-icon {
  flex-shrink: 0;
}

.input-bar input {
  flex: 1;
  border: none;
  outline: none;
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  color: var(--text-primary);
  background: transparent;
}

.input-bar input::placeholder {
  color: var(--text-tertiary);
}

.btn-process {
  height: 44px;
  padding: 0 24px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.btn-process:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-process:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Content */
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 28px;
  padding: 32px 48px;
}

/* Media Preview Card */
.media-card {
  display: flex;
  gap: 20px;
  width: 720px;
  max-width: 100%;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.thumb-wrapper {
  position: relative;
  flex-shrink: 0;
  width: 240px;
  height: 135px;
  border-radius: 4px;
  overflow: hidden;
}

.thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.duration-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(17, 24, 39, 0.9);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
}

.video-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
  min-width: 0;
}

.video-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text-primary);
}

.channel-name {
  font-size: 13px;
  color: var(--text-secondary);
}

.meta-row {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
  color: var(--text-tertiary);
}

.dot { margin: 0 4px; }

/* Format Section */
.format-section {
  width: 720px;
  max-width: 100%;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}

/* Tabs */
.tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  background: none;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: var(--text-tertiary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.15s;
}

.tab.active {
  color: var(--accent);
  font-weight: 600;
  border-bottom-color: var(--accent);
}

.tab:hover:not(.active) {
  color: var(--text-secondary);
}

/* List Header */
.list-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-secondary);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Format Rows */
.format-row {
  display: flex;
  flex-direction: column;
  padding: 0;
  border-bottom: 1px solid var(--border);
}

.format-row:last-child {
  border-bottom: none;
}

.format-row .row-main {
  display: flex;
  align-items: center;
  padding: 14px 16px;
}

.format-row.row-active {
  background: var(--accent-light);
  border-radius: 6px;
}

/* Inline status (spinner + %) shown in the action column */
.inline-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--bg-tertiary);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.inline-pct {
  font-variant-numeric: tabular-nums;
}

/* Inline progress panel under active row */
.inline-progress {
  padding: 10px 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.col-quality {
  width: 140px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.col-format {
  width: 100px;
  font-size: 13px;
  color: var(--text-primary);
}

.col-size {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
}

.col-action {
  width: 120px;
  display: flex;
  justify-content: flex-end;
}

.quality-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.quality-badge.badge-accent {
  background: var(--accent-light);
  color: var(--accent);
  font-weight: 700;
}

.best-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  background: var(--success-light);
  color: var(--success);
}

/* Download Buttons */
.btn-dl {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  background: var(--bg-primary);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.btn-dl:hover:not(:disabled) {
  border-color: var(--text-tertiary);
  color: var(--text-primary);
}

.btn-dl.primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  font-weight: 600;
}

.btn-dl.primary:hover:not(:disabled) {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}

.btn-dl:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Progress */
.progress-section {
  width: 720px;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prog-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.prog-pct {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
}

.progress-bar-bg {
  width: 100%;
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.btn-download-ready {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
  padding: 12px 24px;
  background: var(--success);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-download-ready:hover {
  background: #047857;
}

/* Sections */
.section {
  padding: 80px 48px;
}

.section-alt {
  background: var(--bg-secondary);
}

.section-inner {
  max-width: 720px;
  margin: 0 auto;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 40px;
  text-align: center;
}

/* Steps */
.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
}

.step {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.step-num {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent-light);
  color: var(--accent);
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.step p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* FAQ */
.faq-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.faq-item {
  border-bottom: 1px solid var(--border);
  padding: 0;
}

.faq-item:first-child {
  border-top: 1px solid var(--border);
}

.faq-item summary {
  padding: 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  cursor: pointer;
  list-style: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.faq-item summary::-webkit-details-marker { display: none; }

.faq-item summary::after {
  content: '+';
  font-size: 18px;
  font-weight: 400;
  color: var(--text-tertiary);
  transition: transform 0.2s;
}

.faq-item[open] summary::after {
  content: '\2212';
}

.faq-item p {
  padding: 0 0 16px 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
}

/* About */
.about-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.disclaimer-box {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 24px;
}

.disclaimer-box h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.disclaimer-box ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.disclaimer-box li {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  padding-left: 16px;
  position: relative;
}

.disclaimer-box li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 4px;
  height: 4px;
  background: var(--text-tertiary);
  border-radius: 50%;
}

.disclaimer-accept {
  font-size: 12px;
  font-style: italic;
  color: var(--text-tertiary);
}

/* Footer */
.footer {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 48px;
  font-size: 12px;
  color: var(--text-tertiary);
  border-top: 1px solid var(--border);
}

/* Menu toggle (hidden on desktop) */
.menu-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-primary);
  padding: 4px;
}

/* Responsive — Mobile (from diseno.pen) */
@media (max-width: 640px) {
  /* Nav: hamburger menu */
  .nav {
    padding: 0 16px;
    height: 56px;
  }

  .menu-toggle { display: block; }

  .nav-links {
    display: none;
    position: absolute;
    top: 56px;
    left: 0;
    right: 0;
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border);
    flex-direction: column;
    padding: 12px 16px;
    gap: 0;
    z-index: 100;
  }

  .nav-links.open { display: flex; }

  .nav-link {
    display: block;
    padding: 12px 0;
    font-size: 15px;
    border-bottom: 1px solid var(--border);
  }

  .nav-donate {
    margin-top: 8px;
    justify-content: center;
  }

  /* Hero */
  .hero {
    padding: 0 16px;
    gap: 12px;
  }

  .heading {
    font-size: 28px;
    text-align: center;
    line-height: 1.2;
  }

  .subheading {
    font-size: 16px;
    text-align: center;
    line-height: 1.5;
  }

  .helper-text { font-size: 12px; }

  /* Input: stacked vertically */
  .input-bar {
    width: 100%;
    flex-direction: column;
    height: auto;
    padding: 0;
    border: none;
    gap: 12px;
    background: transparent;
  }

  .input-bar.compact {
    width: 100%;
    height: auto;
  }

  .input-bar .play-icon { display: none; }

  .input-bar input {
    width: 100%;
    height: 48px;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0 14px;
    font-size: 14px;
    background: var(--bg-primary);
  }

  .btn-process {
    width: 100%;
    height: 48px;
    font-size: 15px;
    border-radius: 6px;
  }

  /* Content */
  .content {
    padding: 20px 16px;
    gap: 20px;
  }

  /* Media card: stacked */
  .media-card {
    flex-direction: column;
    width: 100%;
    gap: 12px;
    padding: 12px;
  }

  .thumb-wrapper {
    width: 100%;
    height: 190px;
  }

  .video-title { font-size: 15px; }
  .channel-name { font-size: 12px; }
  .meta-row { font-size: 11px; }

  /* Format section: mobile rows */
  .format-section {
    width: 100%;
  }

  .tabs {
    display: flex;
  }

  .tab {
    flex: 1;
    justify-content: center;
    padding: 10px 20px;
    font-size: 13px;
    gap: 6px;
  }

  /* Hide table header on mobile */
  .list-header { display: none; }

  /* Format rows: horizontal badge+meta on left, button on right */
  .format-row {
    padding: 0;
  }

  .format-row .row-main {
    padding: 12px;
    justify-content: space-between;
    align-items: center;
  }

  .col-quality {
    width: auto;
    flex-shrink: 0;
  }

  .col-format, .col-size { display: none; }

  /* Show combined meta on mobile via pseudo or inline */
  .format-row .row-main .col-quality::after {
    content: attr(data-meta);
    font-size: 12px;
    font-weight: 400;
    color: var(--text-secondary);
    margin-left: 8px;
  }

  .col-action {
    width: auto;
  }

  .btn-dl {
    padding: 8px 16px;
    font-size: 12px;
    gap: 6px;
  }

  /* Progress */
  .progress-section {
    width: 100%;
  }

  .prog-text, .prog-pct { font-size: 12px; }

  /* Sections */
  .section { padding: 48px 16px; }
  .section-title { font-size: 20px; margin-bottom: 28px; }
  .steps { grid-template-columns: 1fr; gap: 24px; }
  .disclaimer-box { padding: 16px; }

  /* Footer */
  .footer {
    padding: 16px;
    font-size: 11px;
  }
}
</style>
