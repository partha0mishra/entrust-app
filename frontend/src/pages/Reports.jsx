import { useState, useEffect } from 'react';
import { reportAPI } from '../api';
import Breadcrumb from '../components/Breadcrumb';
import ReactMarkdown from 'react-markdown';

export default function Reports() {
  const [user, setUser] = useState(null);
  const [dimensions, setDimensions] = useState([]);
  const [selectedDimension, setSelectedDimension] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [customerCode, setCustomerCode] = useState(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
      loadDimensions(parsedUser);
    }
  }, []);

  const loadDimensions = async (userData) => {
    try {
      const customerId = userData.customer_id;
      const response = await reportAPI.getDimensions(customerId);
      setDimensions(response.data);
      
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const statusResponse = await fetch(`${API_URL}/api/survey/status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const statusData = await statusResponse.json();
      setCustomerCode(statusData.customer_code);
    } catch (error) {
      console.error('Failed to load dimensions:', error);
    }
  };

  const loadDimensionReport = async (dimension) => {
    setSelectedDimension(dimension);
    setLoading(true);
    setReport(null);

    try {
      const response = await reportAPI.getDimensionReport(user.customer_id, dimension);
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
      const response = await reportAPI.getOverallReport(user.customer_id);
      setReport(response.data);
    } catch (error) {
      console.error('Failed to load overall report:', error);
      alert('Failed to load overall report');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!user || !selectedDimension) return;

    setDownloading(true);
    try {
      let response;
      if (selectedDimension === 'Overall') {
        response = await reportAPI.downloadOverallPDF(user.customer_id);
      } else {
        response = await reportAPI.downloadDimensionPDF(user.customer_id, selectedDimension);
      }
      
      // Create blob from response
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      
      // Create download link
      const link = document.createElement('a');
      link.href = url;
      const safeDimension = selectedDimension.replace(/[^a-zA-Z0-9]/g, '_');
      link.download = `${customerCode}_${safeDimension}_Report.pdf`;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download PDF:', error);
      alert('Failed to download PDF: ' + (error.response?.data?.detail || error.message));
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div>
      <Breadcrumb 
        items={[{ label: 'Reports' }]}
        customerCode={customerCode}
      />

      <h1 className="text-3xl font-bold mb-6">Reports</h1>

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
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-gray-600">Loading report...</div>
        </div>
      )}

      {report && !loading && (
        <div className="bg-white rounded-lg shadow p-8">
          <h2 className="text-2xl font-bold mb-6">{selectedDimension} Report</h2>

          {selectedDimension === 'Overall' ? (
            <>
              {report.executive_summary && (
                <div className="mb-8 bg-purple-50 p-6 rounded-lg border border-purple-200">
                  <h3 className="text-lg font-bold mb-3 text-purple-700">
                    🤖 Executive Summary
                  </h3>
                  <div className="prose prose-sm max-w-none text-gray-700">
                    <ReactMarkdown>{report.executive_summary}</ReactMarkdown>
                  </div>
                </div>
              )}

              {report.llm_error && (
                <div className="mb-8 bg-red-50 p-6 rounded-lg border border-red-200">
                  <h3 className="text-lg font-bold mb-3 text-red-700">
                    ⚠️ LLM Analysis Error
                  </h3>
                  <p className="text-red-600">{report.llm_error}</p>
                  <p className="text-sm text-gray-600 mt-2">
                    The dimension reports below are still available.
                  </p>
                </div>
              )}

              {report.dimensions && report.dimensions.length > 0 && (
                <div className="space-y-6">
                  <h3 className="text-xl font-bold mb-4">Dimension Analysis</h3>
                  {report.dimensions.map((dim) => (
                    <div key={dim.dimension} className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                      <h4 className="text-lg font-bold mb-3 text-gray-900">{dim.dimension}</h4>
                      
                      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                        <div>
                          <span className="text-gray-600">Average Score:</span>
                          <span className="ml-2 font-semibold text-gray-900">
                            {dim.avg_score !== null ? dim.avg_score.toFixed(2) : 'N/A'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Response Rate:</span>
                          <span className="ml-2 font-semibold text-gray-900">{dim.response_rate}</span>
                        </div>
                      </div>

                      {dim.summary && (
                        <div className="prose prose-sm max-w-none text-gray-700 mt-3">
                          <ReactMarkdown>{dim.summary}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6 flex space-x-4">
                <button 
                  onClick={handleDownloadPDF}
                  disabled={downloading}
                  className="px-6 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {downloading ? 'Downloading...' : 'Download PDF'}
                </button>
              </div>
            </>
          ) : (
            <>
              {report.llm_summary && (
                <div className="mb-8 bg-green-50 p-6 rounded-lg border border-green-200">
                  <h3 className="text-lg font-bold mb-3 text-encora-green">
                    🤖 AI-Generated Summary & Suggestions
                  </h3>
                  <div className="prose prose-sm max-w-none text-gray-700">
                    <ReactMarkdown>{report.llm_summary}</ReactMarkdown>
                  </div>
                </div>
              )}

              {report.llm_error && (
                <div className="mb-8 bg-red-50 p-6 rounded-lg border border-red-200">
                  <h3 className="text-lg font-bold mb-3 text-red-700">
                    ⚠️ LLM Analysis Error
                  </h3>
                  <p className="text-red-600">{report.llm_error}</p>
                  <p className="text-sm text-gray-600 mt-2">
                    The report data below is still available. Please check LLM configuration.
                  </p>
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
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
                  className="px-6 py-2 bg-encora-green text-white rounded hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {downloading ? 'Downloading...' : 'Download PDF'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}