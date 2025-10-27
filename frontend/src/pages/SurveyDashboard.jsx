import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { surveyAPI } from '../api';
import Breadcrumb from '../components/Breadcrumb';

export default function SurveyDashboard() {
  const [progress, setProgress] = useState([]);
  const [surveyStatus, setSurveyStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [progressRes, statusRes] = await Promise.all([
        surveyAPI.getProgress(),
        surveyAPI.getStatus()
      ]);
      setProgress(progressRes.data);
      setSurveyStatus(statusRes.data);
    } catch (error) {
      console.error('Failed to load survey data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!window.confirm('Are you sure you want to submit this survey? You will not be able to edit it after submission.')) {
      return;
    }

    try {
      await surveyAPI.submit();
      alert('Survey submitted successfully!');
      loadData();
    } catch (error) {
      alert('Failed to submit survey: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) return <div>Loading...</div>;

  const isSubmitted = surveyStatus?.status === 'Submitted';
  const allCompleted = progress.every(p => p.status === 'Completed');

  return (
    <div>
      <Breadcrumb 
        items={[{ label: 'Survey Dashboard' }]}
        customerCode={surveyStatus?.customer_code}
      />

      <div className="mb-6 bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Survey Dashboard</h1>
            <p className="text-gray-600 mt-2">Complete all sections to submit your survey</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600 mb-2">Overall Status</div>
            <div className={`text-xl font-bold ${
              isSubmitted ? 'text-green-600' :
              allCompleted ? 'text-blue-600' :
              'text-yellow-600'
            }`}>
              {surveyStatus?.status}
            </div>
          </div>
        </div>

        {allCompleted && !isSubmitted && (
          <div className="mt-4 pt-4 border-t">
            <button
              onClick={handleSubmit}
              className="px-6 py-3 bg-encora-green text-white rounded font-medium hover:bg-green-600"
            >
              Submit Survey
            </button>
          </div>
        )}

        {isSubmitted && (
          <div className="mt-4 pt-4 border-t">
            <div className="bg-green-50 text-green-800 p-4 rounded">
              ✅ Survey has been submitted. No further changes can be made.
            </div>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {progress.map((item) => (
          <Link
            key={item.dimension}
            to={isSubmitted ? '#' : `/survey/${encodeURIComponent(item.dimension)}`}
            className={`bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition ${
              isSubmitted ? 'cursor-not-allowed opacity-60' : ''
            }`}
            onClick={(e) => isSubmitted && e.preventDefault()}
          >
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              {item.dimension}
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Progress</span>
                <span className="font-medium">
                  {item.answered_questions}/{item.total_questions}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    item.status === 'Completed' ? 'bg-green-500' :
                    item.status === 'Not Started' ? 'bg-gray-300' :
                    'bg-yellow-500'
                  }`}
                  style={{ width: `${(item.answered_questions / item.total_questions) * 100}%` }}
                />
              </div>
              <div className={`text-sm font-medium ${
                item.status === 'Completed' ? 'text-green-600' :
                item.status === 'Not Started' ? 'text-gray-500' :
                'text-yellow-600'
              }`}>
                {item.status}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}