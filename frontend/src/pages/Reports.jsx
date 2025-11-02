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
  const [downloading, setDownloading] = useState(false);
  const reportRef = useRef(null);
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [isSalesUser, setIsSalesUser] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
      
      // Debug: Log user type
      console.log('User data:', parsedUser);
      console.log('User type:', parsedUser.user_type);
      
      const salesUser = parsedUser.user_type === 'Sales' || parsedUser.user_type === 'SALES';
      setIsSalesUser(salesUser);
      
      if (salesUser) {
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
      const customer = [...customers, selectedCustomer].find(c => c && c.id === customerId);
      if (customer) {
        setCustomerCode(customer.customer_code || null);
      }
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
  };

  const loadDimensionReport = async (dimension) => {
    setSelectedDimension(dimension);
    setLoading(true);
    setReport(null);

    try {
      const customerId = isSalesUser ? (selectedCustomer?.id || user.customer_id) : user.customer_id;

      // Ensure customer code is set
      if (isSalesUser && selectedCustomer) {
        setCustomerCode(selectedCustomer.customer_code);
      } else if (user.customer_code) {
        setCustomerCode(user.customer_code);
      }

      const response = await reportAPI.getDimensionReport(customerId, dimension);
      setReport(response.data);
    } catch (error) {
      console.error('Failed to load report:', error);
      alert('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const loadOverallReport = async () => {
    setSelectedDimension('Overall');
    setLoading(true);
    setReport(null);

    try {
      const customerId = isSalesUser ? (selectedCustomer?.id || user.customer_id) : user.customer_id;

      // Ensure customer code is set
      if (isSalesUser && selectedCustomer) {
        setCustomerCode(selectedCustomer.customer_code);
      } else if (user.customer_code) {
        setCustomerCode(user.customer_code);
      }

      const response = await reportAPI.getOverallReport(customerId);
      setReport(response.data);
    } catch (error) {
      console.error('Failed to load overall report:', error);
      alert('Failed to load overall report');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!reportRef.current) return;

    setDownloading(true);
    try {
      // Dynamically import jsPDF and html2canvas
      const { default: jsPDF } = await import('jspdf');
      const html2canvas = (await import('html2canvas')).default;

      // Expand all accordion/details elements before cloning
      const allDetails = reportRef.current.querySelectorAll('details');
      const wasOpen = Array.from(allDetails).map(detail => detail.hasAttribute('open'));
      allDetails.forEach(detail => detail.setAttribute('open', ''));

      // Wait for any animations/transitions to complete
      await new Promise(resolve => setTimeout(resolve, 500));

      // Create a clone of the report content
      const content = reportRef.current.cloneNode(true);

      // Remove download button from clone
      const buttons = content.querySelectorAll('button');
      buttons.forEach(btn => btn.remove());

      // Remove interactive elements from clone
      const summaries = content.querySelectorAll('summary');
      summaries.forEach(summary => {
        // Convert summary to div to remove interactive behavior
        const div = document.createElement('div');
        div.className = summary.className;
        div.innerHTML = summary.innerHTML;
        summary.parentNode.replaceChild(div, summary);
      });

      // Create a temporary container
      const tempContainer = document.createElement('div');
      tempContainer.style.position = 'absolute';
      tempContainer.style.left = '-9999px';
      tempContainer.style.width = '210mm'; // A4 width
      tempContainer.style.padding = '20px';
      tempContainer.style.backgroundColor = 'white';
      tempContainer.appendChild(content);
      document.body.appendChild(tempContainer);

      // Wait a bit more for SVG charts to fully render
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Convert all SVG elements to img elements for better compatibility
      const svgElements = tempContainer.querySelectorAll('svg');
      for (const svg of svgElements) {
        try {
          // Get SVG dimensions
          const svgRect = svg.getBoundingClientRect();
          const svgWidth = svgRect.width || svg.getAttribute('width') || 800;
          const svgHeight = svgRect.height || svg.getAttribute('height') || 400;

          // Serialize SVG to string
          const svgData = new XMLSerializer().serializeToString(svg);
          const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
          const svgUrl = URL.createObjectURL(svgBlob);

          // Create canvas to convert SVG to PNG
          const canvas = document.createElement('canvas');
          canvas.width = svgWidth * 2; // 2x for better quality
          canvas.height = svgHeight * 2;
          const ctx = canvas.getContext('2d');

          // Create image from SVG
          const img = new Image();
          await new Promise((resolve, reject) => {
            img.onload = () => {
              ctx.scale(2, 2);
              ctx.drawImage(img, 0, 0);
              URL.revokeObjectURL(svgUrl);
              resolve();
            };
            img.onerror = () => {
              URL.revokeObjectURL(svgUrl);
              reject(new Error('Failed to load SVG'));
            };
            img.src = svgUrl;
          });

          // Convert canvas to image element
          const pngDataUrl = canvas.toDataURL('image/png');
          const imgElement = document.createElement('img');
          imgElement.src = pngDataUrl;
          imgElement.style.width = `${svgWidth}px`;
          imgElement.style.height = `${svgHeight}px`;
          imgElement.style.display = 'block';

          // Replace SVG with IMG
          svg.parentNode.replaceChild(imgElement, svg);
        } catch (err) {
          console.warn('Failed to convert SVG to image:', err);
          // Leave SVG as is if conversion fails
        }
      }

      // Wait for replaced images to load
      await new Promise(resolve => setTimeout(resolve, 500));

      // Generate canvas from HTML with optimized settings
      const canvas = await html2canvas(tempContainer, {
        scale: 1.5, // Reduced from 2 for better performance
        useCORS: true,
        allowTaint: true,
        logging: false,
        backgroundColor: '#ffffff',
        windowWidth: tempContainer.scrollWidth,
        windowHeight: tempContainer.scrollHeight,
        imageTimeout: 15000,
        onclone: (clonedDoc) => {
          // Ensure all styles are applied in the cloned document
          const clonedContainer = clonedDoc.querySelector('div');
          if (clonedContainer) {
            clonedContainer.style.width = '210mm';
            clonedContainer.style.padding = '20px';
          }
        }
      });

      // Cleanup temp container
      document.body.removeChild(tempContainer);

      // Validate canvas
      if (!canvas || canvas.width === 0 || canvas.height === 0) {
        throw new Error('Canvas generation failed - invalid dimensions');
      }

      // Calculate PDF dimensions
      const imgWidth = 210; // A4 width in mm
      const pageHeight = 297; // A4 height in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      const pdf = new jsPDF('p', 'mm', 'a4');
      let heightLeft = imgHeight;
      let position = 0;

      // Convert canvas to image data with error handling
      let imgData;
      try {
        imgData = canvas.toDataURL('image/png', 0.95);

        // Validate the data URL
        if (!imgData || imgData === 'data:,' || imgData.length < 100) {
          throw new Error('Invalid image data generated');
        }
      } catch (err) {
        throw new Error(`Failed to convert canvas to image: ${err.message}`);
      }

      // Add image to PDF (handle multiple pages)
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      // Save PDF with proper filename
      const safeDimension = (selectedDimension || 'Report').replace(/[^a-zA-Z0-9]/g, '_');
      const safeCustomerCode = (customerCode || 'Customer').replace(/[^a-zA-Z0-9]/g, '_');
      const filename = `${safeCustomerCode}_${safeDimension}_Report.pdf`;
      pdf.save(filename);

      // Restore accordion states
      allDetails.forEach((detail, index) => {
        if (!wasOpen[index]) {
          detail.removeAttribute('open');
        }
      });

    } catch (error) {
      console.error('PDF Generation Error:', error);
      console.error('Error stack:', error.stack);

      let errorMessage = 'Failed to generate PDF. ';

      if (error.message.includes('PNG')) {
        errorMessage += 'There was an issue rendering charts. Try viewing the report in a different browser or contact support.';
      } else if (error.message.includes('canvas')) {
        errorMessage += 'The report content could not be captured. Please try again.';
      } else if (error.message.includes('memory')) {
        errorMessage += 'The report is too large. Try generating reports for individual dimensions.';
      } else {
        errorMessage += error.message || 'Please try again or contact support.';
      }

      alert(errorMessage);
    } finally {
      setDownloading(false);
    }
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
        {isSalesUser && customers.length > 0 && (
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
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <button
          onClick={loadOverallReport}
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
          <h2 className="text-2xl font-bold mb-6">{selectedDimension} Report</h2>

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
                      {report.overall_summary}
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

              <div className="mt-6 flex space-x-4">
                <button 
                  onClick={handleDownloadPDF}
                  disabled={downloading}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center shadow-md hover:shadow-lg transition"
                >
                  {downloading ? (
                    <>
                      <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Generating PDF...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Download PDF
                    </>
                  )}
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

              <div className="mt-6 flex space-x-4">
                <button
                  onClick={handleDownloadPDF}
                  disabled={downloading}
                  className="px-6 py-3 bg-encora-green text-white rounded-lg hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center shadow-md hover:shadow-lg transition"
                >
                  {downloading ? (
                    <>
                      <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Generating PDF...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Download PDF
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
    <style>{`
      @media print {
        /* Page break control */
        .page-break {
          page-break-before: auto;
          break-before: auto;
        }

        .print-section-break {
          page-break-inside: avoid;
          break-inside: avoid;
        }

        /* Expand all accordions for printing */
        details {
          display: block !important;
        }

        details summary {
          display: block !important;
          list-style: none;
          page-break-after: avoid;
          font-weight: 600;
          margin-bottom: 0.5rem;
          background-color: #f3f4f6 !important;
          padding: 0.75rem !important;
          border-radius: 0.5rem;
        }

        details summary::-webkit-details-marker {
          display: none;
        }

        details[open] summary ~ * {
          display: block !important;
        }

        .print-content {
          page-break-inside: avoid;
          padding: 1rem !important;
        }

        /* Table improvements for print */
        table {
          page-break-inside: auto;
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

        /* Chart containers */
        .recharts-wrapper,
        svg {
          page-break-inside: avoid;
        }

        /* Hide interactive elements */
        button {
          display: none !important;
        }

        /* Better spacing */
        h2, h3, h4 {
          page-break-after: avoid;
        }

        /* Ensure borders show in print */
        * {
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
      }
    `}</style></>
  );
}