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
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <span className="w-1 h-5 bg-green-500 rounded-full mr-3"></span>
          Project Summary
        </h3>
        <div className="text-gray-500 text-center py-8">
          Project summary will appear here after processing
        </div>
      </div>
    )
  }

  const Section = ({ title, items, className = "" }: { title: string, items?: any, className?: string }) => {
    if (!items) return null
    
    // Handle different data types - convert to array if needed
    let itemsArray: string[] = []
    
    if (Array.isArray(items)) {
      itemsArray = items
    } else if (typeof items === 'string') {
      // Split string by common delimiters
      itemsArray = items.split(/[,;•\n]/).map(item => item.trim()).filter(item => item.length > 0)
    } else if (typeof items === 'object' && items !== null) {
      // Handle object - use values or convert to string
      itemsArray = Object.values(items).filter(item => Boolean(item) && typeof item === 'string') as string[]
    }
    
    if (itemsArray.length === 0) return null
    
    return (
      <div className={className}>
        <h4 className="font-semibold text-gray-800 mb-2">{title}</h4>
        <ul className="space-y-1">
          {itemsArray.map((item, index) => (
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
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <span className="w-1 h-5 bg-green-500 rounded-full mr-3"></span>
        Project Summary
      </h3>
      
      <div className="space-y-4">
        
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