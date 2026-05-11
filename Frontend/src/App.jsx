import Renderer from './components/Renderer'
import Login from './components/Login'
import SelectionPage from './components/SelectionPage'
import ProtectedRoute from './components/ProtectedRoute'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'

function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster position="top-right" />
        <Routes>
          <Route path="/select" element={<SelectionPage />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Renderer />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/select" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
