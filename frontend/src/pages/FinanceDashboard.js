import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { financeAPI, dashboardAPI } from '../services/api';
import { format } from 'date-fns';
import { toast } from 'react-toastify';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const FinanceDashboard = () => {
  const [approvedRequests, setApprovedRequests] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [validationLoading, setValidationLoading] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [requestsData, statsData] = await Promise.all([
        financeAPI.getApprovedRequests(),
        dashboardAPI.getUserStats(),
      ]);
      setApprovedRequests(requestsData.results || requestsData);
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReceiptValidation = async (purchaseOrderId, event) => {
    const file = event.target.files[0];
    if (!file) return;

    setValidationLoading(purchaseOrderId);
    try {
      const result = await financeAPI.validateReceipt(purchaseOrderId, file);
      
      if (result.is_valid) {
        toast.success('Receipt validated successfully!');
      } else {
        toast.warning(`Receipt validation found ${result.discrepancies.length} discrepancies.`);
      }
      
      // Refresh data
      await fetchData();
    } catch (error) {
      console.error('Error validating receipt:', error);
    } finally {
      setValidationLoading(null);
      // Clear file input
      event.target.value = '';
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading finance dashboard..." />;
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Finance Dashboard</h1>
        <p className="text-gray-600">Manage approved requests and validate receipts</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 font-medium text-sm">{stats.approved_requests}</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Approved Requests</p>
                <p className="text-lg font-semibold text-gray-900">{stats.approved_requests}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-medium text-sm">{stats.total_purchase_orders}</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Purchase Orders</p>
                <p className="text-lg font-semibold text-gray-900">{stats.total_purchase_orders}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 font-medium text-sm">{stats.receipt_validations}</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Receipt Validations</p>
                <p className="text-lg font-semibold text-gray-900">{stats.receipt_validations}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 font-medium text-sm">{stats.valid_receipts}</span>
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Valid Receipts</p>
                <p className="text-lg font-semibold text-gray-900">{stats.valid_receipts}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Approved Requests */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">Approved Purchase Requests</h2>
        </div>

        {approvedRequests.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No approved requests found.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {approvedRequests.map((request) => (
              <div key={request.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-medium text-gray-900">{request.title}</h3>
                      {getStatusBadge(request.status)}
                    </div>
                    
                    <p className="text-gray-600 mb-3">{request.description}</p>
                    
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Amount:</span>
                        <span className="ml-2 font-medium">${request.amount}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Requested by:</span>
                        <span className="ml-2 font-medium">{request.created_by.full_name}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Approved:</span>
                        <span className="ml-2">{format(new Date(request.approved_at), 'MMM dd, yyyy')}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Approved by:</span>
                        <span className="ml-2 font-medium">{request.approved_by.full_name}</span>
                      </div>
                      {request.purchase_order && (
                        <div>
                          <span className="text-gray-500">PO Number:</span>
                          <span className="ml-2 font-medium">{request.purchase_order.po_number}</span>
                        </div>
                      )}
                    </div>

                    {/* Purchase Order Info */}
                    {request.purchase_order && (
                      <div className="mt-3 p-3 bg-blue-50 rounded-md">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-blue-900">
                              Purchase Order Generated
                            </p>
                            <p className="text-sm text-blue-700">
                              PO #{request.purchase_order.po_number} | 
                              Vendor: {request.purchase_order.vendor} | 
                              Total: ${request.purchase_order.total_amount}
                            </p>
                          </div>
                          {request.purchase_order.file && (
                            <a
                              href={request.purchase_order.file}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                            >
                              Download PO
                            </a>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Items preview */}
                    {request.items && request.items.length > 0 && (
                      <div className="mt-3">
                        <span className="text-gray-500 text-sm">Items:</span>
                        <div className="mt-1 space-y-1">
                          {request.items.slice(0, 3).map((item, index) => (
                            <div key={index} className="text-sm text-gray-600">
                              {item.name} (Qty: {item.quantity} × ${item.unit_price} = ${item.total_price})
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
                    
                    {/* Receipt validation */}
                    {request.purchase_order && (
                      <div>
                        <label 
                          htmlFor={`receipt-${request.purchase_order.id}`}
                          className="btn-primary text-sm cursor-pointer inline-block text-center"
                        >
                          {validationLoading === request.purchase_order.id ? 'Validating...' : 'Validate Receipt'}
                        </label>
                        <input
                          id={`receipt-${request.purchase_order.id}`}
                          type="file"
                          accept=".pdf,.png,.jpg,.jpeg"
                          onChange={(e) => handleReceiptValidation(request.purchase_order.id, e)}
                          disabled={validationLoading === request.purchase_order.id}
                          className="hidden"
                        />
                      </div>
                    )}
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

export default FinanceDashboard;