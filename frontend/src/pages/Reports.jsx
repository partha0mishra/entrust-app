// frontend/src/pages/Reports.jsx
import { useState, useEffect, useRef } from 'react';
import { reportAPI } from '../api';
import Breadcrumb from '../components/Breadcrumb';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
      // Use a functional update for selectedCustomer to get the latest state
      setSelectedCustomer(prevCustomer => {
        const customer = customers.find(c => c && c.id === customerId) || prevCustomer;
        setCustomerCode(customer.customer_code || null);
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

  const loadDimensionReport = async (dimension) => {
    setSelectedDimension(dimension);
    setLoading(true);
    setReport(null);

    try {
      const customerId = isSalesUser ? (selectedCustomer?.id || user.customer_id) : user.customer_id;
      const response = await reportAPI.getDimensionReport(customerId, dimension);
      setReport(response.data);
      setShowJson(false);
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
      const response = await reportAPI.getOverallReport(customerId);
      setReport(response.data);
      setShowJson(false);
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
      const { default: autoTable } = await import('jspdf-autotable');
      const html2canvas = (await import('html2canvas')).default;

      // Create a clone of the report content for PDF generation
      const content = reportRef.current.cloneNode(true);
      
      // Remove download button and other interactive elements from clone
      const buttons = content.querySelectorAll('button');
      buttons.forEach(btn => btn.remove());

      // Separate markdown content from tables for individual processing
      const tables = content.querySelectorAll('table');
      const nonTableContent = content.cloneNode(true);
      nonTableContent.querySelectorAll('table').forEach(t => t.remove());


      // Create a temporary container
      const tempContainer = document.createElement('div');
      tempContainer.style.position = 'absolute';
      tempContainer.style.left = '-9999px';
      // Use a fixed width that works well for html2canvas rendering
      tempContainer.style.width = '1000px'; 
      tempContainer.style.padding = '20px';
      tempContainer.style.backgroundColor = 'white';
      tempContainer.appendChild(content);
      document.body.appendChild(tempContainer);

      // Generate canvas from HTML
      const canvas = await html2canvas(tempContainer, {
        width: tempContainer.scrollWidth,
        height: tempContainer.scrollHeight,
        scale: 1.5, // Reduced scale to decrease file size
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
      });

      const pdf = new jsPDF('p', 'mm', 'a4'); // portrait, mm, a4
      const margin = 15;
      const pdfWidth = pdf.internal.pageSize.getWidth();

      const addHeaderAndFooter = (pdf, pageNum, totalPages) => {
        const pdfHeight = pdf.internal.pageSize.getHeight();
        // Header
        pdf.setFontSize(10);
        pdf.setTextColor(150);
        pdf.text('EnTrust (TM) by Encora', margin, 10);
        
        const customerName = selectedCustomer?.name || '';
        if (customerName) {
          const customerNameWidth = pdf.getStringUnitWidth(customerName) * pdf.getFontSize() / pdf.internal.scaleFactor;
          pdf.text(customerName, pdfWidth - margin - customerNameWidth, 10);
        }
        
        // Footer
        const footerText = `Page ${pageNum} of ${totalPages}`;
        const footerTextWidth = pdf.getStringUnitWidth(footerText) * pdf.getFontSize() / pdf.internal.scaleFactor;
        pdf.text(footerText, (pdfWidth - footerTextWidth) / 2, pdfHeight - 10);
      };

      // 1. Add non-table content as an image
      const imgData = canvas.toDataURL('image/jpeg', 0.8);
      const imgWidth = pdfWidth - margin * 2;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      pdf.addImage(imgData, 'JPEG', margin, margin + 5, imgWidth, imgHeight);

      let lastY = margin + 5 + imgHeight;

      // 2. Add tables using autoTable
      tables.forEach(table => {
        autoTable(pdf, {
          html: table,
          startY: lastY + 5,
          theme: 'grid',
          headStyles: { fillColor: [230, 230, 230], textColor: 20 },
          styles: { fontSize: 8 },
          margin: { left: margin, right: margin },
          didDrawPage: (data) => {
            // This will be handled in the final loop
          }
        });
        lastY = pdf.lastAutoTable.finalY;
      });

      // 3. Add headers and footers to all pages
      const totalPages = pdf.internal.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        pdf.setPage(i);
        addHeaderAndFooter(pdf, i, totalPages);
      }

      // Save PDF
      const safeDimension = selectedDimension ? selectedDimension.replace(/[^a-zA-Z0-9]/g, '_') : 'Report';
      const customerPrefix = customerCode ? `${customerCode}_` : '';
      const filename = `${customerPrefix}${safeDimension}_Report.pdf`;
      pdf.save(filename);

      // Cleanup
      document.body.removeChild(tempContainer);
    } catch (error) {
      console.error('Failed to generate PDF:', error);
      alert('Failed to generate PDF. Please ensure you have a stable internet connection.');
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
              {/* Dimension LLM Summary */}
              {report.llm_summary && (
                <div className="mb-8 bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-lg border-2 border-green-200">
                  <h3 className="text-lg font-bold mb-4 text-encora-green flex items-center">
                    Strategic Insights, Observations & Action Plan
                    <br/>
                    <span className="text-2xl mr-2">🤖</span>
                    Leveraging Augmented-Intelligence
                  </h3>
                  <div className="prose prose-sm max-w-none text-gray-800">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={markdownComponents}
                    >
                      {report.final_summary || report.llm_summary}
                    </ReactMarkdown>
                  </div>
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

              {/* Question Data Table */}
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
                        Responses
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Min Score
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Max Score
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
                          {index + 1}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {q.question}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                          {q.responded}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                          {q.min_score !== null ? q.min_score : '-'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                          {q.max_score !== null ? q.max_score : '-'}
                        </td>
                        <td className="px-6 py-4 text-sm font-medium text-gray-900 whitespace-nowrap">
                          {q.avg_score !== null ? q.avg_score : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
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
  );
}