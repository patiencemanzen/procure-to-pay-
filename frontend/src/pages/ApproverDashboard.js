import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { purchaseRequestAPI, dashboardAPI } from '../services/api';
import { format } from 'date-fns';
import { toast } from 'react-toastify';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const ApproverDashboard = () => {
  const [pendingRequests, setPendingRequests] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [requestsData, statsData] = await Promise.all([
        purchaseRequestAPI.getPendingRequests(),
        dashboardAPI.getUserStats(),
      ]);
      setPendingRequests(requestsData.results || requestsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApproval = async (requestId, decision, comments = '') => {
    setActionLoading(requestId);
    try {
      await purchaseRequestAPI.approveRequest(requestId, decision, comments);
      toast.success(`Request ${decision} successfully!`);
      // Refresh data
      await fetchData();
    } catch (error) {
      console.error('Error processing approval:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const quickApprove = (requestId) => {
    handleApproval(requestId, 'approved');
  };

  const quickReject = (requestId) => {
    const comments = prompt('Please provide reason for rejection:');
    if (comments !== null) {
      handleApproval(requestId, 'rejected', comments);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading approvals..." />;
  }

  const getStatusBadge = (status) => {
    const statusClasses = {
      pending: 'status-pending',
      approved: 'status-approved',
      rejected: 'status-rejected',
    };
    
    return (
      <span className={statusClasses[status] || 'status-pending'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getApprovalLevel = (request) => {
    const approvals = request.approvals || [];
    const lastApproval = approvals[approvals.length - 1];
    
    if (!lastApproval) {
      return 'Awaiting Level 1 Approval';
    }
    
    if (lastApproval.level === 1 && lastApproval.decision === 'approved') {
      return 'Awaiting Level 2 Approval';
    }
    
    return 'Unknown';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Approver Dashboard</h1>
        <p className="text-gray-600">Review and approve purchase requests</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                  <span className="text-yellow-600 font-medium text-sm">{stats.pending_for_approval}</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Pending Approval</p>
                <p className="text-lg font-semibold text-gray-900">{stats.pending_for_approval}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 font-medium text-sm">{stats.total_approved}</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Approved</p>
                <p className="text-lg font-semibold text-gray-900">{stats.total_approved}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-red-600 font-medium text-sm">{stats.total_rejected}</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Rejected</p>
                <p className="text-lg font-semibold text-gray-900">{stats.total_rejected}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pending Requests */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">Pending Approvals</h2>
          <span className="text-sm text-gray-500">
            Role: {stats?.role?.replace('approver_level_', 'Level ')}
          </span>
        </div>

        {pendingRequests.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No requests pending your approval.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {pendingRequests.map((request) => (
              <div key={request.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-medium text-gray-900">{request.title}</h3>
                      {getStatusBadge(request.status)}
                    </div>
                    
                    <p className="text-gray-600 mb-3">{request.description}</p>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Amount:</span>
                        <span className="ml-2 font-medium">RWF {parseFloat(request.amount).toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Requested by:</span>
                        <span className="ml-2 font-medium">{request.created_by.full_name}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Created:</span>
                        <span className="ml-2">{format(new Date(request.created_at), 'MMM dd, yyyy')}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Stage:</span>
                        <span className="ml-2">{getApprovalLevel(request)}</span>
                      </div>
                    </div>

                    {/* Items preview */}
                    {request.items && request.items.length > 0 && (
                      <div className="mt-3">
                        <span className="text-gray-500 text-sm">Items:</span>
                        <div className="mt-1 space-y-1">
                          {request.items.slice(0, 3).map((item, index) => (
                            <div key={index} className="text-sm text-gray-600">
                              {item.name} (Qty: {item.quantity} × RWF {parseFloat(item.unit_price).toLocaleString()})
                            </div>
                          ))}
                          {request.items.length > 3 && (
                            <div className="text-sm text-gray-500">
                              ...and {request.items.length - 3} more items
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="ml-6 flex flex-col space-y-2">
                    <Link
                      to={`/requests/${request.id}`}
                      className="btn-secondary text-sm"
                    >
                      View Details
                    </Link>
                    
                    <button
                      onClick={() => quickApprove(request.id)}
                      disabled={actionLoading === request.id}
                      className="btn-success text-sm disabled:opacity-50"
                    >
                      {actionLoading === request.id ? 'Processing...' : 'Quick Approve'}
                    </button>
                    
                    <button
                      onClick={() => quickReject(request.id)}
                      disabled={actionLoading === request.id}
                      className="btn-danger text-sm disabled:opacity-50"
                    >
                      {actionLoading === request.id ? 'Processing...' : 'Quick Reject'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ApproverDashboard;