import axios from 'axios';
import { toast } from 'react-toastify';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    // Show error toast for non-401 errors
    if (error.response?.status !== 401) {
      const message = error.response?.data?.error || error.response?.data?.detail || 'An error occurred';
      toast.error(message);
    }
    
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login/', { email, password });
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },
  
  refresh: async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    const response = await api.post('/auth/refresh/', { refresh: refreshToken });
    return response.data;
  },
  
  getProfile: async () => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },
  
  updateProfile: async (userData) => {
    const response = await api.patch('/auth/profile/', userData);
    return response.data;
  },
};

// Purchase Request API calls
export const purchaseRequestAPI = {
  getMyRequests: async () => {
    const response = await api.get('/requests/');
    return response.data;
  },
  
  getPendingRequests: async () => {
    const response = await api.get('/requests/pending/');
    return response.data;
  },
  
  getRequest: async (id) => {
    const response = await api.get(`/requests/${id}/`);
    return response.data;
  },
  
  createRequest: async (requestData) => {
    // Check if requestData is FormData (contains file upload)
    if (requestData instanceof FormData) {
      const response = await api.post('/requests/', requestData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } else {
      // Regular JSON request
      const response = await api.post('/requests/', requestData);
      return response.data;
    }
  },
  
  updateRequest: async (id, requestData) => {
    const response = await api.patch(`/requests/${id}/`, requestData);
    return response.data;
  },
  
  approveRequest: async (id, decision, comments) => {
    const response = await api.patch(`/requests/${id}/approve/`, {
      decision,
      comments,
    });
    return response.data;
  },
  
  submitReceipt: async (id, receiptFile) => {
    const formData = new FormData();
    formData.append('receipt', receiptFile);
    
    const response = await api.post(`/requests/${id}/submit-receipt/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Finance API calls
export const financeAPI = {
  getApprovedRequests: async () => {
    const response = await api.get('/finance/requests/approved/');
    return response.data;
  },
  
  validateReceipt: async (purchaseOrderId, receiptFile) => {
    const formData = new FormData();
    formData.append('purchase_order_id', purchaseOrderId);
    formData.append('receipt_file', receiptFile);
    
    const response = await api.post('/finance/validate-receipt/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Purchase Order API calls
export const purchaseOrderAPI = {
  getPurchaseOrders: async () => {
    const response = await api.get('/purchase-orders/');
    return response.data;
  },
  
  getPurchaseOrder: async (id) => {
    const response = await api.get(`/purchase-orders/${id}/`);
    return response.data;
  },
};

// Dashboard API calls
export const dashboardAPI = {
  getUserStats: async () => {
    const response = await api.get('/dashboard/stats/');
    return response.data;
  },
};

export default api;