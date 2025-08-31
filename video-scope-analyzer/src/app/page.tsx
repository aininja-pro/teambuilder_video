'use client'

import { useState, useRef } from 'react'
import FileUpload from '@/components/FileUpload'
import ProcessingStatus from '@/components/ProcessingStatus'
import TranscriptView from '@/components/TranscriptView'
import ScopeItemsTable from '@/components/ScopeItemsTable'
import ProjectSummary from '@/components/ProjectSummary'
import DocumentDownload from '@/components/DocumentDownload'
import SavedAnalyses from '@/components/SavedAnalyses'
import { uploader, API_BASE_URL } from '@/utils/api'

interface ScopeItem {
  mainCode: string
  mainCategory: string
  subCode: string
  subCategory: string
  description: string
  details: {
    material?: string
    location?: string
    quantity?: string
    notes?: string
  }
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStep, setProcessingStep] = useState('')
  const [processingProgress, setProcessingProgress] = useState(0)
  const [transcript, setTranscript] = useState('')
  const [scopeItems, setScopeItems] = useState<ScopeItem[]>([])
  const [projectSummary, setProjectSummary] = useState<any>(null)
  const [documents, setDocuments] = useState<{ docx: string | null; pdf: string | null }>({ docx: null, pdf: null })
  const [error, setError] = useState('')
  const [currentAnalysisId, setCurrentAnalysisId] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    // Reset previous results
    setTranscript('')
    setScopeItems([])
    setProjectSummary(null)
    setDocuments({ docx: null, pdf: null })
    setError('')
    setProcessingProgress(0)
    setCurrentAnalysisId(null)
  }

  const handleAnalysisSelected = (analysis: any) => {
    // Load saved analysis into current view
    setTranscript(analysis.transcript)
    setScopeItems(analysis.scope_items)
    setProjectSummary(analysis.project_summary)
    setDocuments({ docx: null, pdf: null }) // Documents not saved yet
    setCurrentAnalysisId(analysis.id)
    setSelectedFile(null) // Clear current file selection
    setError('')
    setProcessingProgress(0)
  }

  const startProcessing = async () => {
    if (!selectedFile) return
    
    setIsProcessing(true)
    setError('')
    setProcessingProgress(0)
    
    try {
      // Start chunked upload
      const sessionId = await uploader.uploadFile(selectedFile, (progress, step) => {
        setProcessingProgress(progress)
        setProcessingStep(step)
      })
      
      // Connect WebSocket for real-time updates
      wsRef.current = uploader.connectWebSocket(
        sessionId,
        // onUpdate
        (update) => {
          if (update.step) {
            setProcessingStep(update.step)
          }
          if (update.progress !== undefined) {
            setProcessingProgress(Math.max(50, update.progress)) // Start from 50% (after upload)
          }
        },
        // onComplete
        (result) => {
          console.log('Processing complete:', result)
          setTranscript(result.transcript || '')
          setScopeItems(result.scope_items || [])
          setProjectSummary(result.project_summary || null)
          setDocuments({
            docx: result.documents?.docx ? `${API_BASE_URL}${result.documents.docx}` : null,
            pdf: result.documents?.pdf ? `${API_BASE_URL}${result.documents.pdf}` : null
          })
          setProcessingStep('Processing complete!')
          setProcessingProgress(100)
          setIsProcessing(false)
          
          if (wsRef.current) {
            wsRef.current.close()
            wsRef.current = null
          }
        },
        // onError
        (errorMessage) => {
          console.error('Processing error:', errorMessage)
          setError(errorMessage)
          setIsProcessing(false)
          setProcessingStep('Processing failed')
          
          if (wsRef.current) {
            wsRef.current.close()
            wsRef.current = null
          }
        }
      )
      
    } catch (error) {
      console.error('Processing failed:', error)
      setError(error instanceof Error ? error.message : 'Upload failed')
      setIsProcessing(false)
      setProcessingStep('')
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Video Scope Analyzer
          </h1>
          <p className="text-gray-600">
            Transform your job site videos into structured scope summaries with AI-powered analysis
          </p>
        </div>

        {/* Saved Analyses Section */}
        <SavedAnalyses onAnalysisSelected={handleAnalysisSelected} />

        {/* Single Column Layout */}
        <div className="space-y-8">
          {/* Upload Section */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Job Video</h2>
            <FileUpload 
              onFileSelect={handleFileSelect}
              isProcessing={isProcessing}
            />

            {selectedFile && (
              <div className="mt-6">
                <button
                  onClick={startProcessing}
                  disabled={isProcessing}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
                >
                  {isProcessing ? 'Processing...' : 'Start Analysis'}
                </button>
              </div>
            )}

            {isProcessing && (
              <div className="mt-6">
                <ProcessingStatus 
                  currentStep={processingStep}
                  progress={processingProgress}
                />
              </div>
            )}

            {error && (
              <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="text-red-800 font-semibold mb-2">Processing Error</h3>
                <p className="text-red-700 text-sm">{error}</p>
                <button
                  onClick={() => setError('')}
                  className="mt-2 text-red-600 hover:text-red-800 text-sm underline"
                >
                  Dismiss
                </button>
              </div>
            )}
          </div>

          {/* Results Section */}
          {(transcript || projectSummary || scopeItems?.length > 0 || documents) && (
            <div className="space-y-6">
              <div className="border-t border-gray-200 pt-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">Analysis Results</h2>
                  {currentAnalysisId && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      📁 Saved Analysis
                    </span>
                  )}
                </div>
              </div>
              
              <TranscriptView transcript={transcript} />
              <ProjectSummary summary={projectSummary} />
              <ScopeItemsTable items={scopeItems} />
              <DocumentDownload documents={documents} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
