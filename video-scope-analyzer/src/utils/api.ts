export const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost' 
  ? '' // Use same domain in production
  : 'http://localhost:8000' // Use localhost in development

export interface UploadChunkResponse {
  session_id: string
  chunk_index: number
  received_chunks: number
  total_chunks: number
  progress: number
  complete: boolean
}

export interface ProcessingUpdate {
  type: 'processing_update' | 'completion' | 'error'
  step?: string
  progress?: number
  status?: string
  result?: any
  message?: string
}

export class ChunkedUploader {
  private chunkSize = 1024 * 1024 // 1MB chunks
  
  async uploadFile(
    file: File, 
    onProgress: (progress: number, step: string) => void
  ): Promise<string> {
    try {
      const chunks = this.createChunks(file)
      const totalChunks = chunks.length
      let sessionId = ''
      
      onProgress(0, 'Preparing upload...')
      
      // Upload chunks
      for (let i = 0; i < chunks.length; i++) {
        const chunk = chunks[i]
        const formData = new FormData()
        
        formData.append('chunk', chunk)
        formData.append('chunk_index', i.toString())
        formData.append('total_chunks', totalChunks.toString())
        formData.append('filename', file.name)
        
        if (sessionId) {
          formData.append('session_id', sessionId)
        }
        
        const response = await fetch(`${API_BASE_URL}/api/upload/chunk`, {
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
      const completeResponse = await fetch(`${API_BASE_URL}/api/upload/complete/${sessionId}`, {
        method: 'POST'
      })
      
      if (!completeResponse.ok) {
        throw new Error(`Upload completion failed: ${completeResponse.statusText}`)
      }
      
      onProgress(50, 'Upload complete. Starting processing...')
      
      return sessionId
      
    } catch (error) {
      console.error('Upload failed:', error)
      throw error
    }
  }
  
  private createChunks(file: File): Blob[] {
    const chunks: Blob[] = []
    let start = 0
    
    while (start < file.size) {
      const end = Math.min(start + this.chunkSize, file.size)
      chunks.push(file.slice(start, end))
      start = end
    }
    
    return chunks
  }
  
  connectWebSocket(
    sessionId: string, 
    onUpdate: (update: ProcessingUpdate) => void,
    onComplete: (result: any) => void,
    onError: (error: string) => void
  ): WebSocket {
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`)
    
    ws.onopen = () => {
      console.log('WebSocket connected for session:', sessionId)
    }
    
    ws.onmessage = (event) => {
      try {
        console.log('WebSocket message received:', event.data)
        const update: ProcessingUpdate = JSON.parse(event.data)
        
        // Handle ChatGPT's Redis pub/sub message format
        if ((update as any).type === 'progress') {
          const pct = Number((update as any).pct || 0)
          const msg = (update as any).msg as string || ''
          const status = (update as any).status || 'processing'
          
          console.log(`Progress update: ${pct}%, ${msg}, status: ${status}`)
          
          onUpdate({
            type: 'processing_update',
            progress: pct,
            status: status,
            step: msg
          })
          
          // Check if completed and fetch final result
          if (pct >= 100 && status === 'completed') {
            console.log('Job completed, fetching final result for session:', sessionId)
            // Fetch final result from Redis
            fetch(`${API_BASE_URL}/api/jobs/${sessionId}`)
              .then(res => res.json())
              .then(data => {
                console.log('Final result data:', data)
                if (data.result) {
                  const result = JSON.parse(data.result)
                  console.log('Parsed result:', result)
                  onComplete(result)
                }
              })
              .catch(err => {
                console.error('Failed to fetch final result:', err)
                onError('Failed to fetch final result')
              })
          }
          return
        }
        
        // Handle snapshot messages
        if ((update as any).type === 'snapshot') {
          const pct = Number((update as any).pct || 0)
          const msg = (update as any).msg as string || ''
          const status = (update as any).status || 'processing'
          
          if (pct >= 100 && status === 'completed' && (update as any).result) {
            const result = JSON.parse((update as any).result)
            onComplete(result)
          } else {
            onUpdate({
              type: 'processing_update',
              progress: pct,
              status: status,
              step: msg
            })
          }
          return
        }

        switch (update.type) {
          case 'processing_update':
            onUpdate(update)
            break
          case 'completion':
            onComplete(update.result)
            break
          case 'error':
            onError(update.message || 'Processing failed')
            break
          default:
            console.log('WebSocket message:', update)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      onError('Connection error')
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }
    
    return ws
  }
}

export const uploader = new ChunkedUploader()