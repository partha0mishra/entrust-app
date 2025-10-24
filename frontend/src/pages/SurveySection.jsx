import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { surveyAPI } from '../api';
import Breadcrumb from '../components/Breadcrumb';

export default function SurveySection() {
  const { dimension } = useParams();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [responses, setResponses] = useState({});
  const [customerCode, setCustomerCode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});

  useEffect(() => {
    loadData();
  }, [dimension]);

  const loadData = async () => {
    try {
      const [questionsRes, responsesRes, statusRes] = await Promise.all([
        surveyAPI.getQuestionsByDimension(dimension),
        surveyAPI.getResponses(dimension),
        surveyAPI.getStatus()
      ]);
      
      setQuestions(questionsRes.data);
      setResponses(responsesRes.data);
      setCustomerCode(statusRes.data?.customer_code);
    } catch (error) {
      console.error('Failed to load section data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleScoreChange = async (questionId, score) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        score
      }
    }));

    setSaving(prev => ({ ...prev, [questionId]: true }));

    try {
      await surveyAPI.saveResponse({
        question_id: questionId,
        score,
        comment: responses[questionId]?.comment || null
      });
    } catch (error) {
      alert('Failed to save response');
    } finally {
      setSaving(prev => ({ ...prev, [questionId]: false }));
    }
  };

  const handleCommentBlur = async (questionId) => {
    const comment = responses[questionId]?.comment;
    
    setSaving(prev => ({ ...prev, [`${questionId}_comment`]: true }));

    try {
      await surveyAPI.saveResponse({
        question_id: questionId,
        score: responses[questionId]?.score || null,
        comment: comment || null
      });
      
      setTimeout(() => {
        setSaving(prev => ({ ...prev, [`${questionId}_comment`]: false }));
      }, 1000);
    } catch (error) {
      alert('Failed to save comment');
      setSaving(prev => ({ ...prev, [`${questionId}_comment`]: false }));
    }
  };

  const handleCommentChange = (questionId, value) => {
    const trimmed = value.trimStart().slice(0, 200);
    setResponses(prev => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        comment: trimmed
      }
    }));
  };

  if (loading) return <div>Loading...</div>;

  const scores = ['NA', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];

  return (
    <div>
      <Breadcrumb 
        items={[
          { label: 'Survey', link: '/survey' },
          { label: dimension }
        ]}
        customerCode={customerCode}
      />

      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{dimension}</h1>
        <p className="text-gray-600 mt-2">{questions.length} questions</p>
      </div>

      <div className="space-y-6">
        {questions.map((question) => {
          const response = responses[question.id] || {};
          const commentLength = response.comment?.length || 0;

          return (
            <div key={question.id} className="bg-white rounded-lg shadow p-6">
              <div className="mb-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <span className="text-sm text-gray-500">Question {question.question_id}</span>
                    <h3 className="text-lg font-semibold text-gray-900 mt-1">
                      {question.text}
                    </h3>
                  </div>
                  {saving[question.id] && (
                    <span className="text-sm text-blue-600">Saving...</span>
                  )}
                </div>
                {question.guidance && (
                  <p className="text-sm text-gray-600 italic mt-2">
                    {question.guidance}
                  </p>
                )}
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Score
                </label>
                <div className="flex flex-wrap gap-2">
                  {scores.map((score) => (
                    <button
                      key={score}
                      onClick={() => handleScoreChange(question.id, score)}
                      className={`px-4 py-2 rounded border ${
                        response.score === score
                          ? 'bg-encora-green text-white border-encora-green'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-encora-green'
                      }`}
                    >
                      {score}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Comments (Optional)
                  </label>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">
                      {commentLength}/200
                    </span>
                    {saving[`${question.id}_comment`] === false && (
                      <span className="text-green-600 text-sm">✓</span>
                    )}
                  </div>
                </div>
                <textarea
                  value={response.comment || ''}
                  onChange={(e) => handleCommentChange(question.id, e.target.value)}
                  onBlur={() => handleCommentBlur(question.id)}
                  className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-encora-green focus:border-transparent"
                  rows="3"
                  maxLength={200}
                  placeholder="Enter your comments here..."
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8">
        <button
          onClick={() => navigate('/survey')}
          className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}