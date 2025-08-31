interface TranscriptViewProps {
  transcript: string
}

export default function TranscriptView({ transcript }: TranscriptViewProps) {
  if (!transcript) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <span className="w-1 h-5 bg-green-500 rounded-full mr-3"></span>
          Transcript Preview
        </h3>
        <div className="text-gray-500 text-center py-8">
          Transcript will appear here after processing
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <span className="w-1 h-5 bg-green-500 rounded-full mr-3"></span>
        Transcript
      </h3>
      <div className="bg-green-50 border border-green-100 rounded-md p-4 max-h-64 overflow-y-auto">
        <p className="text-sm text-gray-800 whitespace-pre-wrap">{transcript}</p>
      </div>
    </div>
  )
}