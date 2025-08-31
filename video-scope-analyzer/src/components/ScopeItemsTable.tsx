interface ScopeItem {
  mainCode: string
  mainCategory: string
  subCode: string
  subCategory: string
  description: string
  details?: {
    material?: string
    location?: string
    quantity?: string
    notes?: string
  }
}

interface ScopeItemsTableProps {
  items: ScopeItem[]
}

export default function ScopeItemsTable({ items }: ScopeItemsTableProps) {
  if (!items || items.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <span className="w-1 h-5 bg-green-500 rounded-full mr-3"></span>
          Scope Items
        </h3>
        <div className="text-gray-500 text-center py-8">
          Scope items will appear here after processing
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <span className="w-1 h-5 bg-green-500 rounded-full mr-3"></span>
        Scope Items ({items.length})
      </h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-green-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Code
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {items.map((item, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                  {item.mainCode}
                  {item.subCode && <div className="text-xs text-gray-500">{item.subCode}</div>}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                  {item.mainCategory}
                  {item.subCategory && <div className="text-xs text-gray-500">{item.subCategory}</div>}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  <div className="mb-1">{item.description}</div>
                  {item.details && (
                    <div className="text-xs text-gray-500 space-y-1">
                      {item.details.material && <div><span className="font-medium">Material:</span> {item.details.material}</div>}
                      {item.details.location && <div><span className="font-medium">Location:</span> {item.details.location}</div>}
                      {item.details.quantity && <div><span className="font-medium">Quantity:</span> {item.details.quantity}</div>}
                      {item.details.notes && <div><span className="font-medium">Notes:</span> {item.details.notes}</div>}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}