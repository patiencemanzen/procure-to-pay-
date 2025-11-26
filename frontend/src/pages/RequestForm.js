import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { purchaseRequestAPI } from '../services/api';
import { toast } from 'react-toastify';
import LoadingSpinner from '../components/UI/LoadingSpinner';

const RequestForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const isEditing = !!id;

  const {
    register,
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: {
      title: '',
      description: '',
      amount: '',
      proforma: null,
      items: [{ name: '', quantity: 1, unit_price: '' }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items',
  });

  const watchedItems = watch('items');

  const loadRequest = useCallback(async () => {
    setLoading(true);
    try {
      const request = await purchaseRequestAPI.getRequest(id);
      
      // Populate form with existing data
      setValue('title', request.title);
      setValue('description', request.description);
      setValue('amount', request.amount);
      
      if (request.items && request.items.length > 0) {
        setValue('items', request.items);
      }
    } catch (error) {
      console.error('Error loading request:', error);
      toast.error('Failed to load request');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  }, [id, setValue, navigate]);

  useEffect(() => {
    if (isEditing) {
      loadRequest();
    }
  }, [isEditing, loadRequest]);

  useEffect(() => {
    // Calculate total amount from items
    const total = watchedItems.reduce((sum, item) => {
      const quantity = parseFloat(item.quantity) || 0;
      const unitPrice = parseFloat(item.unit_price) || 0;
      return sum + (quantity * unitPrice);
    }, 0);
    setValue('amount', total.toFixed(2));
  }, [watchedItems, setValue]);

  const onSubmit = async (data) => {
    setSubmitting(true);
    try {
      let requestData;
      
      // Check if we have a file upload
      const hasFile = data.proforma && data.proforma[0];
      
      if (hasFile) {
        // Use FormData for file uploads
        const formData = new FormData();
        formData.append('title', data.title);
        formData.append('description', data.description);
        formData.append('amount', data.amount);
        formData.append('proforma', data.proforma[0]);
        
        // Append each item separately
        data.items.forEach((item, index) => {
          formData.append(`items[${index}]name`, item.name);
          formData.append(`items[${index}]quantity`, item.quantity);
          formData.append(`items[${index}]unit_price`, item.unit_price);
        });
        
        requestData = formData;
      } else {
        // Use regular JSON for requests without files
        requestData = {
          title: data.title,
          description: data.description,
          amount: data.amount,
          items: data.items
        };
      }

      if (isEditing) {
        await purchaseRequestAPI.updateRequest(id, requestData);
        toast.success('Request updated successfully!');
      } else {
        await purchaseRequestAPI.createRequest(requestData);
        toast.success('Request created successfully!');
      }
      
      navigate('/dashboard');
    } catch (error) {
      console.error('Error saving request:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading request..." />;
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {isEditing ? 'Edit Purchase Request' : 'Create New Purchase Request'}
          </h1>
          <p className="text-gray-600">
            Fill out the form below to {isEditing ? 'update your' : 'create a new'} purchase request.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="form-label">Title</label>
              <input
                type="text"
                {...register('title', { required: 'Title is required' })}
                className="form-input"
                placeholder="Enter request title"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
              )}
            </div>

            <div>
              <label className="form-label">Total Amount (RWF)</label>
              <input
                type="number"
                step="0.01"
                {...register('amount', { 
                  required: 'Amount is required',
                  min: { value: 0.01, message: 'Amount must be greater than 0' }
                })}
                className="form-input"
                placeholder="0.00"
                readOnly
              />
              <p className="mt-1 text-xs text-gray-500">
                Total is calculated automatically from items below
              </p>
              {errors.amount && (
                <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
              )}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="form-label">Description</label>
            <textarea
              {...register('description', { required: 'Description is required' })}
              rows={4}
              className="form-input"
              placeholder="Describe the purpose and details of this purchase request"
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
            )}
          </div>

          {/* Proforma Invoice */}
          <div>
            <label className="form-label">Proforma Invoice (Optional)</label>
            <input
              type="file"
              {...register('proforma')}
              accept=".pdf,.png,.jpg,.jpeg"
              className="form-input"
            />
            <p className="mt-1 text-xs text-gray-500">
              Upload a proforma invoice or quote (PDF, PNG, JPG)
            </p>
          </div>

          {/* Items */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <label className="form-label">Items</label>
              <button
                type="button"
                onClick={() => append({ name: '', quantity: 1, unit_price: '' })}
                className="btn-primary text-sm"
              >
                Add Item
              </button>
            </div>

            <div className="space-y-4">
              {fields.map((field, index) => (
                <div key={field.id} className="flex items-end space-x-4 p-4 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <label className="form-label">Item Name</label>
                    <input
                      type="text"
                      {...register(`items.${index}.name`, { required: 'Item name is required' })}
                      className="form-input"
                      placeholder="Enter item name"
                    />
                    {errors.items?.[index]?.name && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.items[index].name.message}
                      </p>
                    )}
                  </div>

                  <div className="w-24">
                    <label className="form-label">Quantity</label>
                    <input
                      type="number"
                      min="1"
                      {...register(`items.${index}.quantity`, { 
                        required: 'Quantity is required',
                        min: { value: 1, message: 'Minimum quantity is 1' }
                      })}
                      className="form-input"
                      placeholder="1"
                    />
                    {errors.items?.[index]?.quantity && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.items[index].quantity.message}
                      </p>
                    )}
                  </div>

                  <div className="w-32">
                    <label className="form-label">Unit Price (RWF)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      {...register(`items.${index}.unit_price`, { 
                        required: 'Unit price is required',
                        min: { value: 0.01, message: 'Price must be greater than 0' }
                      })}
                      className="form-input"
                      placeholder="0.00"
                    />
                    {errors.items?.[index]?.unit_price && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.items[index].unit_price.message}
                      </p>
                    )}
                  </div>

                  <div className="w-32">
                    <label className="form-label">Total (RWF)</label>
                    <input
                      type="text"
                      value={
                        watchedItems[index]
                          ? `RWF ${((watchedItems[index].quantity || 0) * (watchedItems[index].unit_price || 0)).toLocaleString()}`
                          : 'RWF 0'
                      }
                      className="form-input bg-gray-50"
                      readOnly
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => remove(index)}
                    disabled={fields.length === 1}
                    className="btn-danger text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="btn-secondary"
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={submitting}
            >
              {submitting ? (
                <div className="flex items-center">
                  <div className="spinner mr-2"></div>
                  {isEditing ? 'Updating...' : 'Creating...'}
                </div>
              ) : (
                isEditing ? 'Update Request' : 'Create Request'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RequestForm;