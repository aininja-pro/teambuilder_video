interface ProjectSummaryProps {
  summary: {
    sentiment?: string
    overview?: string
    keyRequirements?: string[]
    concerns?: string[]
    decisionPoints?: string[]
    importantNotes?: string[]
  } | null
}

export default function ProjectSummary({ summary }: ProjectSummaryProps) {
  if (!summary) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Summary</h3>
        <div className="text-gray-500 text-center py-8">
          Project summary will appear here after processing
        </div>
      </div>
    )
  }

  const Section = ({ title, items, className = "" }: { title: string, items?: string[], className?: string }) => {
    if (!items || items.length === 0) return null
    
    return (
      <div className={className}>
        <h4 className="font-semibold text-gray-800 mb-2">{title}</h4>
        <ul className="space-y-1">
          {items.map((item, index) => (
            <li key={index} className="text-sm text-gray-600 flex items-start">
              <span className="text-gray-400 mr-2">•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Summary</h3>
      
      <div className="space-y-4">
        {summary.sentiment && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Overall Sentiment</h4>
            <p className="text-sm text-gray-600 bg-blue-50 px-3 py-2 rounded-md">
              {summary.sentiment}
            </p>
          </div>
        )}
        
        {summary.overview && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Overview</h4>
            <p className="text-sm text-gray-600">{summary.overview}</p>
          </div>
        )}
        
        <div className="grid md:grid-cols-2 gap-4">
          <Section 
            title="Key Requirements" 
            items={summary.keyRequirements} 
            className="bg-green-50 p-3 rounded-md"
          />
          
          <Section 
            title="Concerns" 
            items={summary.concerns} 
            className="bg-yellow-50 p-3 rounded-md"
          />
          
          <Section 
            title="Decision Points" 
            items={summary.decisionPoints} 
            className="bg-blue-50 p-3 rounded-md"
          />
          
          <Section 
            title="Important Notes" 
            items={summary.importantNotes} 
            className="bg-purple-50 p-3 rounded-md"
          />
        </div>
      </div>
    </div>
  )
}