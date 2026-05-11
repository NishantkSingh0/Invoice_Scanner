import { useNavigate } from 'react-router-dom'

export default function SelectionPage() {
  const navigate = useNavigate()

  const handleSelection = (keyName) => {
    navigate('/login', { state: { key_name: keyName } })
  }

  const options = [
    {
      id: 'bank',
      title: 'Bank Statement',
      description: 'Process and analyze bank statements',
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      id: 'purchase',
      title: 'Purchase Invoice',
      description: 'Manage purchase invoices',
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      id: 'sales',
      title: 'Sales Invoice',
      description: 'Handle sales invoices',
      color: 'bg-purple-500 hover:bg-purple-600'
    }
  ]

  return (
    <div className="min-h-screen bg-gray-200 flex items-center justify-center p-4">
      <div className="max-w-6xl w-full">
        <h1 className="md:block hidden text-4xl font-bold text-gray-800 mb-4 text-center">
          Select Document Type
        </h1>
        <p className="md:block hidden text-gray-600 text-center mb-12">
          Choose the type of document you want to process
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {options.map((option) => (
            <div
              key={option.id}
              onClick={() => handleSelection(option.id)}
              className="bg-white rounded-lg shadow-lg p-8 cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-xl"
            >
              <div className="text-center">
                <div className="text-6xl mb-4">{option.icon}</div>
                <h2 className="text-2xl font-bold text-gray-800 mb-3">
                  {option.title}
                </h2>
                <p className="text-gray-600 mb-6">{option.description}</p>
                <button
                  className={`w-full ${option.color} text-white font-semibold py-3 px-6 rounded-lg transition duration-200`}
                >
                  Select
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
