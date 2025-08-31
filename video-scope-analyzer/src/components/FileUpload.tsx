'use client'

import { useState, useCallback, useRef } from 'react'
import { Upload, FileVideo, FileAudio, X, AlertCircle, CheckCircle } from 'lucide-react'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  isProcessing?: boolean
}

export default function FileUpload({ onFileSelect, isProcessing = false }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }, [])

  const validateFile = (file: File) => {
    const validTypes = [
      'video/mp4', 'video/quicktime', 'video/mpeg', 'video/webm',
      'audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/flac'
    ]
    
    if (!validTypes.includes(file.type)) {
      throw new Error('Invalid file type. Please upload MP4, MOV, MP3, or other supported formats.')
    }
    
    const maxSize = 500 * 1024 * 1024 // 500MB
    if (file.size > maxSize) {
      throw new Error('File size exceeds 500MB limit. Please use a smaller file.')
    }
    
    return true
  }

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return
    
    const file = files[0]
    
    try {
      validateFile(file)
      setSelectedFile(file)
      onFileSelect(file)
    } catch (error) {
      alert(error instanceof Error ? error.message : 'File validation failed')
    }
  }, [onFileSelect])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files)
    }
  }, [handleFiles])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files)
  }, [handleFiles])

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('video/')) {
      return <FileVideo className="h-8 w-8 text-blue-500" />
    } else {
      return <FileAudio className="h-8 w-8 text-green-500" />
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileWarning = (file: File) => {
    const sizeMB = file.size / (1024 * 1024)
    const isMovFile = file.name.toLowerCase().endsWith('.mov')
    
    if (isMovFile && sizeMB > 200) {
      return {
        type: 'error' as const,
        message: 'Large MOV files often fail. Consider converting to MP4 or extracting audio first.'
      }
    } else if (isMovFile && sizeMB > 100) {
      return {
        type: 'warning' as const,
        message: 'MOV files may need conversion. MP4 format is more reliable.'
      }
    } else if (sizeMB > 300) {
      return {
        type: 'warning' as const,
        message: 'Large file detected. Processing will take longer.'
      }
    }
    
    return null
  }

  const clearFile = () => {
    setSelectedFile(null)
    setUploadProgress(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {!selectedFile ? (
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-blue-400 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">
            Upload Job Site Video or Audio
          </h3>
          <p className="text-gray-500 mb-4">
            Drag and drop your file here, or click to browse
          </p>
          
          <button
            onClick={() => fileInputRef.current?.click()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium transition-colors"
            disabled={isProcessing}
          >
            Choose File
          </button>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/quicktime,video/mpeg,video/webm,audio/mp3,audio/mpeg,audio/wav,audio/m4a,audio/flac"
            onChange={handleFileInput}
            className="hidden"
          />
          
          <p className="text-xs text-gray-400 mt-4">
            Supports MP4, MOV, MP3, WAV, and other formats • Max 500MB
          </p>
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg p-6 bg-white">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-4">
              {getFileIcon(selectedFile)}
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">{selectedFile.name}</h4>
                <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
                
                {/* File warnings */}
                {(() => {
                  const warning = getFileWarning(selectedFile)
                  if (!warning) return null
                  
                  return (
                    <div className={`flex items-center space-x-2 mt-2 p-2 rounded-md ${
                      warning.type === 'error' 
                        ? 'bg-red-50 text-red-700' 
                        : 'bg-yellow-50 text-yellow-700'
                    }`}>
                      <AlertCircle className="h-4 w-4" />
                      <span className="text-sm">{warning.message}</span>
                    </div>
                  )
                })()}
                
                {uploadProgress > 0 && uploadProgress < 100 && (
                  <div className="mt-2">
                    <div className="bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Uploading... {uploadProgress}%</p>
                  </div>
                )}
                
                {uploadProgress === 100 && (
                  <div className="flex items-center space-x-2 mt-2 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm">Upload complete</span>
                  </div>
                )}
              </div>
            </div>
            
            {!isProcessing && (
              <button
                onClick={clearFile}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}