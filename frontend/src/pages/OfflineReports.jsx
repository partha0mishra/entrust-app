import React, { useState, useEffect } from 'react';
import { reportAPI } from '../api';
import Breadcrumb from '../components/Breadcrumb';

// Dimension descriptions
const DIMENSION_INFO = {
  'Data Privacy & Compliance': {
    description: 'Ensures personal and sensitive data is protected in accordance with legal and regulatory requirements.',
    color: 'blue'
  },
  'Data Ethics & Bias': {
    description: 'Addresses fairness, transparency, and potential biases in data usage and decision-making processes.',
    color: 'purple'
  },
  'Data Lineage & Traceability': {
    description: 'Tracks the flow and transformation of data from origin to destination across systems.',
    color: 'green'
  },
  'Value & Lifecycle': {
    description: 'Assesses data value, relevance, and management throughout its entire lifecycle.',
    color: 'yellow'
  },
  'Governance & Management': {
    description: 'Establishes policies, roles, and accountability for data stewardship and decision-making.',
    color: 'red'
  },
  'Security & Access': {
    description: 'Protects data from unauthorized access, breaches, and cyber threats.',
    color: 'indigo'
  },
  'Metadata & Documentation': {
    description: 'Provides comprehensive information about data structure, meaning, and context.',
    color: 'pink'
  },
  'Quality': {
    description: 'Ensures data accuracy, completeness, consistency, and fitness for intended use.',
    color: 'teal'
  },
  'Overall': {
    description: 'Comprehensive analysis across all data trust dimensions.',
    color: 'gray'
  }
};

