import { Download, FileText, File } from 'lucide-react'

interface Documents {
  docx: string | null
  pdf: string | null
}

interface DocumentDownloadProps {
  documents: Documents
}

export default function DocumentDownload({ documents }: DocumentDownloadProps) {
  const hasDocuments = documents.docx || documents.pdf

  if (!hasDocuments) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Download Documents</h3>
        <div className="text-gray-500 text-center py-8">
          Documents will be available for download after processing
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Download Documents</h3>
      
      <div className="space-y-3">
        {documents.docx && (
          <a
            href={documents.docx}
            download
            className="flex items-center justify-between p-3 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <FileText className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-gray-700">Scope Summary.docx</span>
            </div>
            <Download className="h-4 w-4 text-gray-400" />
          </a>
        )}
        
        {documents.pdf && (
          <a
            href={documents.pdf}
            download
            className="flex items-center justify-between p-3 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <File className="h-5 w-5 text-red-600" />
              <span className="font-medium text-gray-700">Scope Summary.pdf</span>
            </div>
            <Download className="h-4 w-4 text-gray-400" />
          </a>
        )}
      </div>
    </div>
  )
}