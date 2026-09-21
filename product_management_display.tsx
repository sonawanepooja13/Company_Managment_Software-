/**
 * Modular Product Management and Display Feature
 * 
 * Components:
 * 1. AdminEntryForm - Dashboard form for adding/editing products
 * 2. CustomerProductPage - Public-facing showcase page
 * 
 * Stack: React + Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { 
  // Icons
  Upload, X, Download, Play, AlertTriangle, Shield, 
  FileText, Image as ImageIcon, ChevronLeft, ChevronRight,
  Plus, Trash2, Save, Eye, ShoppingCart, Package, Settings,
  CheckCircle, AlertCircle, File, Video, Info, ExternalLink
} from 'lucide-react';

// ============================================
// TYPES
// ============================================

interface Product {
  id: string;
  title: string;
  sku: string;
  category: string;
  price: number;
  currency: string;
  stockStatus: 'in_stock' | 'out_of_stock' | 'low_stock';
  stockQty: number;
  minOrderQty: number;
  description: string;
  images: string[];
  featureVideo: string;
  operationVideo: string;
  datasheet: string;
  userManual: string;
  specifications: Specification[];
  warranty: string;
  precautions: string;
  certifications: string[];
  createdAt: string;
  updatedAt: string;
}

interface Specification {
  id: string;
  key: string;
  value: string;
}

// ============================================
// ADMIN ENTRY FORM COMPONENT
// ============================================

interface AdminEntryFormProps {
  product?: Product;
  onSave: (product: Product) => void;
  onCancel: () => void;
}

function AdminEntryForm({ product, onSave, onCancel }: AdminEntryFormProps) {
  const [activeTab, setActiveTab] = useState<'general' | 'media' | 'specs' | 'safety'>('general');
  const [formData, setFormData] = useState<Partial<Product>>({
    title: '',
    sku: '',
    category: '',
    price: 0,
    currency: 'INR',
    stockStatus: 'in_stock',
    stockQty: 0,
    minOrderQty: 1,
    description: '',
    images: [],
    featureVideo: '',
    operationVideo: '',
    datasheet: '',
    userManual: '',
    specifications: [],
    warranty: '',
    precautions: '',
    certifications: []
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  const categories = [
    'Industrial Automation',
    'PLC Controllers',
    'Sensors & Transmitters',
    'Motor Drives & VFDs',
    'Switchgear & Protection',
    'Cables & Wires',
    'Control Panels',
    'Instruments & Meters',
    'Other'
  ];

  const availableCertifications = [
    'CE', 'RoHS', 'ISO 9001', 'UL', 'CSA', 'FCC', 'TUV', 'IP65', 'IP67'
  ];

  useEffect(() => {
    if (product) {
      setFormData(product);
    }
  }, [product]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.title?.trim()) {
      newErrors.title = 'Title is required';
    }
    if (!formData.sku?.trim()) {
      newErrors.sku = 'SKU is required';
    }
    if (!formData.category?.trim()) {
      newErrors.category = 'Category is required';
    }
    if (!formData.price || formData.price <= 0) {
      newErrors.price = 'Price must be greater than 0';
    }
    if (!formData.stockQty || formData.stockQty < 0) {
      newErrors.stockQty = 'Stock quantity must be 0 or greater';
    }
    if (!formData.minOrderQty || formData.minOrderQty < 1) {
      newErrors.minOrderQty = 'Minimum order quantity must be at least 1';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validateForm()) {
      setIsSaving(true);
      const productToSave: Product = {
        id: formData.id || `prod_${Date.now()}`,
        title: formData.title!,
        sku: formData.sku!,
        category: formData.category!,
        price: formData.price!,
        currency: formData.currency || 'INR',
        stockStatus: formData.stockStatus || 'in_stock',
        stockQty: formData.stockQty!,
        minOrderQty: formData.minOrderQty!,
        description: formData.description || '',
        images: formData.images || [],
        featureVideo: formData.featureVideo || '',
        operationVideo: formData.operationVideo || '',
        datasheet: formData.datasheet || '',
        userManual: formData.userManual || '',
        specifications: formData.specifications || [],
        warranty: formData.warranty || '',
        precautions: formData.precautions || '',
        certifications: formData.certifications || [],
        createdAt: formData.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      setTimeout(() => {
        onSave(productToSave);
        setIsSaving(false);
      }, 500);
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const newImages = Array.from(files).map(file => URL.createObjectURL(file));
      setFormData(prev => ({
        ...prev,
        images: [...(prev.images || []), ...newImages]
      }));
    }
  };

  const handleRemoveImage = (index: number) => {
    setFormData(prev => ({
      ...prev,
      images: prev.images?.filter((_, i) => i !== index) || []
    }));
  };

  const handleAddSpecification = () => {
    setFormData(prev => ({
      ...prev,
      specifications: [
        ...(prev.specifications || []),
        { id: `spec_${Date.now()}`, key: '', value: '' }
      ]
    }));
  };

  const handleSpecificationChange = (id: string, field: 'key' | 'value', value: string) => {
    setFormData(prev => ({
      ...prev,
      specifications: prev.specifications?.map(spec =>
        spec.id === id ? { ...spec, [field]: value } : spec
      ) || []
    }));
  };

  const handleRemoveSpecification = (id: string) => {
    setFormData(prev => ({
      ...prev,
      specifications: prev.specifications?.filter(spec => spec.id !== id) || []
    }));
  };

  const handleCertificationToggle = (cert: string) => {
    setFormData(prev => ({
      ...prev,
      certifications: prev.certifications?.includes(cert)
        ? prev.certifications.filter(c => c !== cert)
        : [...(prev.certifications || []), cert]
    }));
  };

  const handleFileUpload = (field: 'datasheet' | 'userManual', e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData(prev => ({
        ...prev,
        [field]: file.name
      }));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Settings className="w-6 h-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">
              {product ? 'Edit Product' : 'Add New Product'}
            </h1>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
            >
              <Save className="w-4 h-4 mr-2" />
              {isSaving ? 'Saving...' : 'Save Product'}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow-sm">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'general', label: 'General Info', icon: Package },
                { id: 'media', label: 'Media & Docs', icon: ImageIcon },
                { id: 'specs', label: 'Technical Specs', icon: FileText },
                { id: 'safety', label: 'Safety & Precautions', icon: Shield }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'general' && (
              <GeneralInfoTab formData={formData} setFormData={setFormData} errors={errors} categories={categories} />
            )}
            {activeTab === 'media' && (
              <MediaDocsTab 
                formData={formData} 
                setFormData={setFormData} 
                onImageUpload={handleImageUpload}
                onRemoveImage={handleRemoveImage}
                onFileUpload={handleFileUpload}
              />
            )}
            {activeTab === 'specs' && (
              <TechnicalSpecsTab 
                formData={formData} 
                setFormData={setFormData}
                onAddSpec={handleAddSpecification}
                onSpecChange={handleSpecificationChange}
                onRemoveSpec={handleRemoveSpecification}
              />
            )}
            {activeTab === 'safety' && (
              <SafetyPrecautionsTab 
                formData={formData} 
                setFormData={setFormData}
                certifications={availableCertifications}
                onCertToggle={handleCertificationToggle}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================
// GENERAL INFO TAB COMPONENT
// ============================================

function GeneralInfoTab({ 
  formData, 
  setFormData, 
  errors, 
  categories 
}: { 
  formData: Partial<Product>;
  setFormData: React.Dispatch<React.SetStateAction<Partial<Product>>>;
  errors: Record<string, string>;
  categories: string[];
}) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Title */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Title / Model Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.title || ''}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="e.g., ESP32 Industrial Automation Controller"
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.title ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.title && <p className="text-sm text-red-600 mt-1">{errors.title}</p>}
        </div>

        {/* SKU */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            SKU / Part Number <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.sku || ''}
            onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
            placeholder="e.g., SEC-PLC-04"
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.sku ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.sku && <p className="text-sm text-red-600 mt-1">{errors.sku}</p>}
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category / Subsystem <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.category || ''}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.category ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Select category</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          {errors.category && <p className="text-sm text-red-600 mt-1">{errors.category}</p>}
        </div>

        {/* Price */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pricing <span className="text-red-500">*</span>
          </label>
          <div className="flex">
            <select
              value={formData.currency || 'INR'}
              onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
              className="px-4 py-2 border border-r-0 border-gray-300 rounded-l-lg bg-gray-50"
            >
              <option value="INR">₹ INR</option>
              <option value="USD">$ USD</option>
              <option value="EUR">€ EUR</option>
            </select>
            <input
              type="number"
              value={formData.price || ''}
              onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
              placeholder="0.00"
              min="0"
              step="0.01"
              className={`flex-1 px-4 py-2 border rounded-r-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.price ? 'border-red-500' : 'border-gray-300'
              }`}
            />
          </div>
          {errors.price && <p className="text-sm text-red-600 mt-1">{errors.price}</p>}
        </div>

        {/* Stock Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Stock Status</label>
          <select
            value={formData.stockStatus || 'in_stock'}
            onChange={(e) => setFormData({ ...formData, stockStatus: e.target.value as any })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="in_stock">In Stock</option>
            <option value="low_stock">Low Stock</option>
            <option value="out_of_stock">Out of Stock</option>
          </select>
        </div>

        {/* Stock Qty */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Stock Quantity <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.stockQty || ''}
            onChange={(e) => setFormData({ ...formData, stockQty: parseInt(e.target.value) || 0 })}
            min="0"
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.stockQty ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.stockQty && <p className="text-sm text-red-600 mt-1">{errors.stockQty}</p>}
        </div>

        {/* MOQ */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Order Quantity (MOQ) <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.minOrderQty || ''}
            onChange={(e) => setFormData({ ...formData, minOrderQty: parseInt(e.target.value) || 1 })}
            min="1"
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.minOrderQty ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.minOrderQty && <p className="text-sm text-red-600 mt-1">{errors.minOrderQty}</p>}
        </div>

        {/* Description */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
          <textarea
            value={formData.description || ''}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={4}
            placeholder="Detailed product description..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          />
        </div>
      </div>
    </div>
  );
}

