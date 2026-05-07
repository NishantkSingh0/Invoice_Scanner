import { createContext, useState, useContext, useEffect } from 'react'

const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [token, setToken] = useState(null)
  const [userId, setUserId] = useState(null)
  const [loading, setLoading] = useState(true)
  const Backend_url = "http://127.0.0.1:8000/"                // http://127.0.0.1:8000/      or       https://invoice-scanner-7hgz.vercel.app/
  // Check for existing token in localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('authToken')
    if (storedToken) {
      verifyStoredToken(storedToken)
    } else {
      setLoading(false)
    }
  }, [])

  const verifyStoredToken = async (storedToken) => {
    try {
      const response = await fetch(`${Backend_url}verify-token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: storedToken }),
      })

      const data = await response.json()

      if (data.status === 'valid') {
        setToken(storedToken)
        setUserId(data.user_id)
        setIsAuthenticated(true)
      } else {
        // Token is invalid or expired, clear it
        localStorage.removeItem('authToken')
        localStorage.removeItem('userId')
        setIsAuthenticated(false)
        setToken(null)
        setUserId(null)
      }
    } catch (error) {
      console.error('Error verifying token:', error)
      localStorage.removeItem('authToken')
      localStorage.removeItem('userId')
      setIsAuthenticated(false)
      setToken(null)
      setUserId(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (user_id, password) => {
    try {
      const response = await fetch(`${Backend_url}login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id, password }),
      })

      const data = await response.json()

      if (data.status === 'success') {
        const authToken = data.token
        setToken(authToken)
        setUserId(data.user_id)
        setIsAuthenticated(true)

        // Store in localStorage
        localStorage.setItem('authToken', authToken)
        localStorage.setItem('userId', data.user_id)

        return { success: true, message: data.message }
      } else {
        return { success: false, error: data.error }
      }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }

  const logout = () => {
    setToken(null)
    setUserId(null)
    setIsAuthenticated(false)
    localStorage.removeItem('authToken')
    localStorage.removeItem('userId')
  }

  const value = {
    isAuthenticated,
    token,
    userId,
    loading,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
