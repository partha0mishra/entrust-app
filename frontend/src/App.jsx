import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import CustomerList from './pages/CustomerList';
import CustomerForm from './pages/CustomerForm';
import UserList from './pages/UserList';
import UserForm from './pages/UserForm';
import LLMConfig from './pages/LLMConfig';
import SurveyDashboard from './pages/SurveyDashboard';
import SurveySection from './pages/SurveySection';
import Reports from './pages/Reports';

// Component to handle default redirect based on user role
function DefaultRedirect() {
  const userData = localStorage.getItem('user');
  
  if (!userData) {
    return <Navigate to="/login" replace />;
  }
  
  const user = JSON.parse(userData);
  
  if (user.user_type === 'SystemAdmin') {
    return <Navigate to="/customers" replace />;
  } else if (user.user_type === 'CXO' || user.user_type === 'Participant') {
    return <Navigate to="/survey" replace />;
  } else if (user.user_type === 'Sales') {
    return <Navigate to="/reports" replace />;
  }
  
  return <Navigate to="/login" replace />;
}

// Admin-only route wrapper
function AdminRoute({ children }) {
  const userData = localStorage.getItem('user');
  
  if (!userData) {
    return <Navigate to="/login" replace />;
  }
  
  const user = JSON.parse(userData);
  
  if (user.user_type !== 'SystemAdmin') {
    return <Navigate to="/" replace />;
  }
  
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<DefaultRedirect />} />
          
          {/* Admin-only routes */}
          <Route path="customers" element={<AdminRoute><CustomerList /></AdminRoute>} />
          <Route path="customers/new" element={<AdminRoute><CustomerForm /></AdminRoute>} />
          <Route path="customers/:id/edit" element={<AdminRoute><CustomerForm /></AdminRoute>} />
          <Route path="users" element={<AdminRoute><UserList /></AdminRoute>} />
          <Route path="users/new" element={<AdminRoute><UserForm /></AdminRoute>} />
          <Route path="users/:id/edit" element={<AdminRoute><UserForm /></AdminRoute>} />
          <Route path="llm-config" element={<AdminRoute><LLMConfig /></AdminRoute>} />
          
          {/* Customer user routes */}
          <Route path="survey" element={<SurveyDashboard />} />
          <Route path="survey/:dimension" element={<SurveySection />} />
          
          {/* Reports routes */}
          <Route path="reports" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;