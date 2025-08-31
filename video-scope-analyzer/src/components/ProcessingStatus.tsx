import { Loader2, CheckCircle } from 'lucide-react'

interface ProcessingStatusProps {
  currentStep: string
  progress: number
}

export default function ProcessingStatus({ currentStep, progress }: ProcessingStatusProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Status</h3>
      
      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
          <span className="text-gray-700">{currentStep}</span>
        </div>
        
        {progress > 0 && (
          <div className="w-full">
            <div className="bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">{progress}% complete</p>
          </div>
        )}
      </div>
    </div>
  )
}