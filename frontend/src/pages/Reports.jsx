// frontend/src/pages/Reports.jsx
import { useState, useEffect, useRef } from 'react';
import { reportAPI } from '../api';
import Breadcrumb from '../components/Breadcrumb';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import RadarChart from '../components/RadarChart';
import FacetBarChart from '../components/FacetBarChart';
import MetricsTable from '../components/MetricsTable';
import CommentWordCloud from '../components/CommentWordCloud';
import LLMAnalysisDisplay from '../components/LLMAnalysisDisplay';

export default function Reports() {
  const [user, setUser] = useState(null);
  const [dimensions, setDimensions] = useState([]);
  const [selectedDimension, setSelectedDimension] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [customerCode, setCustomerCode] = useState(null);
  const reportRef = useRef(null);
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [isSalesUser, setIsSalesUser] = useState(false);
  const [isAdminUser, setIsAdminUser] = useState(false);
  const [showJson, setShowJson] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
      
      // Debug: Log user type
      console.log('User data:', parsedUser);
      console.log('User type:', parsedUser.user_type);
      
      const salesUser = parsedUser.user_type === 'Sales' || parsedUser.user_type === 'SALES';
      const adminUser = parsedUser.user_type === 'SystemAdmin';
      setIsSalesUser(salesUser);
      setIsAdminUser(adminUser);
      
      if (salesUser || adminUser) {
        loadCustomers(parsedUser);
      } else {
        loadDimensions(parsedUser, parsedUser.customer_id);
      }
    }
  }, []);

  const loadCustomers = async (userData) => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_URL}/api/reports/customers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      
      // Debug: Log customers
      console.log('Customers loaded:', data);
      console.log('Number of customers:', data.length);
      
      setCustomers(data);
      
      // Select first customer by default
      if (data.length > 0) {
        setSelectedCustomer(data[0]);
        loadDimensions(userData, data[0].id);
      }
    } catch (error) {
      console.error('Failed to load customers:', error);
    }
  };

  const loadDimensions = async (userData, customerId) => {
    try {
      const response = await reportAPI.getDimensions(customerId);
      
      // Check if response indicates no survey
      if (response.data && typeof response.data === 'object' && response.data.message) {
        setDimensions([]);
        console.log('No survey data for this customer');
      } else {
        setDimensions(response.data);
      }
      
      // Find customer code
      // Use a functional update for selectedCustomer to get the latest state
      setSelectedCustomer(prevCustomer => {
        const customer = customers.find(c => c && c.id === customerId) || prevCustomer;
        setCustomerCode(customer && customer.customer_code ? customer.customer_code : null);
        return customer;
      });
    } catch (error) {
      console.error('Failed to load dimensions:', error);
      setDimensions([]);
    }
  };

  const handleCustomerChange = (event) => {
    const customer = customers.find(c => c.id === parseInt(event.target.value));
    setSelectedCustomer(customer);
    setCustomerCode(customer?.customer_code || null);
    loadDimensions(user, customer.id);
    // Clear current report when changing customer
    setReport(null);
    setSelectedDimension(null);
    setShowJson(false);
  };

  const loadDimensionReport = async (dimension, forceRegenerate = false) => {
    setSelectedDimension(dimension);
    setLoading(true);
    setReport(null);

    try {
      const customerId = (isSalesUser || isAdminUser) ? (selectedCustomer?.id || user.customer_id) : user.customer_id;

      // Ensure customer code is set
      if ((isSalesUser || isAdminUser) && selectedCustomer) {
        setCustomerCode(selectedCustomer.customer_code);
      } else if (user.customer_code) {
        setCustomerCode(user.customer_code);
      }

      const response = await reportAPI.getDimensionReport(customerId, dimension, forceRegenerate);
      setReport(response.data);
      setShowJson(false);
    } catch (error) {
      console.error('Failed to load report:', error);
      alert('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const loadOverallReport = async (forceRegenerate = false) => {
    setSelectedDimension('Overall');
    setLoading(true);
    setReport(null);

    try {
      const customerId = (isSalesUser || isAdminUser) ? (selectedCustomer?.id || user.customer_id) : user.customer_id;

      // Ensure customer code is set
      if ((isSalesUser || isAdminUser) && selectedCustomer) {
        setCustomerCode(selectedCustomer.customer_code);
      } else if (user.customer_code) {
        setCustomerCode(user.customer_code);
      }

      const response = await reportAPI.getOverallReport(customerId, forceRegenerate);
      setReport(response.data);
      setShowJson(false);
    } catch (error) {
      console.error('Failed to load overall report:', error);
      alert('Failed to load overall report');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = () => {
    // Find all accordion/details elements and open them before printing
    const allDetails = document.querySelectorAll('details');
    const wasOpen = Array.from(allDetails).map(detail => detail.hasAttribute('open'));

    // Open all accordions
    allDetails.forEach(detail => detail.setAttribute('open', ''));

    // Small delay to ensure DOM updates before print dialog
    setTimeout(() => {
      // Use browser's native print dialog which produces perfect quality PDFs
      window.print();

      // Restore accordion states after a short delay
      setTimeout(() => {
        allDetails.forEach((detail, index) => {
          if (!wasOpen[index]) {
            detail.removeAttribute('open');
          }
        });
      }, 100);
    }, 100);
  };

  // Custom markdown components for better rendering
  const markdownComponents = {
    // Add proper spacing between paragraphs
    p: ({node, ...props}) => <p className="mb-4 leading-relaxed" {...props} />,
    
    // Style headers with proper spacing
    h1: ({node, ...props}) => <h1 className="text-2xl font-bold mb-4 mt-6" {...props} />,
    h2: ({node, ...props}) => <h2 className="text-xl font-bold mb-3 mt-5" {...props} />,
    h3: ({node, ...props}) => <h3 className="text-lg font-bold mb-2 mt-4" {...props} />,
    
    // Style lists with proper spacing
    ul: ({node, ...props}) => <ul className="list-disc list-inside mb-4 space-y-2" {...props} />,
    ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-4 space-y-2" {...props} />,
    li: ({node, ...props}) => <li className="ml-4" {...props} />,
    
    // Style tables properly
    table: ({node, ...props}) => (
      <div className="overflow-x-auto mb-4">
        <table className="min-w-full divide-y divide-gray-300 border border-gray-300" {...props} />
      </div>
    ),
    thead: ({node, ...props}) => <thead className="bg-gray-100" {...props} />,
    tbody: ({node, ...props}) => <tbody className="divide-y divide-gray-200" {...props} />,
    tr: ({node, ...props}) => <tr className="hover:bg-gray-50" {...props} />,
    th: ({node, ...props}) => (
      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-r border-gray-300 last:border-r-0" {...props} />
    ),
    td: ({node, ...props}) => (
      <td className="px-4 py-3 text-sm text-gray-700 border-r border-gray-200 last:border-r-0" {...props} />
    ),
    
    // Style code blocks
    code: ({node, inline, ...props}) => 
      inline ? (
        <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props} />
      ) : (
        <code className="block bg-gray-100 p-4 rounded mb-4 text-sm overflow-x-auto" {...props} />
      ),
    
    // Style blockquotes
    blockquote: ({node, ...props}) => (
      <blockquote className="border-l-4 border-encora-green pl-4 italic my-4 text-gray-700" {...props} />
    ),
    
    // Add line breaks
    br: ({node, ...props}) => <br className="my-2" {...props} />,
  };

  return (
    <>
    <div>
      <Breadcrumb 
        items={[{ label: 'Reports' }]}
        customerCode={customerCode}
      />

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Reports</h1>
        <div className="flex items-center space-x-4">
          {(isSalesUser || isAdminUser) && customers.length > 0 && (
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Customer:</label>
              <select
                value={selectedCustomer?.id || ''}
                onChange={handleCustomerChange}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-encora-green focus:border-transparent"
              >
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name} ({customer.customer_code}){!customer.has_survey ? ' - No Survey' : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
          {report && !loading && (
            <button
              onClick={() => {
                if (selectedDimension === 'Overall') {
                  loadOverallReport(true);
                } else {
                  loadDimensionReport(selectedDimension, true);
                }
              }}
              className="px-4 py-2 bg-encora-green text-white rounded-lg hover:bg-green-600 transition font-semibold shadow-md flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Re-generate Report</span>
            </button>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <button
          onClick={() => loadOverallReport()}
          className="bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg shadow-md p-6 hover:shadow-lg transition text-left"
        >
          <h3 className="text-xl font-bold mb-2">Overall Report</h3>
          <p className="text-purple-100 text-sm">
            Comprehensive analysis across all dimensions
          </p>
        </button>

        {dimensions.map((item) => (
          <button
            key={item.dimension}
            onClick={() => loadDimensionReport(item.dimension)}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition text-left border-2 border-transparent hover:border-encora-green"
          >
            <h3 className="text-lg font-bold text-gray-900 mb-2">
              {item.dimension}
            </h3>
            <p className="text-gray-600 text-sm">
              View detailed dimension report
            </p>
          </button>
        ))}
      </div>

      {loading && (
        <div className="bg-white rounded-lg shadow p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-encora-green"></div>
            <span className="ml-4 text-gray-600 text-lg">Loading report...</span>
          </div>
          <p className="text-center text-gray-500 mt-4 text-sm">
            Analyzing survey data and generating insights...
          </p>
        </div>
      )}

      {report && !loading && (
        <div className="bg-white rounded-lg shadow p-8" ref={reportRef}>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">{selectedDimension} Report</h2>
            <button
              onClick={() => {
                if (selectedDimension === 'Overall') {
                  loadOverallReport(true);
                } else {
                  loadDimensionReport(selectedDimension, true);
                }
              }}
              className="px-4 py-2 bg-encora-green text-white rounded-lg hover:bg-green-600 transition font-semibold shadow-md flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Re-generate Report</span>
            </button>
          </div>

          {selectedDimension === 'Overall' ? (
            <>
              {/* Overall Summary */}
              {report.overall_summary && (
                <div className="mb-8 bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-lg border-2 border-purple-200">
                  <h3 className="text-lg font-bold mb-4 text-purple-800 flex items-center">
                    <span className="text-2xl mr-2">🤖</span>
                    Executive Summary
                  </h3>
                  <div className="prose prose-sm max-w-none text-gray-800">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={markdownComponents}
                    >
                      {report.markdown_content || report.overall_summary}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {/* Overall Error */}
              {report.overall_error && (
                <div className="mb-8 bg-red-50 p-6 rounded-lg border-2 border-red-200">
                  <h3 className="text-lg font-bold mb-3 text-red-700 flex items-center">
                    <span className="text-2xl mr-2">⚠️</span>
                    LLM Analysis Error
                  </h3>
                  <p className="text-red-600 mb-2">{report.overall_error}</p>
                  <p className="text-sm text-gray-600">
                    The dimension reports below are still available.
                  </p>
                </div>
              )}

              {/* Overall Statistics */}
              {report.overall_stats && (
                <div className="mb-8 bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <h3 className="text-xl font-bold mb-4">Survey Statistics</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <div className="text-2xl font-bold text-encora-green">
                        {report.overall_stats.total_questions}
                      </div>
                      <div className="text-sm text-gray-600">Total Questions</div>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <div className="text-2xl font-bold text-blue-600">
                        {report.total_participants}
                      </div>
                      <div className="text-sm text-gray-600">Participants</div>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <div className="text-2xl font-bold text-purple-600">
                        {report.overall_stats.avg_score_overall.toFixed(2)}
                      </div>
                      <div className="text-sm text-gray-600">Average Score</div>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm">
                      <div className="text-2xl font-bold text-orange-600">
                        {report.overall_stats.dimensions?.length || 0}
                      </div>
                      <div className="text-sm text-gray-600">Dimensions</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Dimension Summaries */}
              {report.dimension_summaries && Object.keys(report.dimension_summaries).length > 0 && (
                <div className="space-y-6 mb-8">
                  <h3 className="text-xl font-bold mb-4">Dimension Analysis</h3>
                  {Object.entries(report.dimension_summaries).map(([dimension, summary]) => {
                    const dimStats = report.overall_stats?.dimensions?.find(d => d.dimension === dimension);
                    
                    return (
                      <div key={dimension} className="bg-gradient-to-r from-green-50 to-teal-50 p-6 rounded-lg border-2 border-green-200">
                        <h4 className="text-lg font-bold mb-3 text-gray-900">{dimension}</h4>
                        
                        {dimStats && (
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4 text-sm">
                            <div className="bg-white p-3 rounded shadow-sm">
                              <span className="text-gray-600">Avg Score:</span>
                              <span className="ml-2 font-bold text-encora-green">
                                {dimStats.avg_score !== null ? dimStats.avg_score.toFixed(2) : 'N/A'}
                              </span>
                            </div>
                            <div className="bg-white p-3 rounded shadow-sm">
                              <span className="text-gray-600">Min Score:</span>
                              <span className="ml-2 font-bold text-orange-600">
                                {dimStats.min_score !== null ? dimStats.min_score.toFixed(2) : 'N/A'}
                              </span>
                            </div>
                            <div className="bg-white p-3 rounded shadow-sm">
                              <span className="text-gray-600">Max Score:</span>
                              <span className="ml-2 font-bold text-blue-600">
                                {dimStats.max_score !== null ? dimStats.max_score.toFixed(2) : 'N/A'}
                              </span>
                            </div>
                          </div>
                        )}

                        <div className="prose prose-sm max-w-none text-gray-800 bg-white p-4 rounded">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={markdownComponents}
                          >
                            {summary}
                          </ReactMarkdown>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="mt-6 flex flex-wrap gap-4">
                <button
                  onClick={handleDownloadPDF}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center shadow-md hover:shadow-lg transition"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                  </svg>
                  Print / Save as PDF
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Section 1: Overall Metrics */}
              {report.overall_metrics && (
                <div className="mb-8">
                  <h3 className="text-xl font-bold mb-4">Dimension Overview</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg shadow-sm border border-green-200">
                      <div className="text-3xl font-bold text-green-700">
                        {report.overall_metrics.avg_score !== null ? report.overall_metrics.avg_score.toFixed(2) : 'N/A'}
                      </div>
                      <div className="text-sm text-gray-700 font-medium">Avg Score</div>
                    </div>
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg shadow-sm border border-blue-200">
                      <div className="text-3xl font-bold text-blue-700">
                        {report.overall_metrics.response_rate}
                      </div>
                      <div className="text-sm text-gray-700 font-medium">Response Rate</div>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg shadow-sm border border-purple-200">
                      <div className="text-3xl font-bold text-purple-700">
                        {report.overall_metrics.total_responses}
                      </div>
                      <div className="text-sm text-gray-700 font-medium">Total Responses</div>
                    </div>
                    <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-lg shadow-sm border border-orange-200">
                      <div className="text-3xl font-bold text-orange-700">
                        {report.overall_metrics.total_respondents}/{report.overall_metrics.total_users}
                      </div>
                      <div className="text-sm text-gray-700 font-medium">Respondents</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Section 2: Dimension-Level LLM Analysis */}
              {report.dimension_llm_analysis && (
                <div className="mb-8">
                  <LLMAnalysisDisplay
                    content={report.dimension_llm_analysis}
                    title="Strategic Analysis & Recommendations"
                    icon="📊"
                  />
                </div>
              )}

              {/* Dimension Error */}
              {report.llm_error && (
                <div className="mb-8 bg-red-50 p-6 rounded-lg border-2 border-red-200">
                  <h3 className="text-lg font-bold mb-3 text-red-700 flex items-center">
                    <span className="text-2xl mr-2">⚠️</span>
                    LLM Analysis Error
                  </h3>
                  <p className="text-red-600 mb-2">{report.llm_error}</p>
                  <p className="text-sm text-gray-600">
                    The report data below is still available. Please check LLM configuration.
                  </p>
                </div>
              )}

              {/* Section 3: Category Analysis */}
              {report.category_analysis && Object.keys(report.category_analysis).length > 0 && (
                <div className="mb-8 bg-white border-2 border-gray-200 rounded-lg p-6 shadow-md page-break">
                  <h3 className="text-xl font-bold mb-6 text-gray-900 flex items-center">
                    <span className="text-2xl mr-2">📂</span>
                    Category Analysis
                  </h3>

                  {/* Chart on top */}
                  <div className="mb-8">
                    <FacetBarChart
                      data={Object.values(report.category_analysis)}
                      facetType="category"
                      title="Category Scores Comparison"
                    />
                  </div>

                  {/* Table at bottom */}
                  <div className="mt-6">
                    <MetricsTable
                      data={Object.values(report.category_analysis)}
                      facetType="Category"
                    />
                  </div>

                  {report.category_llm_analyses && Object.keys(report.category_llm_analyses).length > 0 && (
                    <div className="mt-8 space-y-4">
                      <h4 className="text-lg font-semibold text-gray-800 mb-4">Category-Specific Insights</h4>
                      {Object.entries(report.category_llm_analyses).map(([category, analysis]) => (
                        <details key={category} className="bg-blue-50 border-2 border-blue-300 rounded-lg accordion-section print-section-break">
                          <summary className="cursor-pointer p-4 font-semibold text-blue-900 hover:bg-blue-100 transition print-heading">
                            {category}
                          </summary>
                          <div className="p-6 border-t-2 border-blue-200 print-content">
                            <LLMAnalysisDisplay
                              content={analysis}
                            />
                          </div>
                        </details>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Section 4: Process Analysis */}
              {report.process_analysis && Object.keys(report.process_analysis).length > 0 && (
                <div className="mb-8 bg-white border-2 border-gray-200 rounded-lg p-6 shadow-md page-break">
                  <h3 className="text-xl font-bold mb-6 text-gray-900 flex items-center">
                    <span className="text-2xl mr-2">⚙️</span>
                    Process Analysis
                  </h3>

                  {/* Chart on top */}
                  <div className="mb-8">
                    <FacetBarChart
                      data={Object.values(report.process_analysis)}
                      facetType="process"
                      title="Process Scores Comparison"
                    />
                  </div>

                  {/* Table at bottom */}
                  <div className="mt-6">
                    <MetricsTable
                      data={Object.values(report.process_analysis)}
                      facetType="Process"
                    />
                  </div>

                  {report.process_llm_analyses && Object.keys(report.process_llm_analyses).length > 0 && (
                    <div className="mt-8 space-y-4">
                      <h4 className="text-lg font-semibold text-gray-800 mb-4">Process-Specific Insights</h4>
                      {Object.entries(report.process_llm_analyses).map(([process, analysis]) => (
                        <details key={process} className="bg-purple-50 border-2 border-purple-300 rounded-lg accordion-section print-section-break">
                          <summary className="cursor-pointer p-4 font-semibold text-purple-900 hover:bg-purple-100 transition print-heading">
                            {process}
                          </summary>
                          <div className="p-6 border-t-2 border-purple-200 print-content">
                            <LLMAnalysisDisplay
                              content={analysis}
                            />
                          </div>
                        </details>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Section 5: Lifecycle Stage Analysis */}
              {report.lifecycle_analysis && Object.keys(report.lifecycle_analysis).length > 0 && (
                <div className="mb-8 bg-white border-2 border-gray-200 rounded-lg p-6 shadow-md page-break">
                  <h3 className="text-xl font-bold mb-6 text-gray-900 flex items-center">
                    <span className="text-2xl mr-2">🔄</span>
                    Lifecycle Stage Analysis
                  </h3>

                  {/* Chart on top */}
                  <div className="mb-8">
                    <FacetBarChart
                      data={Object.values(report.lifecycle_analysis)}
                      facetType="lifecycle_stage"
                      title="Lifecycle Stage Scores Comparison"
                    />
                  </div>

                  {/* Table at bottom */}
                  <div className="mt-6">
                    <MetricsTable
                      data={Object.values(report.lifecycle_analysis)}
                      facetType="Lifecycle Stage"
                    />
                  </div>

                  {report.lifecycle_llm_analyses && Object.keys(report.lifecycle_llm_analyses).length > 0 && (
                    <div className="mt-8 space-y-4">
                      <h4 className="text-lg font-semibold text-gray-800 mb-4">Lifecycle-Specific Insights</h4>
                      {Object.entries(report.lifecycle_llm_analyses).map(([lifecycle, analysis]) => (
                        <details key={lifecycle} className="bg-green-50 border-2 border-green-300 rounded-lg accordion-section print-section-break">
                          <summary className="cursor-pointer p-4 font-semibold text-green-900 hover:bg-green-100 transition print-heading">
                            {lifecycle}
                          </summary>
                          <div className="p-6 border-t-2 border-green-200 print-content">
                            <LLMAnalysisDisplay
                              content={analysis}
                            />
                          </div>
                        </details>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Section 6: Comment Analysis */}
              {report.comment_insights && report.comment_insights.total_comments > 0 && (
                <div className="mb-8 bg-white border-2 border-gray-200 rounded-lg p-6 shadow-md page-break">
                  <h3 className="text-xl font-bold mb-6 text-gray-900 flex items-center">
                    <span className="text-2xl mr-2">💬</span>
                    Comment Analysis
                  </h3>

                  {/* Statistics and Sentiment */}
                  <div className="mb-6 grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="text-2xl font-bold text-gray-900">{report.comment_insights.total_comments}</div>
                      <div className="text-xs text-gray-600">Total Comments</div>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <div className="text-2xl font-bold text-green-700">{report.comment_insights.positive_count || 0}</div>
                      <div className="text-xs text-gray-600">Positive</div>
                    </div>
                    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                      <div className="text-2xl font-bold text-red-700">{report.comment_insights.negative_count || 0}</div>
                      <div className="text-xs text-gray-600">Negative</div>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="text-2xl font-bold text-blue-700">{report.comment_insights.neutral_count || 0}</div>
                      <div className="text-xs text-gray-600">Neutral</div>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                      <div className="text-2xl font-bold text-purple-700">{report.comment_insights.avg_comment_length}</div>
                      <div className="text-xs text-gray-600">Avg Length (chars)</div>
                    </div>
                  </div>

                  {report.comment_insights.word_frequency && Object.keys(report.comment_insights.word_frequency).length > 0 && (
                    <div className="mb-6">
                      <CommentWordCloud
                        wordFrequency={report.comment_insights.word_frequency}
                        title="Most Frequently Mentioned Words"
                      />
                    </div>
                  )}

                  {report.comment_insights.llm_analysis && (
                    <div className="mt-6">
                      <LLMAnalysisDisplay
                        content={report.comment_insights.llm_analysis}
                        title="Comment Sentiment & Themes Analysis"
                        icon="💭"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Section 7: Question-Level Details */}
              <div className="mb-8">
                <h3 className="text-xl font-bold mb-4 text-gray-900 flex items-center">
                  <span className="text-2xl mr-2">📋</span>
                  Question-Level Details
                </h3>
                <div className="overflow-x-auto rounded-lg border border-gray-200">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-16">
                          Q#
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Question
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Process
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Lifecycle
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Responses
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Avg Score
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {report.questions?.map((q, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm font-semibold text-gray-700 text-center">
                            {q.question_id || index + 1}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900">
                            {q.question}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                            {q.category || '-'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                            {q.process || '-'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                            {q.lifecycle_stage || '-'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                            {q.responded}
                          </td>
                          <td className="px-6 py-4 text-sm font-medium text-gray-900 whitespace-nowrap">
                            {q.avg_score !== null ? q.avg_score.toFixed(2) : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mt-6 flex flex-wrap gap-4">
                <button
                  onClick={handleDownloadPDF}
                  className="px-6 py-3 bg-encora-green text-white rounded-lg hover:bg-green-600 flex items-center shadow-md hover:shadow-lg transition"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                  </svg>
                  Print / Save as PDF
                </button>
              </div>

              {/* JSON Output Section */}
              {(report.final_json || report.json_content) && (
                <div className="mt-8 border-t pt-6">
                  <button
                    onClick={() => setShowJson(!showJson)}
                    className="text-lg font-semibold text-gray-700 hover:text-encora-green flex items-center"
                  >
                    {showJson ? (
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                    ) : (
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                    )}
                    View Raw JSON Output
                  </button>
                  {showJson && (
                    <div className="mt-4 bg-gray-900 text-white p-4 rounded-lg overflow-x-auto">
                      <pre className="text-sm">
                        <code>
                          {JSON.stringify(report.final_json || report.json_content, null, 2)}
                        </code>
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
    <style>{`
      @media print {
        /* Page setup */
        @page {
          size: A4;
          margin: 1.5cm;
        }

        /* Page break control */
        .page-break {
          page-break-before: auto;
          break-before: auto;
        }

        .print-section-break {
          page-break-inside: avoid;
          break-inside: avoid;
        }

        /* Force all accordions to be open and display all content */
        details {
          display: block !important;
          page-break-inside: avoid;
        }

        /* Force details to show all content, not just when open */
        details > * {
          display: block !important;
        }

        /* Style accordion titles as section headers */
        details summary {
          display: block !important;
          list-style: none !important;
          page-break-after: avoid;
          font-weight: 700 !important;
          font-size: 1.1em !important;
          margin-top: 1.5rem !important;
          margin-bottom: 0.75rem !important;
          padding: 0.75rem 1rem !important;
          background-color: #f3f4f6 !important;
          border-left: 4px solid #10b981 !important;
          color: #1f2937 !important;
        }

        /* Remove the disclosure triangle */
        details summary::-webkit-details-marker,
        details summary::marker {
          display: none !important;
        }

        /* Show accordion content */
        details summary ~ * {
          display: block !important;
        }

        .print-content {
          display: block !important;
          page-break-inside: avoid;
          padding: 1rem !important;
          margin-bottom: 1rem !important;
        }

        /* Accordion section styling */
        .accordion-section {
          border: 1px solid #e5e7eb !important;
          border-radius: 0.5rem !important;
          margin-bottom: 1.5rem !important;
          page-break-inside: avoid;
        }

        /* Table improvements for print */
        table {
          page-break-inside: auto;
          border-collapse: collapse !important;
          width: 100% !important;
        }

        tr {
          page-break-inside: avoid;
          page-break-after: auto;
        }

        thead {
          display: table-header-group;
        }

        tfoot {
          display: table-footer-group;
        }

        th, td {
          border: 1px solid #d1d5db !important;
          padding: 0.5rem !important;
        }

        /* Chart containers */
        .recharts-wrapper,
        svg {
          page-break-inside: avoid;
          max-width: 100% !important;
        }

        /* Hide interactive elements */
        button {
          display: none !important;
        }

        /* Hide breadcrumb and navigation */
        nav {
          display: none !important;
        }

        /* Better spacing for headings */
        h1, h2, h3, h4, h5, h6 {
          page-break-after: avoid;
          page-break-inside: avoid;
        }

        h1 {
          margin-top: 0 !important;
          margin-bottom: 1.5rem !important;
        }

        h2 {
          margin-top: 1.5rem !important;
          margin-bottom: 1rem !important;
        }

        h3 {
          margin-top: 1.25rem !important;
          margin-bottom: 0.75rem !important;
        }

        /* Ensure backgrounds and colors print correctly */
        * {
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
          color-adjust: exact !important;
        }

        /* Better text rendering */
        body {
          font-size: 11pt !important;
          line-height: 1.5 !important;
          color: #000 !important;
        }

        /* Improve prose rendering */
        .prose p {
          margin-bottom: 0.75rem !important;
        }

        .prose ul, .prose ol {
          margin-bottom: 0.75rem !important;
          padding-left: 1.5rem !important;
        }

        .prose li {
          margin-bottom: 0.25rem !important;
        }

        /* Stats cards */
        .grid {
          display: grid !important;
        }

        /* Fix word cloud and charts */
        canvas {
          max-width: 100% !important;
          page-break-inside: avoid;
        }
      }
    `}</style></>
  );
}