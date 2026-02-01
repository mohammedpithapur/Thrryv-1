import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Upload, TrendingUp, Sparkles, Loader2, X, CheckCircle2 } from 'lucide-react';

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
  const [createdClaimId, setCreatedClaimId] = useState(null);
  const [claimData, setClaimData] = useState(null);

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

  const wordCount = text.trim().split(/\s+/).filter(w => w).length;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!user) {
      toast.error('Please login to create a claim');
      return;
    }

    // Strict 250 word limit enforcement
    if (wordCount > 250) {
      toast.error('Claim must be 250 words or less. Please shorten your claim.');
      return;
    }

    if (wordCount === 0) {
      toast.error('Please enter your claim text');
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
      setCreatedClaimId(response.data.id);
      setClaimData(response.data);
      setEvaluationResult(evaluation);
      
      // Always show the evaluation modal
      setShowEvaluation(true);
      
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create claim');
      setSubmitting(false);
    }
  };

  const handleDismissEvaluation = () => {
    setShowEvaluation(false);
    if (createdClaimId) {
      navigate(`/claims/${createdClaimId}`);
    } else {
      navigate('/feed');
    }
  };

  return (
    <div data-testid="create-claim-page" className="max-w-3xl mx-auto px-4 md:px-6 py-8">
      <div className="mb-8">
        <h1 className="playfair text-3xl md:text-4xl font-bold tracking-tight mb-2">Create a Claim</h1>
        <p className="text-muted-foreground">
          Post a factual assertion. Claims are evaluated by AI for quality and verified by the community.
        </p>
      </div>

      <form data-testid="create-claim-form" onSubmit={handleSubmit} className="bg-card border border-border p-6 md:p-8 rounded-sm">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Claim Text (max 250 words)</label>
          <textarea
            data-testid="claim-text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background"
            rows="6"
            placeholder="Enter your factual claim here..."
            required
          />
          <div className="flex justify-between items-center mt-2">
            <span className={`text-xs ${wordCount > 250 ? 'text-destructive font-medium' : 'text-muted-foreground'}`}>
              {wordCount} / 250 words
            </span>
            {wordCount > 250 && (
              <span className="text-xs text-destructive font-medium">Exceeds word limit</span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            💡 Domain will be automatically classified by AI based on your claim content and any media
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
              data-testid="media-upload-input"
              type="file"
              accept="image/*,video/*"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
              id="media-upload"
            />
            <label
              htmlFor="media-upload"
              className="cursor-pointer flex flex-col items-center gap-2"
            >
              <Upload size={32} className="text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {uploading ? 'Uploading...' : 'Click to upload image or video'}
              </span>
              <span className="text-xs text-muted-foreground">
                Max 50MB. Images and videos up to 30 seconds.
              </span>
            </label>
          </div>

          {uploadedMedia.length > 0 && (
            <div className="mt-4 space-y-2">
              {uploadedMedia.map((media, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-secondary rounded-sm">
                  <span className="text-sm truncate flex-1">{media.file_type}</span>
                  {media.is_ai_generated && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
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
            <strong>Note:</strong> Claims can be deleted from your profile, but doing so will reverse any reputation gained.
            The community will add annotations to verify or refute your claim over time.
          </p>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-sm mb-6">
          <div className="flex items-start gap-3">
            <Sparkles size={20} className="text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">AI Reputation Evaluator</p>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Your post will be evaluated for clarity, originality, relevance, effort, and evidentiary value.
                High-quality contributions earn a reputation boost (+5 to +15 points). Low-value posts receive
                no penalty. This is separate from community verification.
              </p>
            </div>
          </div>
        </div>

        <button
          type="submit"
          data-testid="submit-claim-btn"
          disabled={submitting || wordCount > 250 || !text.trim()}
          className="w-full px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Analyzing & Creating...
            </>
          ) : (
            'Post Claim'
          )}
        </button>
      </form>

      {/* AI Evaluation Result Modal - Shows for ALL claims */}
      {showEvaluation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-sm p-6 md:p-8 max-w-lg w-full max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in duration-300">
            {/* Header */}
            <div className="text-center mb-6">
              <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
                evaluationResult?.qualifies_for_boost 
                  ? 'bg-green-100 dark:bg-green-900/30' 
                  : 'bg-blue-100 dark:bg-blue-900/30'
              }`}>
                {evaluationResult?.qualifies_for_boost ? (
                  <TrendingUp size={32} className="text-green-600 dark:text-green-400" />
                ) : (
                  <CheckCircle2 size={32} className="text-blue-600 dark:text-blue-400" />
                )}
              </div>
              <h2 className="playfair text-2xl font-bold mb-2">
                {evaluationResult?.qualifies_for_boost ? 'Great Contribution!' : 'Claim Created!'}
              </h2>
              <p className="text-muted-foreground">
                {evaluationResult?.qualifies_for_boost 
                  ? 'Your content adds significant value to the platform'
                  : 'Your claim has been posted and is now live'}
              </p>
            </div>

            {/* Domain Classification */}
            {claimData && (
              <div className="bg-secondary p-4 rounded-sm mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Domain</span>
                  <span className="text-sm bg-primary/10 text-primary px-3 py-1 rounded-full font-medium">
                    {claimData.domain}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Initial Assessment</span>
                  <span className={`text-sm px-3 py-1 rounded-full font-medium ${
                    claimData.truth_label === 'True' || claimData.truth_label === 'Likely True'
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                      : claimData.truth_label === 'False' || claimData.truth_label === 'Likely False'
                      ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                  }`}>
                    {claimData.truth_label}
                  </span>
                </div>
              </div>
            )}

            {/* Reputation Boost Section */}
            {evaluationResult?.qualifies_for_boost && evaluationResult?.reputation_boost > 0 ? (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-sm p-4 mb-6">
                <div className="flex items-center justify-center gap-3 mb-3">
                  <TrendingUp size={24} className="text-green-600 dark:text-green-400" />
                  <span className="text-3xl font-bold text-green-600 dark:text-green-400">
                    +{evaluationResult.reputation_boost?.toFixed(1)}
                  </span>
                  <span className="text-green-700 dark:text-green-300 font-medium">Reputation</span>
                </div>
              </div>
            ) : (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-sm p-4 mb-6">
                <p className="text-sm text-blue-800 dark:text-blue-200 text-center">
                  <strong>No reputation boost this time.</strong> Your claim is still valuable! Community annotations over time may increase your reputation.
                </p>
              </div>
            )}

            {/* Quality Scores */}
            {evaluationResult && (
              <div className="space-y-4 mb-6">
                <h3 className="font-semibold text-sm">Content Quality Analysis</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex justify-between items-center p-2 bg-secondary/50 rounded-sm">
                    <span className="text-muted-foreground">Clarity</span>
                    <span className="font-medium">{evaluationResult.clarity_score || 0}/100</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-secondary/50 rounded-sm">
                    <span className="text-muted-foreground">Originality</span>
                    <span className="font-medium">{evaluationResult.originality_score || 0}/100</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-secondary/50 rounded-sm">
                    <span className="text-muted-foreground">Relevance</span>
                    <span className="font-medium">{evaluationResult.relevance_score || 0}/100</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-secondary/50 rounded-sm">
                    <span className="text-muted-foreground">Effort</span>
                    <span className="font-medium">{evaluationResult.effort_score || 0}/100</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-secondary/50 rounded-sm">
                    <span className="text-muted-foreground">Evidence Value</span>
                    <span className="font-medium">{evaluationResult.evidentiary_value_score || 0}/100</span>
                  </div>
                  {evaluationResult.media_value_score !== null && evaluationResult.media_value_score !== undefined && (
                    <div className="flex justify-between items-center p-2 bg-secondary/50 rounded-sm">
                      <span className="text-muted-foreground">Media Value</span>
                      <span className="font-medium">{evaluationResult.media_value_score}/100</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Explanation */}
            <div className="bg-secondary/50 border border-border rounded-sm p-4 mb-6">
              <h4 className="font-semibold text-sm mb-2">
                {evaluationResult?.qualifies_for_boost ? 'Why did you earn this boost?' : 'How reputation works'}
              </h4>
              <p className="text-xs text-muted-foreground">
                {evaluationResult?.qualifies_for_boost 
                  ? evaluationResult.evaluation_summary || 'Your content was evaluated for clarity, originality, relevance, effort, and evidentiary value. Posts that score above average across these criteria earn reputation rewards. This is separate from community verification, which happens over time through annotations.'
                  : 'Reputation boosts are awarded to posts that demonstrate exceptional clarity, originality, relevance, effort, and evidentiary value. Your claim may still earn reputation through community engagement - when others vote your annotations as helpful or when your claims age well over time.'}
              </p>
            </div>

            {/* OK Button */}
            <button
              onClick={handleDismissEvaluation}
              data-testid="dismiss-evaluation-btn"
              className="w-full px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium"
            >
              OK, View My Claim
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CreateClaim;
