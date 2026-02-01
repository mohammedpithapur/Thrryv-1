import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Upload, TrendingUp, Sparkles } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateClaim = ({ user }) => {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [confidenceLevel, setConfidenceLevel] = useState(50);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [uploadedMedia, setUploadedMedia] = useState([]);
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [showEvaluation, setShowEvaluation] = useState(false);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      toast.error('File size must be less than 50MB');
      return;
    }

    setUploading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/media/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`
        }
      });

      setUploadedMedia([...uploadedMedia, response.data]);
      toast.success('Media uploaded successfully');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload media');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!user) {
      toast.error('Please login to create a claim');
      return;
    }

    if (text.length > 250) {
      toast.error('Claim text must be 250 words or less');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/claims`,
        {
          text,
          confidence_level: confidenceLevel,
          media_ids: uploadedMedia.map(m => m.id)
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const evaluation = response.data.baseline_evaluation;
      setEvaluationResult(evaluation);
      
      if (evaluation && evaluation.qualifies_for_boost && evaluation.reputation_boost > 0) {
        setShowEvaluation(true);
        toast.success(
          `Claim created! +${evaluation.reputation_boost.toFixed(1)} reputation boost!`,
          { duration: 5000 }
        );
        // Wait to show evaluation before navigating
        setTimeout(() => {
          navigate(`/claims/${response.data.id}`);
        }, 3000);
      } else {
        toast.success(`Claim created! AI classified as: ${response.data.domain} | Truth: ${response.data.truth_label}`);
        navigate(`/claims/${response.data.id}`);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create claim');
    } finally {
      setSubmitting(false);
    }
  };

  const wordCount = text.trim().split(/\s+/).filter(w => w).length;

  return (
    <div data-testid="create-claim-page" className="max-w-3xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="playfair text-4xl font-bold tracking-tight mb-2">Create a Claim</h1>
        <p className="text-muted-foreground">
          Post a factual assertion. Claims are immutable once created. Be clear and concise.
        </p>
      </div>

      <form data-testid="create-claim-form" onSubmit={handleSubmit} className="bg-card border border-border p-8 rounded-sm">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Claim Text (max 250 words)</label>
          <textarea
            data-testid="claim-text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
            rows="6"
            placeholder="Enter your factual claim here..."
            required
          />
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-muted-foreground">
              {wordCount} / 250 words
            </span>
            {wordCount > 250 && (
              <span className="text-xs text-destructive">Exceeds word limit</span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            💡 Domain will be automatically classified by AI based on your claim content
          </p>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Your Confidence Level: {confidenceLevel}%
          </label>
          <input
            data-testid="confidence-slider"
            type="range"
            min="0"
            max="100"
            value={confidenceLevel}
            onChange={(e) => setConfidenceLevel(parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>No confidence</span>
            <span>Absolutely certain</span>
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Supporting Media (Optional)</label>
          <div className="border-2 border-dashed border-border rounded-sm p-6 text-center">
            <input
              type="file"
              id="file-upload"
              data-testid="file-upload-input"
              onChange={handleFileUpload}
              accept="image/*,video/*"
              className="hidden"
              disabled={uploading}
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center gap-2"
            >
              <Upload size={32} className="text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {uploading ? 'Uploading...' : 'Click to upload images or videos (max 50MB)'}
              </span>
            </label>
          </div>

          {uploadedMedia.length > 0 && (
            <div className="mt-4 grid grid-cols-3 gap-3">
              {uploadedMedia.map((media, idx) => (
                <div key={idx} className="relative border border-border rounded-sm p-2">
                  <p className="text-xs truncate">{media.file_name}</p>
                  {media.is_ai_generated && (
                    <span className="text-xs text-purple-600 mt-1 block">
                      AI-Generated ({(media.ai_confidence * 100).toFixed(0)}%)
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-secondary p-4 rounded-sm mb-6">
          <p className="text-sm text-muted-foreground">
            <strong>Note:</strong> Claims are immutable. Once posted, they cannot be edited or deleted.
            The community will add annotations to verify or refute your claim.
          </p>
        </div>

        <button
          type="submit"
          data-testid="submit-claim-btn"
          disabled={submitting || wordCount > 250 || !text.trim()}
          className="w-full px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? 'Creating & Evaluating...' : 'Post Claim'}
        </button>
      </form>

      {/* AI Evaluation Result Modal */}
      {showEvaluation && evaluationResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-sm p-8 max-w-lg w-full animate-in fade-in zoom-in duration-300">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
                <Sparkles size={32} className="text-green-600 dark:text-green-400" />
              </div>
              <h2 className="playfair text-2xl font-bold mb-2">Content Evaluated!</h2>
              <p className="text-muted-foreground">Your contribution adds value to the platform</p>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-sm p-4 mb-6">
              <div className="flex items-center justify-center gap-3">
                <TrendingUp size={24} className="text-green-600 dark:text-green-400" />
                <span className="text-3xl font-bold text-green-600 dark:text-green-400">
                  +{evaluationResult.reputation_boost?.toFixed(1)}
                </span>
                <span className="text-green-700 dark:text-green-300">Reputation</span>
              </div>
            </div>

            <div className="space-y-3 mb-6">
              <h3 className="font-semibold text-sm">Content Quality Scores</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Clarity</span>
                  <span className="font-medium">{evaluationResult.clarity_score}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Originality</span>
                  <span className="font-medium">{evaluationResult.originality_score}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Relevance</span>
                  <span className="font-medium">{evaluationResult.relevance_score}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Effort</span>
                  <span className="font-medium">{evaluationResult.effort_score}/100</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Evidentiary Value</span>
                  <span className="font-medium">{evaluationResult.evidentiary_value_score}/100</span>
                </div>
                {evaluationResult.media_value_score !== null && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Media Value</span>
                    <span className="font-medium">{evaluationResult.media_value_score}/100</span>
                  </div>
                )}
              </div>
            </div>

            <p className="text-xs text-muted-foreground text-center mb-4">
              {evaluationResult.evaluation_summary}
            </p>

            <p className="text-xs text-center text-muted-foreground">
              Redirecting to your claim...
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default CreateClaim;