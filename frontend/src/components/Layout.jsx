import React, { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const isAdmin = user?.user_type === 'SystemAdmin';
  const isCustomerUser = user?.user_type === 'CXO' || user?.user_type === 'Participant';
  const canViewReports = user?.user_type === 'CXO' || user?.user_type === 'Sales';

  return (
    <div className="min-h-screen bg-gray-50 font-schibsted">
      {/* Top Bar - Darker */}
      <div className="bg-oxford-800 shadow-lg border-b border-oxford-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link to="/" className="text-2xl font-bold text-white hover:text-encora-yellow-400 transition">
                EnTrust
              </Link>
              <img 
                src="https://encora.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fyon5rraf34cy%2F79kzG7hI6Aps6cv6Aocb6H%2F76c56d2335d20935cfecab9696697801%2Fencora_logo_green.svg&w=384&q=75"
                alt="Encora"
                className="h-8"
              />
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-oxford-100 font-medium">{user?.username}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-encora-red-600 text-white rounded-lg hover:bg-encora-red-700 transition font-semibold shadow-md"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation - Even Darker */}
      <div className="bg-oxford-900 text-white shadow-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-1 py-3">
            {isAdmin && (
              <>
                <Link
                  to="/customers"
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    location.pathname.startsWith('/customers') 
                      ? 'bg-encora-yellow-400 text-oxford-900' 
                      : 'text-oxford-100 hover:bg-oxford-700'
                  }`}
                >
                  Customers
                </Link>
                <Link
                  to="/users"
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    location.pathname.startsWith('/users') 
                      ? 'bg-encora-yellow-400 text-oxford-900' 
                      : 'text-oxford-100 hover:bg-oxford-700'
                  }`}
                >
                  Users
                </Link>
                <Link
                  to="/llm-config"
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    location.pathname === '/llm-config' 
                      ? 'bg-encora-yellow-400 text-oxford-900' 
                      : 'text-oxford-100 hover:bg-oxford-700'
                  }`}
                >
                  LLM Configuration
                </Link>
              </>
            )}
            {isCustomerUser && (
              <Link
                to="/survey"
                className={`px-4 py-2 rounded-lg font-semibold transition ${
                  location.pathname.startsWith('/survey') 
                    ? 'bg-encora-yellow-400 text-oxford-900' 
                    : 'text-oxford-100 hover:bg-oxford-700'
                }`}
              >
                Survey
              </Link>
            )}
            {canViewReports && (
              <>
                <Link
                  to="/reports"
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    location.pathname === '/reports'
                      ? 'bg-encora-yellow-400 text-oxford-900'
                      : 'text-oxford-100 hover:bg-oxford-700'
                  }`}
                >
                  Reports
                </Link>
                <Link
                  to="/offline-reports"
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    location.pathname === '/offline-reports'
                      ? 'bg-encora-yellow-400 text-oxford-900'
                      : 'text-oxford-100 hover:bg-oxford-700'
                  }`}
                >
                  Offline Reports
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </div>
    </div>
  );
}