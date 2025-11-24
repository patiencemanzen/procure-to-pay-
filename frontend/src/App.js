import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import LoginPage from './pages/LoginPage';
import StaffDashboard from './pages/StaffDashboard';
import ApproverDashboard from './pages/ApproverDashboard';
import FinanceDashboard from './pages/FinanceDashboard';
import RequestForm from './pages/RequestForm';
import RequestDetail from './pages/RequestDetail';
import LoadingSpinner from './components/UI/LoadingSpinner';

// Protected Route component
const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

// Dashboard router based on user role
const DashboardRouter = () => {
  const { user } = useAuth();

  switch (user?.role) {
    case 'staff':
      return <StaffDashboard />;
    case 'approver_lvl1':
    case 'approver_lvl2':
      return <ApproverDashboard />;
    case 'finance':
      return <FinanceDashboard />;
    default:
      return <Navigate to="/unauthorized" replace />;
  }
};

function App() {
  const { loading } = useAuth();

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="App">
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardRouter />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardRouter />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/requests/new"
          element={
            <ProtectedRoute allowedRoles={['staff']}>
              <Layout>
                <RequestForm />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/requests/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <RequestDetail />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/requests/:id/edit"
          element={
            <ProtectedRoute allowedRoles={['staff']}>
              <Layout>
                <RequestForm />
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/unauthorized"
          element={
            <div className="min-h-screen flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-gray-900">Unauthorized</h1>
                <p className="text-gray-600">You don't have permission to access this page.</p>
              </div>
            </div>
          }
        />

        <Route
          path="*"
          element={
            <div className="min-h-screen flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-2xl font-bold text-gray-900">Page Not Found</h1>
                <p className="text-gray-600">The page you're looking for doesn't exist.</p>
              </div>
            </div>
          }
        />
      </Routes>
    </div>
  );
}

export default App;