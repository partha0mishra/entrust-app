import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/auth/login?user_id=${userId}&password=${password}`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Invalid credentials');

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Redirect based on user role
      if (data.user.user_type === 'SystemAdmin') {
        navigate('/customers');
      } else if (data.user.user_type === 'CXO' || data.user.user_type === 'Participant') {
        navigate('/survey');
      } else if (data.user.user_type === 'Sales') {
        navigate('/reports');
      } else {
        navigate('/');
      }
    } catch (err) {
      setError('Invalid user ID or password');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ 
      backgroundColor: '#213459',
      fontFamily: "'Schibsted Grotesk', sans-serif"
    }}>
      <div className="bg-white rounded-xl shadow-2xl p-10 w-full max-w-md" style={{
        boxShadow: '0 4px 20px rgba(10, 17, 30, 0.15)'
      }}>
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4" style={{ 
            color: '#0a111e',
            fontWeight: 800
          }}>
            EnTrust
          </h1>
          <img 
            src="https://encora.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fyon5rraf34cy%2F79kzG7hI6Aps6cv6Aocb6H%2F76c56d2335d20935cfecab9696697801%2Fencora_logo_green.svg&w=384&q=75"
            alt="Encora"
            className="h-12 mx-auto mb-4"
          />
          <p className="text-base" style={{ color: '#2c4477' }}>
            Data Governance Survey Platform
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 rounded-lg border" style={{ 
              backgroundColor: '#fff0ef',
              color: '#b03822',
              borderColor: '#ffafa0'
            }}>
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: '#2c4477' }}>
              User ID
            </label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 transition"
              style={{ 
                borderColor: '#d2dbee',
                fontSize: '1rem'
              }}
              onFocus={(e) => e.target.style.borderColor = '#3d5da4'}
              onBlur={(e) => e.target.style.borderColor = '#d2dbee'}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: '#2c4477' }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 transition"
              style={{ 
                borderColor: '#d2dbee',
                fontSize: '1rem'
              }}
              onFocus={(e) => e.target.style.borderColor = '#3d5da4'}
              onBlur={(e) => e.target.style.borderColor = '#d2dbee'}
              required
            />
          </div>

          <button 
            type="submit" 
            className="w-full py-3 rounded-lg font-semibold transition transform hover:scale-[1.02]"
            style={{
              backgroundColor: '#213459',
              color: 'white',
              fontSize: '1.05rem',
              boxShadow: '0 2px 8px rgba(33, 52, 89, 0.3)'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#2c4477'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#213459'}
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}