// ============================================
// MEDIA & DOCS TAB COMPONENT
// ============================================

function MediaDocsTab({ 
  formData, 
  setFormData, 
  onImageUpload, 
  onRemoveImage,
  onFileUpload 
}: { 
  formData: Partial<Product>;
  setFormData: React.Dispatch<React.SetStateAction<Partial<Product>>>;
  onImageUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveImage: (index: number) => void;
  onFileUpload: (field: 'datasheet' | 'userManual', e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="space-y-8">
      {/* Product Photos */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Product Photos <span className="text-gray-500">(5-8 images recommended)</span>
        </label>
        
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={onImageUpload}
            className="hidden"
            id="image-upload"
          />
          <label htmlFor="image-upload" className="cursor-pointer">
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-600 mb-1">
              Drag & drop images here, or click to select
            </p>
            <p className="text-xs text-gray-500">
              Supports: JPG, PNG, GIF, WebP (Max 5MB each)
            </p>
          </label>
        </div>

        {/* Image Preview */}
        {formData.images && formData.images.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {formData.images.map((image, index) => (
              <div key={index} className="relative group">
                <img
                  src={image}
                  alt={`Product ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg border border-gray-200"
                />
                <button
                  onClick={() => onRemoveImage(index)}
                  className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Feature Video */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Feature / Promotional Video</label>
        <div className="flex space-x-2">
          <input
            type="url"
            value={formData.featureVideo || ''}
            onChange={(e) => setFormData({ ...formData, featureVideo: e.target.value })}
            placeholder="https://www.youtube.com/watch?v=..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {formData.featureVideo && (
            <a
              href={formData.featureVideo}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center"
            >
              <Play className="w-4 h-4 mr-2" />
              Preview
            </a>
          )}
        </div>
      </div>

      {/* Operation Video */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Operation / Wiring / Setup Video</label>
        <div className="flex space-x-2">
          <input
            type="url"
            value={formData.operationVideo || ''}
            onChange={(e) => setFormData({ ...formData, operationVideo: e.target.value })}
            placeholder="https://www.youtube.com/watch?v=..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {formData.operationVideo && (
            <a
              href={formData.operationVideo}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center"
            >
              <Play className="w-4 h-4 mr-2" />
              Preview
            </a>
          )}
        </div>
      </div>

      {/* Datasheet */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Technical Datasheet (PDF)</label>
        <div className="flex items-center space-x-4">
          <label className="flex-1 flex items-center px-4 py-3 border border-gray-300 rounded-lg hover:border-blue-400 cursor-pointer">
            <File className="w-5 h-5 text-gray-400 mr-3" />
            <span className="text-sm text-gray-600">
              {formData.datasheet || 'No file selected'}
            </span>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => onFileUpload('datasheet', e)}
              className="hidden"
              id="datasheet-upload"
            />
          </label>
          <label htmlFor="datasheet-upload" className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg cursor-pointer">
            Choose File
          </label>
        </div>
      </div>

      {/* User Manual */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">User Manual / Installation Guide (PDF)</label>
        <div className="flex items-center space-x-4">
          <label className="flex-1 flex items-center px-4 py-3 border border-gray-300 rounded-lg hover:border-blue-400 cursor-pointer">
            <File className="w-5 h-5 text-gray-400 mr-3" />
            <span className="text-sm text-gray-600">
              {formData.userManual || 'No file selected'}
            </span>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => onFileUpload('userManual', e)}
              className="hidden"
              id="manual-upload"
            />
          </label>
          <label htmlFor="manual-upload" className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg cursor-pointer">
            Choose File
          </label>
        </div>
      </div>
    </div>
  );
}

// ============================================
// TECHNICAL SPECS TAB COMPONENT
// ============================================

function TechnicalSpecsTab({ 
  formData, 
  setFormData, 
  onAddSpec, 
  onSpecChange, 
  onRemoveSpec 
}: { 
  formData: Partial<Product>;
  setFormData: React.Dispatch<React.SetStateAction<Partial<Product>>>;
  onAddSpec: () => void;
  onSpecChange: (id: string, field: 'key' | 'value', value: string) => void;
  onRemoveSpec: (id: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Technical Specifications</h3>
        <button
          onClick={onAddSpec}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Specification
        </button>
      </div>

      {/* Specifications Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 w-1/3">Parameter</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 w-1/2">Value</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700 w-20">Action</th>
            </tr>
          </thead>
          <tbody>
            {formData.specifications && formData.specifications.length > 0 ? (
              formData.specifications.map((spec) => (
                <tr key={spec.id} className="border-t border-gray-200">
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      value={spec.key}
                      onChange={(e) => onSpecChange(spec.id, 'key', e.target.value)}
                      placeholder="e.g., Operating Voltage"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      value={spec.value}
                      onChange={(e) => onSpecChange(spec.id, 'value', e.target.value)}
                      placeholder="e.g., 220V AC"
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => onRemoveSpec(spec.id)}
                      className="p-1 text-red-500 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-gray-500">
                  No specifications added. Click "Add Specification" to add.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Common Specs Suggestions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800 font-medium mb-2">Common specifications to consider:</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm text-blue-700">
          <span>• Operating Voltage / Power Rating</span>
          <span>• Communication Protocol / Interface</span>
          <span>• Enclosure / IP Rating</span>
          <span>• Dimensions / Weight</span>
          <span>• Temperature Range</span>
          <span>• Certification Standards</span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// SAFETY & PRECAUTIONS TAB COMPONENT
// ============================================

function SafetyPrecautionsTab({ 
  formData, 
  setFormData, 
  certifications, 
  onCertToggle 
}: { 
  formData: Partial<Product>;
  setFormData: React.Dispatch<React.SetStateAction<Partial<Product>>>;
  certifications: string[];
  onCertToggle: (cert: string) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Warranty */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Warranty Duration & Terms</label>
        <textarea
          value={formData.warranty || ''}
          onChange={(e) => setFormData({ ...formData, warranty: e.target.value })}
          rows={3}
          placeholder="e.g., 12 Months Replacement Warranty against manufacturing defects"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
        />
      </div>

      {/* Precautions */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Critical Operating Precautions / Hazard Warnings
        </label>
        <div className="relative">
          <AlertTriangle className="absolute left-3 top-3 w-5 h-5 text-amber-500" />
          <textarea
            value={formData.precautions || ''}
            onChange={(e) => setFormData({ ...formData, precautions: e.target.value })}
            rows={4}
            placeholder="e.g., Check input polarity before powering. Max 24V DC. Ensure proper grounding."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          />
        </div>
      </div>

      {/* Certifications */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Regulatory Certifications</label>
        <div className="flex flex-wrap gap-3">
          {certifications.map((cert) => (
            <button
              key={cert}
              onClick={() => onCertToggle(cert)}
              className={`px-4 py-2 rounded-lg border-2 flex items-center transition-colors ${
                formData.certifications?.includes(cert)
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-300 text-gray-600 hover:border-gray-400'
              }`}
            >
              {formData.certifications?.includes(cert) && <CheckCircle className="w-4 h-4 mr-2" />}
              {cert}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================
// CUSTOMER PRODUCT PAGE COMPONENT
// ============================================

interface CustomerProductPageProps {
  product: Product;
  onBuyNow: (product: Product) => void;
  onInquire: (product: Product) => void;
}

function CustomerProductPage({ product, onBuyNow, onInquire }: CustomerProductPageProps) {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [activeMediaTab, setActiveMediaTab] = useState<'specs' | 'feature' | 'operation' | 'warranty'>('specs');
  const [quantity, setQuantity] = useState(product.minOrderQty);

  const nextImage = () => {
    setCurrentImageIndex((prev) => (prev + 1) % (product.images.length || 1));
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => (prev - 1 + (product.images.length || 1)) % (product.images.length || 1));
  };

  const getStockStatusColor = () => {
    switch (product.stockStatus) {
      case 'in_stock': return 'text-green-600 bg-green-50';
      case 'low_stock': return 'text-amber-600 bg-amber-50';
      case 'out_of_stock': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStockStatusText = () => {
    switch (product.stockStatus) {
      case 'in_stock': return 'In Stock';
      case 'low_stock': return 'Low Stock';
      case 'out_of_stock': return 'Out of Stock';
      default: return 'Unknown';
    }
  };

  const embedYouTubeVideo = (url: string) => {
    const videoId = url.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|([^\/?&]*)(?=[?&]|$)|([^\/?&]*)(?=[?&]|$)|watch\?v=)?([^&]+)?/)?.[1];
    if (videoId) {
      return `https://www.youtube.com/embed/${videoId}`;
    }
    return url;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center">
          <button className="flex items-center text-gray-600 hover:text-gray-900">
            <ChevronLeft className="w-5 h-5 mr-2" />
            Back to Products
          </button>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Left: Image Gallery */}
          <div className="space-y-4">
            <div className="bg-white rounded-lg shadow-sm overflow-hidden">
              <div className="relative aspect-video bg-gray-100">
                {product.images && product.images.length > 0 ? (
                  <img
                    src={product.images[currentImageIndex]}
                    alt={product.title}
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <ImageIcon className="w-16 h-16 text-gray-300" />
                  </div>
                )}
              </div>

              {/* Thumbnail Navigation */}
              {product.images && product.images.length > 1 && (
                <div className="flex items-center justify-between p-4 border-t border-gray-200">
                  <button
                    onClick={prevImage}
                    className="p-2 hover:bg-gray-100 rounded-full disabled:opacity-50"
                    disabled={currentImageIndex === 0}
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="text-sm text-gray-600">
                    {currentImageIndex + 1} / {product.images.length}
                  </span>
                  <button
                    onClick={nextImage}
                    className="p-2 hover:bg-gray-100 rounded-full disabled:opacity-50"
                    disabled={currentImageIndex === product.images.length - 1}
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>

            {/* Thumbnail Strip */}
            {product.images && product.images.length > 1 && (
              <div className="flex space-x-2 overflow-x-auto pb-2">
                {product.images.map((image, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentImageIndex(index)}
                    className={`flex-shrink-0 relative rounded-lg overflow-hidden border-2 transition-all ${
                      currentImageIndex === index
                        ? 'border-blue-500 ring-2 ring-blue-200'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <img
                      src={image}
                      alt={`Thumbnail ${index + 1}`}
                      className="w-20 h-20 object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Right: Product Info */}
          <div className="space-y-6">
            {/* Title */}
            <h1 className="text-3xl font-bold text-gray-900">{product.title}</h1>

            {/* SKU Badge */}
            <div className="flex items-center space-x-3">
              <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-medium">
                SKU: {product.sku}
              </span>
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                {product.category}
              </span>
            </div>

            {/* Stock Status */}
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStockStatusColor()}`}>
              {getStockStatusText()}
            </div>

            {/* Price */}
            <div className="border-t border-gray-200 pt-4">
              <div className="flex items-baseline">
                <span className="text-4xl font-bold text-gray-900">
                  {product.currency === 'INR' ? '₹' : '$'}
                  {product.price.toLocaleString()}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Stock: {product.stockQty} units
              </p>
            </div>

            {/* MOQ */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Minimum Order Quantity:</span>
                <span className="text-lg font-semibold text-gray-900">{product.minOrderQty} units</span>
              </div>
            </div>

            {/* Quantity Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Quantity</label>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setQuantity(Math.max(product.minOrderQty, quantity - 1))}
                  className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  disabled={quantity <= product.minOrderQty}
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(product.minOrderQty, parseInt(e.target.value) || product.minOrderQty))}
                  min={product.minOrderQty}
                  className="w-24 px-4 py-2 border border-gray-300 rounded-lg text-center font-medium"
                />
                <button
                  onClick={() => setQuantity(quantity + 1)}
                  className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Datasheet Download */}
            {product.datasheet && (
              <button className="w-full flex items-center justify-center px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg border border-gray-300 transition-colors">
                <File className="w-5 h-5 text-gray-600 mr-2" />
                <Download className="w-5 h-5 text-gray-600 mr-2" />
                <span className="font-medium text-gray-700">Download Datasheet (PDF)</span>
              </button>
            )}

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <button
                onClick={() => onBuyNow(product)}
                disabled={product.stockStatus === 'out_of_stock'}
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center font-semibold"
              >
                <ShoppingCart className="w-5 h-5 mr-2" />
                Buy Now
              </button>
              <button
                onClick={() => onInquire(product)}
                className="flex-1 px-6 py-3 border-2 border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 flex items-center justify-center font-semibold"
              >
                Inquire Now
              </button>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Description</h2>
          <p className="text-gray-700 leading-relaxed">{product.description}</p>
        </div>

        {/* Safety Precaution Alert */}
        {product.precautions && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-8">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-amber-800 mb-2">Safety Precautions</h3>
                <p className="text-amber-900 leading-relaxed">{product.precautions}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tabbed Media Hub */}
        <div className="bg-white rounded-lg shadow-sm">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'specs', label: 'Features & Specs', icon: FileText },
                { id: 'feature', label: 'Feature Video', icon: Video },
                { id: 'operation', label: 'Operation / Setup Video', icon: Video },
                { id: 'warranty', label: 'Warranty & Compliance', icon: Shield }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveMediaTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 transition-colors ${
                    activeMediaTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeMediaTab === 'specs' && (
              <SpecsContent specifications={product.specifications} />
            )}
            {activeMediaTab === 'feature' && (
              <VideoContent videoUrl={product.featureVideo} title="Feature Video" />
            )}
            {activeMediaTab === 'operation' && (
              <VideoContent videoUrl={product.operationVideo} title="Operation / Setup Video" />
            )}
            {activeMediaTab === 'warranty' && (
              <WarrantyContent 
                warranty={product.warranty} 
                certifications={product.certifications} 
              userManual={product.userManual}
              datasheet={product.datasheet}
              onDownload={(file) => console.log('Download:', file)}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ============================================
// SPECS CONTENT COMPONENT
// ============================================

function SpecsContent({ specifications }: { specifications: Specification[] }) {
  return (
    <div>
      {specifications && specifications.length > 0 ? (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 w-1/3">Parameter</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700 w-2/3">Value</th>
              </tr>
            </thead>
            <tbody>
              {specifications.map((spec) => (
                <tr key={spec.id} className="border-t border-gray-200">
                  <td className="px-4 py-3 text-sm text-gray-900 font-medium">{spec.key}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{spec.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          No specifications available.
        </div>
      )}
    </div>
  );
}

// ============================================
// VIDEO CONTENT COMPONENT
// ============================================

function VideoContent({ videoUrl, title }: { videoUrl: string; title: string }) {
  if (!videoUrl) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Video className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No video available.</p>
      </div>
    );
  }

  const embedUrl = videoUrl.includes('youtube') || videoUrl.includes('youtu.be')
    ? embedYouTubeVideo(videoUrl)
    : videoUrl;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
        <iframe
          src={embedUrl}
          className="w-full h-full"
          allowFullScreen
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        />
      </div>
      <a
        href={videoUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center text-blue-600 hover:text-blue-700"
      >
        <ExternalLink className="w-4 h-4 mr-2" />
        Open in new tab
      </a>
    </div>
  );
}

// ============================================
// WARRANTY CONTENT COMPONENT
// ============================================

function WarrantyContent({ 
  warranty, 
  certifications, 
  userManual, 
  datasheet,
  onDownload 
}: { 
  warranty: string;
  certifications: string[];
  userManual: string;
  datasheet: string;
  onDownload: (file: string) => void;
}) {
  return (
    <div className="space-y-6">
      {/* Warranty */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Warranty</h3>
        <p className="text-gray-700 leading-relaxed bg-gray-50 rounded-lg p-4">
          {warranty || 'No warranty information available.'}
        </p>
      </div>

      {/* Certifications */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Certifications</h3>
        {certifications && certifications.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {certifications.map((cert) => (
              <span key={cert} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                <CheckCircle className="w-4 h-4 mr-1 inline" />
                {cert}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No certifications listed.</p>
        )}
      </div>

      {/* Documents */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Documents</h3>
        <div className="space-y-3">
          {datasheet && (
            <button
              onClick={() => onDownload(datasheet)}
              className="w-full flex items-center justify-between px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg border border-gray-300 transition-colors"
            >
              <div className="flex items-center">
                <File className="w-5 h-5 text-gray-600 mr-3" />
                <span className="font-medium text-gray-700">Datasheet (PDF)</span>
              </div>
              <Download className="w-5 h-5 text-gray-600" />
            </button>
          )}
          {userManual && (
            <button
              onClick={() => onDownload(userManual)}
              className="w-full flex items-center justify-between px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg border border-gray-300 transition-colors"
            >
              <div className="flex items-center">
                <File className="w-5 h-5 text-gray-600 mr-3" />
                <span className="font-medium text-gray-700">User Manual (PDF)</span>
              </div>
              <Download className="w-5 h-5 text-gray-600" />
            </button>
          )}
          {!datasheet && !userManual && (
            <p className="text-gray-500">No documents available.</p>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================
// EXPORT COMPONENTS
// ============================================

export { AdminEntryForm, CustomerProductPage };
export type { Product, Specification };