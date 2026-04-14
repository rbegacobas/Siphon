const API_BASE = '/api'

export function useApi() {
  async function extractMetadata(url) {
    const res = await fetch(`${API_BASE}/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Error extrayendo metadata')
    }
    return res.json()
  }

  async function startDownload(payload) {
    const res = await fetch(`${API_BASE}/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Error iniciando descarga')
    }
    return res.json()
  }

  async function getJobStatus(jobId) {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`)
    if (!res.ok) throw new Error('Error consultando estado')
    return res.json()
  }

  function getDownloadUrl(jobId) {
    return `${API_BASE}/download/${jobId}`
  }

  function connectWebSocket(jobId, onMessage, onClose) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${location.host}/ws/jobs/${jobId}`)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onMessage(data)
    }

    ws.onclose = () => {
      if (onClose) onClose()
    }

    ws.onerror = () => {
      ws.close()
    }

    return ws
  }

  return { extractMetadata, startDownload, getJobStatus, getDownloadUrl, connectWebSocket }
}