const OfflineReports = () => {
  const [user, setUser] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerId, setCustomerId] = useState(null);
  const [customerCode, setCustomerCode] = useState(null);
  const [dimensions, setDimensions] = useState([]);
  const [availability, setAvailability] = useState({});
  const [folderInfo, setFolderInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generatingAll, setGeneratingAll] = useState(false);
  const [dimensionProgress, setDimensionProgress] = useState({});
  const [viewingDimension, setViewingDimension] = useState(null);
  const [viewingReport, setViewingReport] = useState(null);

  useEffect(() => {
    const userData = JSON.parse(localStorage.getItem('user'));
    setUser(userData);

    if (userData?.role === 'Sales' || userData?.role === 'CXO') {
      if (userData.role === 'Sales') {
        // Sales user - load their customer
        setCustomerId(userData.customer_id);
        setCustomerCode(userData.customer_code);
        loadReportAvailability(userData.customer_id);
      } else {
        // CXO - load all customers
        loadCustomers();
      }
    } else {
      setError('Only CXO and Sales users can access offline report generation.');
      setLoading(false);
    }
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await reportAPI.getCustomers();
      const customersList = response.data || [];
      setCustomers(customersList);

      if (customersList.length > 0) {
        const firstCustomer = customersList[0];
        setSelectedCustomer(firstCustomer);
        setCustomerId(firstCustomer.customer_id);
        setCustomerCode(firstCustomer.customer_code);
        await loadReportAvailability(firstCustomer.customer_id);
      }
      setLoading(false);
    } catch (err) {
      console.error('Error loading customers:', err);
      setError('Failed to load customers');
      setLoading(false);
    }
  };

  const loadReportAvailability = async (custId) => {
    try {
      setLoading(true);
      const response = await reportAPI.checkReportsAvailability(custId);
      const data = response.data;

      setAvailability(data.availability || {});
      setFolderInfo({
        exists: data.folder_path_exists,
        path: data.reports_base_path,
        customerCode: data.customer_code,
        customerName: data.customer_name
      });

      // Get dimensions from availability
      const dims = Object.keys(data.availability || {});
      setDimensions(dims);

      setLoading(false);
    } catch (err) {
      console.error('Error loading report availability:', err);
      setError('Failed to load report availability');
      setLoading(false);
    }
  };

  const handleCustomerChange = async (e) => {
    const custId = parseInt(e.target.value);
    const customer = customers.find(c => c.customer_id === custId);
    setSelectedCustomer(customer);
    setCustomerId(custId);
    setCustomerCode(customer?.customer_code);
    await loadReportAvailability(custId);
  };

  const generateDimensionReport = async (dimension) => {
    try {
      // Update progress
      setDimensionProgress(prev => ({
        ...prev,
        [dimension]: { status: 'generating', progress: 0 }
      }));

      // Call the existing report generation endpoint with force_regenerate=true
      let response;
      if (dimension === 'Overall') {
        response = await reportAPI.getOverallReport(customerId, true);
      } else {
        response = await reportAPI.getDimensionReport(customerId, dimension, true);
      }

      // Mark as completed
      setDimensionProgress(prev => ({
        ...prev,
        [dimension]: { status: 'completed', progress: 100 }
      }));

      // Reload availability to update View button
      await loadReportAvailability(customerId);

    } catch (err) {
      console.error(`Error generating report for ${dimension}:`, err);
      setDimensionProgress(prev => ({
        ...prev,
        [dimension]: { status: 'error', progress: 0, error: err.message }
      }));
    }
  };

  const generateAllReports = async () => {
    setGeneratingAll(true);

    // Generate dimensional reports first
    const dimensionalReports = dimensions.filter(d => d !== 'Overall');

    for (const dimension of dimensionalReports) {
      await generateDimensionReport(dimension);
    }

    // Generate overall report last
    if (dimensions.includes('Overall')) {
      await generateDimensionReport('Overall');
    }

    setGeneratingAll(false);
  };

  const viewReport = async (dimension) => {
    try {
      setViewingDimension(dimension);
      const response = await reportAPI.getHtmlReport(customerId, dimension);
      setViewingReport(response.data);
    } catch (err) {
      console.error(`Error viewing report for ${dimension}:`, err);
      alert(`Failed to load report: ${err.response?.data?.detail || err.message}`);
    }
  };

  const closeReportView = () => {
    setViewingDimension(null);
    setViewingReport(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-encora-green mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <div className="flex items-center mb-2">
            <svg className="w-6 h-6 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-semibold text-red-800">Access Denied</h3>
          </div>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  // If viewing a report, show it
  if (viewingReport && viewingDimension) {
    return (
      <div className="fixed inset-0 bg-white z-50 overflow-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm z-10">
          <h2 className="text-xl font-bold text-gray-800">{viewingDimension} Report</h2>
          <button
            onClick={closeReportView}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span>Close</span>
          </button>
        </div>
        <div dangerouslySetInnerHTML={{ __html: viewingReport }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Breadcrumb items={[{ label: 'Offline Reports', path: '/offline-reports' }]} />

      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold mb-2">Offline Report Generation</h1>
        <p className="text-gray-600 mb-6">
          Generate and save reports locally for offline access. Reports will be saved in Markdown, JSON, and HTML formats.
        </p>

        {/* Customer Selector for CXO */}
        {user?.role === 'CXO' && customers.length > 0 && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Customer
            </label>
            <select
              value={customerId || ''}
              onChange={handleCustomerChange}
              className="w-full md:w-96 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-encora-green focus:border-encora-green"
            >
              {customers.map((customer) => (
                <option key={customer.customer_id} value={customer.customer_id}>
                  {customer.customer_name} ({customer.customer_code})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Folder Information */}
        {folderInfo && (
          <div className={`mb-6 p-4 rounded-lg border-2 ${folderInfo.exists ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
            <div className="flex items-start">
              <svg className={`w-6 h-6 mr-2 mt-0.5 ${folderInfo.exists ? 'text-green-600' : 'text-yellow-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={folderInfo.exists ? "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" : "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"} />
              </svg>
              <div className="flex-1">
                <h3 className={`font-semibold ${folderInfo.exists ? 'text-green-800' : 'text-yellow-800'}`}>
                  {folderInfo.exists ? 'Reports Folder Ready' : 'Reports Folder Not Found'}
                </h3>
                <p className={`text-sm mt-1 ${folderInfo.exists ? 'text-green-700' : 'text-yellow-700'}`}>
                  {folderInfo.exists ? (
                    <>
                      Reports will be saved to: <code className="bg-white px-2 py-0.5 rounded font-mono text-xs">{folderInfo.path}</code>
                      <br />
                      <span className="text-xs">
                        Folder structure:
                        <br />
                        • <code className="bg-white px-1 rounded">~/entrust/reports/{folderInfo.customerCode}/</code> - Markdown reports
                        <br />
                        • <code className="bg-white px-1 rounded">~/entrust/report_json/{folderInfo.customerCode}/</code> - JSON reports
                        <br />
                        • <code className="bg-white px-1 rounded">~/entrust/reports_html/{folderInfo.customerCode}/</code> - HTML reports
                      </span>
                    </>
                  ) : (
                    <>
                      Please create the folder at: <code className="bg-white px-2 py-0.5 rounded font-mono text-xs">{folderInfo.path || '/app/entrust'}</code>
                      <br />
                      <span className="text-xs">The system will automatically create subfolders when generating reports.</span>
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Generate All Button */}
        <div className="mb-6">
          <button
            onClick={generateAllReports}
            disabled={generatingAll || !folderInfo?.exists}
            className={`px-6 py-3 rounded-lg font-semibold text-white shadow-lg flex items-center space-x-2 ${
              generatingAll || !folderInfo?.exists
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700'
            }`}
          >
            {generatingAll ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Generating All Reports...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Generate All Reports</span>
              </>
            )}
          </button>
        </div>

        {/* Dimension Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dimensions.map((dimension) => {
            const info = DIMENSION_INFO[dimension] || { description: dimension, color: 'gray' };
            const avail = availability[dimension] || {};
            const progress = dimensionProgress[dimension];

            return (
              <div key={dimension} className="bg-white border-2 border-gray-200 rounded-lg shadow-md p-5 hover:shadow-lg transition">
                {/* Dimension Name */}
                <h3 className="text-lg font-bold text-gray-800 mb-2">{dimension}</h3>

                {/* Description */}
                <p className="text-sm text-gray-600 mb-4 h-20 overflow-hidden">{info.description}</p>

                {/* Status Indicator */}
                {avail.html_exists && !progress && (
                  <div className="mb-3 flex items-center text-sm text-green-600">
                    <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span>Report available</span>
                  </div>
                )}

                {/* Buttons */}
                <div className="flex space-x-2 mb-3">
                  <button
                    onClick={() => generateDimensionReport(dimension)}
                    disabled={progress?.status === 'generating' || generatingAll || !folderInfo?.exists}
                    className={`flex-1 px-4 py-2 rounded-lg font-semibold transition flex items-center justify-center space-x-1 ${
                      progress?.status === 'generating' || generatingAll || !folderInfo?.exists
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-encora-green text-white hover:bg-green-600'
                    }`}
                  >
                    {progress?.status === 'generating' ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span className="text-xs">Generating...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                        <span className="text-sm">Generate</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => viewReport(dimension)}
                    disabled={!avail.html_exists || progress?.status === 'generating'}
                    className={`flex-1 px-4 py-2 rounded-lg font-semibold transition flex items-center justify-center space-x-1 ${
                      !avail.html_exists || progress?.status === 'generating'
                        ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    <span className="text-sm">View</span>
                  </button>
                </div>

                {/* Progress Bar */}
                {progress && (
                  <div className="space-y-1">
                    {progress.status === 'generating' && (
                      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div className="bg-encora-green h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
                      </div>
                    )}
                    {progress.status === 'completed' && (
                      <div className="flex items-center text-sm text-green-600">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span>Generated successfully</span>
                      </div>
                    )}
                    {progress.status === 'error' && (
                      <div className="text-sm text-red-600">
                        <div className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                          <span>Generation failed</span>
                        </div>
                        {progress.error && (
                          <p className="text-xs mt-1 text-red-500">{progress.error}</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default OfflineReports;
