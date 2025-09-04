// src/utils/api.ts
// In prod (Next build), this is empty => same-origin.
// In dev, set NEXT_PUBLIC_API_BASE=http://localhost:8000 in .env.local.
export const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

// Build an absolute URL for our API.
export function apiUrl(path: string) {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${BASE}${p}`;
}

// Fetch wrapper used everywhere.
export function apiFetch(path: string, init?: RequestInit) {
  return fetch(apiUrl(path), init);
}

// WebSocket base that mirrors BASE or falls back to window.location.
export function wsUrl(path: string) {
  const isHttps = typeof window !== "undefined" && window.location.protocol === "https:";
  const wsBase =
    BASE
      ? BASE.replace(/^http:/, "ws:").replace(/^https:/, "wss:")
      : (isHttps ? "wss://" : "ws://") + (typeof window !== "undefined" ? window.location.host : "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${wsBase}${p}`;
}

// --- PROD GUARD: explode loudly if localhost leaks into prod ---
if (typeof window !== "undefined" && process.env.NODE_ENV === "production") {
  if (BASE.includes("localhost")) {
    // eslint-disable-next-line no-console
    console.error("❌ NEXT_PUBLIC_API_BASE contains localhost in production:", BASE);
    throw new Error("Invalid API base in production");
  }
}

export interface UploadChunkResponse {
  session_id: string
  chunk_index: number
  received_chunks: number
  total_chunks: number
  progress: number
  complete: boolean
}

interface ProcessingUpdate {
  type: string
  pct: number
  msg: string
  status?: string
}

export async function uploadFileInChunks(
  file: File, 
  onProgress: (progress: number, message: string) => void
): Promise<string> {
  const CHUNK_SIZE = 5 * 1024 * 1024 // 5MB chunks
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE)
  let sessionId: string | undefined

  try {
    onProgress(0, 'Preparing upload...')
    
    // Upload chunks
    for (let i = 0; i < totalChunks; i++) {
      const start = i * CHUNK_SIZE
      const end = Math.min(start + CHUNK_SIZE, file.size)
      const chunk = file.slice(start, end)
      
      const formData = new FormData()
      
      formData.append('chunk', chunk)
      formData.append('chunk_index', i.toString())
      formData.append('total_chunks', totalChunks.toString())
      formData.append('filename', file.name)
      
      if (sessionId) {
        formData.append('session_id', sessionId)
      }
      
      const response = await apiFetch("/api/upload/chunk", {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        throw new Error(`Chunk upload failed: ${response.statusText}`)
      }
      
      const result: UploadChunkResponse = await response.json()
      sessionId = result.session_id
      
      const progress = Math.round((result.received_chunks / result.total_chunks) * 50) // 50% for upload
      onProgress(progress, `Uploading... (${result.received_chunks}/${result.total_chunks} chunks)`)
    }
    
    // Complete upload and start processing
    const completeResponse = await apiFetch(`/api/upload/complete/${sessionId}`, {
      method: 'POST'
    })
    
    if (!completeResponse.ok) {
      throw new Error(`Upload completion failed: ${completeResponse.statusText}`)
    }
    
    const completeResult = await completeResponse.json()
    onProgress(50, 'Upload complete, starting processing...')
    
    return sessionId!
  } catch (error) {
    throw new Error(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

export class ProcessingStatusManager {
  private ws: WebSocket | null = null
  
  connectWebSocket(
    sessionId: string, 
    onUpdate: (update: ProcessingUpdate) => void,
    onComplete: (result: any) => void,
    onError: (error: string) => void
  ): WebSocket {
    const ws = new WebSocket(wsUrl(`/ws/${sessionId}`))
    
    ws.onopen = () => {
      console.log('WebSocket connected for session:', sessionId)
    }
    
    ws.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data)
        console.log('WebSocket message:', update)
        
        if (update.type === 'progress') {
          onUpdate(update)
          
          // Check if completed and fetch final result
          if (update.pct >= 100 && update.status === 'completed') {
            console.log('Job completed, fetching final result for session:', sessionId)
            // Fetch final result from Redis
            apiFetch(`/api/jobs/${sessionId}`)
              .then(res => res.json())
              .then(data => {
                console.log('Final result data:', data)
                if (data.result) {
                  try {
                    const result = typeof data.result === 'string' ? JSON.parse(data.result) : data.result
                    console.log('Parsed result:', result)
                    onComplete(result)
                  } catch (e) {
                    console.error('Error parsing result:', e)
                    onError('Failed to parse processing result')
                  }
                } else {
                  onError('No result data available')
                }
              })
              .catch(err => {
                console.error('Error fetching final result:', err)
                onError('Failed to fetch processing result')
              })
          }
        } else if (update.type === 'snapshot' && update.status === 'completed') {
          // Handle initial snapshot if already completed
          console.log('Received completed snapshot, fetching result')
          onComplete(update)
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e)
        onError('Failed to parse progress update')
      }
    }
    
    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      if (event.code !== 1000) { // Not normal closure
        onError('Connection lost. Refreshing to check status...')
        
        // Fallback: poll for completion
        const pollInterval = setInterval(() => {
          apiFetch(`/api/jobs/${sessionId}`)
            .then(res => res.json())
            .then(data => {
              if (data.status === 'completed') {
                clearInterval(pollInterval)
                if (data.result) {
                  const result = typeof data.result === 'string' ? JSON.parse(data.result) : data.result
                  onComplete(result)
                }
              }
            })
            .catch(() => {
              // Continue polling
            })
        }, 2000)
        
        // Stop polling after 5 minutes
        setTimeout(() => clearInterval(pollInterval), 300000)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      onError('Connection error')
    }
    
    this.ws = ws
    return ws
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close(1000)
      this.ws = null
    }
  }
}