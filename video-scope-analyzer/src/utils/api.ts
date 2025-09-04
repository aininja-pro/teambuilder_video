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
  step?: string
  progress?: number
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

// Export for backward compatibility
export const uploader = {
  uploadFile: uploadFileInChunks
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
    let completed = false
    
    ws.onopen = () => {
      console.log('WebSocket connected for session:', sessionId)
    }
    
    ws.onmessage = async (event) => {
      let msg: any
      try {
        msg = JSON.parse(event.data)
      } catch {
        return
      }
      
      console.log('WebSocket message:', msg)
      
      if (msg.type === 'progress') {
        if (typeof msg.pct === 'number') {
          onUpdate(msg)
        }
        
        if (msg.status === 'completed' || msg.pct === 100) {
          completed = true
          
          // Fetch final result once, then close gracefully
          try {
            console.log('Job completed, fetching final result for session:', sessionId)
            const res = await apiFetch(`/api/jobs/${sessionId}`)
            const data = await res.json()
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
              onComplete(data)
            }
          } catch (e: any) {
            onError(`Finalize fetch failed: ${e?.message ?? e}`)
          } finally {
            // Tell the browser this is a normal close
            try {
              ws.close(1000, 'done')
            } catch {}
          }
        }
      } else if (msg.type === 'snapshot' && msg.status === 'completed') {
        // Handle initial snapshot if already completed
        completed = true
        console.log('Received completed snapshot, fetching result')
        onComplete(msg)
      }
    }
    
    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason)
      
      // Triple-check before showing error banner:
      // 1. Job must not be completed
      // 2. Close code must not be normal (1000, 1005)
      // 3. API check must confirm status ≠ complete
      
      // Check 1: If already completed, this is normal
      if (completed) {
        return
      }
      
      // Check 2: Normal close codes should not trigger errors
      if (event.code === 1000 || event.code === 1005) {
        return
      }
      
      // Check 3: One-shot status verification before showing error
      apiFetch(`/api/jobs/${sessionId}`)
        .then(res => res.json())
        .then(data => {
          // Only show error if job is truly not complete
          if (data?.status !== 'completed' && data?.status !== 'complete') {
            onError(`Connection lost (code ${event.code}). Retrying or refresh to continue.`)
          } else {
            // Job actually completed, treat as success
            onComplete(data)
          }
        })
        .catch(() => {
          // If API check fails, show error as last resort
          onError(`Connection lost (code ${event.code}).`)
        })
    }
    
    ws.onerror = () => {
      // Don't double-report if we've already completed
      if (!completed) {
        console.error('WebSocket error')
        onError('WebSocket error')
      }
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