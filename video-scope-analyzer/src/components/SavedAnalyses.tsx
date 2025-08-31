'use client'

import { useState, useEffect } from 'react'
import { TrashIcon, EyeIcon, CalendarIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

interface AnalysisListItem {
  id: string
  filename: string
  created_at: string
  file_size_mb?: number
  scope_count: number
}

interface SavedAnalysis {
  id: string
  filename: string
  created_at: string
  transcript: string
  scope_items: any[]
  project_summary: any
  file_size_mb?: number
}

interface SavedAnalysesProps {
  onAnalysisSelected: (analysis: SavedAnalysis) => void
  show?: boolean
  onToggle?: () => void
}

export default function SavedAnalyses({ onAnalysisSelected, show = false, onToggle }: SavedAnalysesProps) {
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadAnalyses()
  }, [])

  const loadAnalyses = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/analyses')
      if (response.ok) {
        const data = await response.json()
        setAnalyses(data)
      } else {
        setError('Failed to load saved analyses')
      }
    } catch (err) {
      setError('Failed to load saved analyses')
    } finally {
      setLoading(false)
    }
  }

  const viewAnalysis = async (id: string) => {
    try {
      const response = await fetch(`/api/analyses/${id}`)
      if (response.ok) {
        const analysis = await response.json()
        onAnalysisSelected(analysis)
        if (onToggle) onToggle()
      } else {
        setError('Failed to load analysis')
      }
    } catch (err) {
      setError('Failed to load analysis')
    }
  }

  const deleteAnalysis = async (id: string) => {
    if (!confirm('Are you sure you want to delete this analysis? This action cannot be undone.')) {
      return
    }

    try {
      const response = await fetch(`/api/analyses/${id}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        setAnalyses(analyses.filter(a => a.id !== id))
      } else {
        setError('Failed to delete analysis')
      }
    } catch (err) {
      setError('Failed to delete analysis')
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  if (!show) {
    return (
      <div className="mb-6">
        <button
          onClick={onToggle}
          className="flex items-center space-x-2 bg-green-50 hover:bg-green-100 text-green-700 hover:text-green-800 px-4 py-2 rounded-lg border border-green-200 transition-colors shadow-sm"
        >
          <DocumentTextIcon className="h-5 w-5" />
          <span>📁 View Saved Analyses ({analyses.length})</span>
        </button>
      </div>
    )
  }

  return (
    <div className="bg-white border border-green-200 rounded-lg p-6 mb-8 shadow-md">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center">
          <span className="w-1 h-6 bg-green-500 rounded-full mr-3"></span>
          Saved Analyses
        </h2>
        <button
          onClick={onToggle}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-red-700 text-sm">{error}</p>
          <button
            onClick={() => setError('')}
            className="text-red-600 hover:text-red-800 text-sm underline mt-1"
          >
            Dismiss
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 mt-2">Loading saved analyses...</p>
        </div>
      ) : analyses.length === 0 ? (
        <div className="text-center py-8">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">No saved analyses yet</p>
          <p className="text-gray-500 text-sm">Process a video to create your first saved analysis</p>
        </div>
      ) : (
        <div className="space-y-3">
          {analyses.map((analysis) => (
            <div
              key={analysis.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-3">
                  <DocumentTextIcon className="h-5 w-5 text-gray-400 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {analysis.filename}
                    </p>
                    <div className="flex items-center space-x-4 mt-1">
                      <div className="flex items-center space-x-1 text-xs text-gray-500">
                        <CalendarIcon className="h-3 w-3" />
                        <span>{formatDate(analysis.created_at)}</span>
                      </div>
                      {analysis.file_size_mb && (
                        <span className="text-xs text-gray-500">
                          {analysis.file_size_mb.toFixed(1)} MB
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {analysis.scope_count} scope items
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={() => viewAnalysis(analysis.id)}
                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-md transition-colors"
                >
                  <EyeIcon className="h-4 w-4" />
                  <span>View</span>
                </button>
                <button
                  onClick={() => deleteAnalysis(analysis.id)}
                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-red-50 text-red-700 hover:bg-red-100 rounded-md transition-colors"
                >
                  <TrashIcon className="h-4 w-4" />
                  <span>Delete</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-gray-200">
        <button
          onClick={loadAnalyses}
          className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
        >
          🔄 Refresh List
        </button>
      </div>
    </div>
  )
}