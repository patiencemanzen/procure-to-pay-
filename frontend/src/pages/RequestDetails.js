import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { purchaseRequestAPI } from '../services/api';
import { format } from 'date-fns';
import { toast } from 'react-toastify';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const RequestDetails = () => {
  const { id } = useParams();
  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadRequest();
  }, [loadRequest]);

  const loadRequest = useCallback(async () => {
    try {
      const data = await purchaseRequestAPI.getRequest(id);
      setRequest(data);
    } catch (error) {
      console.error('Error loading request:', error);
      toast.error('Failed to load request details');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const handleApproval = async (action) => {
    setActionLoading(true);
    try {
      await purchaseRequestAPI.approveRequest(id, { action });
      toast.success(`Request ${action}d successfully!`);
      loadRequest(); // Reload to get updated status
    } catch (error) {
      console.error(`Error ${action}ing request:`, error);
      toast.error(`Failed to ${action} request`);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      PENDING: 'bg-yellow-100 text-yellow-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusClasses[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  const getApprovalLevelDisplay = (level) => {
    return level === 1 ? 'Level 1 Approver' : 'Level 2 Approver';
  };

  if (loading) {
    return <LoadingSpinner message="Loading request details..." />;
  }

  if (!request) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Request Not Found</h2>
          <p className="text-gray-600">The request you're looking for doesn't exist or you don't have permission to view it.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{request.title}</h1>
            <p className="text-gray-600 mt-1">Request #{request.id}</p>
          </div>
          <div className="text-right">
            {getStatusBadge(request.status)}
            <p className="text-sm text-gray-600 mt-1">
              Created: {format(new Date(request.created_at), 'MMM dd, yyyy')}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Requested By</h3>
            <p className="mt-2 text-lg font-semibold">{request.created_by?.full_name}</p>
            <p className="text-gray-600">{request.created_by?.email}</p>
          </div>
          
          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total Amount</h3>
            <p className="mt-2 text-2xl font-bold text-green-600">RWF {parseFloat(request.amount).toLocaleString()}</p>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Current Status</h3>
            <p className="mt-2">{getStatusBadge(request.status)}</p>
          </div>
        </div>
      </div>

      {/* Description */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Description</h2>
        <p className="text-gray-700 whitespace-pre-wrap">{request.description}</p>
      </div>

      {/* Items */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Items</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Item
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Unit Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {request.items.map((item, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {item.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.quantity}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    RWF {parseFloat(item.unit_price).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    RWF {(item.quantity * parseFloat(item.unit_price)).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr>
                <td colSpan="3" className="px-6 py-4 text-right text-sm font-medium text-gray-900">
                  Total Amount:
                </td>
                <td className="px-6 py-4 text-sm font-bold text-gray-900">
                  RWF {parseFloat(request.amount).toLocaleString()}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Approval History */}
      {request.approvals && request.approvals.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Approval History</h2>
          <div className="space-y-4">
            {request.approvals.map((approval, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {getApprovalLevelDisplay(approval.level)}
                    </h3>
                    <p className="text-gray-600">
                      {approval.approver?.full_name}
                    </p>
                    <p className="text-sm text-gray-500">{approval.approver?.email}</p>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(approval.status)}
                    {approval.approved_at && (
                      <p className="text-sm text-gray-600 mt-1">
                        {format(new Date(approval.approved_at), 'MMM dd, yyyy HH:mm')}
                      </p>
                    )}
                  </div>
                </div>
                {approval.comments && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-700">{approval.comments}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Proforma Invoice */}
      {request.proforma && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Proforma Invoice</h2>
          <a
            href={request.proforma}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            View Proforma Invoice
          </a>
        </div>
      )}

      {/* Purchase Order */}
      {request.purchase_order && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Purchase Order</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">PO Number</p>
              <p className="font-semibold">{request.purchase_order.po_number}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Generated On</p>
              <p className="font-semibold">
                {format(new Date(request.purchase_order.created_at), 'MMM dd, yyyy HH:mm')}
              </p>
            </div>
          </div>
          {request.purchase_order.po_file && (
            <div className="mt-4">
              <a
                href={request.purchase_order.po_file}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-800"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download Purchase Order PDF
              </a>
            </div>
          )}
        </div>
      )}

      {/* Approval Actions (for approvers) */}
      {request.can_approve && request.status === 'PENDING' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Approval Actions</h2>
          <div className="flex space-x-4">
            <button
              onClick={() => handleApproval('approve')}
              disabled={actionLoading}
              className="btn-primary"
            >
              {actionLoading ? (
                <div className="flex items-center">
                  <div className="spinner mr-2"></div>
                  Processing...
                </div>
              ) : (
                'Approve'
              )}
            </button>
            <button
              onClick={() => handleApproval('reject')}
              disabled={actionLoading}
              className="btn-danger"
            >
              {actionLoading ? (
                <div className="flex items-center">
                  <div className="spinner mr-2"></div>
                  Processing...
                </div>
              ) : (
                'Reject'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RequestDetails;