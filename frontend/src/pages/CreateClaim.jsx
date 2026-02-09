import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Upload, TrendingUp, Sparkles, Loader2, X, CheckCircle2, ArrowLeft } from 'lucide-react';
import PostAnalysisModal from '../components/PostAnalysisModal';

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
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [createdPostId, setCreatedPostId] = useState(null);
  const [postData, setPostData] = useState(null);

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
      toast.error('Please login to create a post');
      return;
    }

    // Strict 250 word limit enforcement
    if (wordCount > 250) {
      toast.error('Post must be 250 words or less. Please shorten your post.');
      return;
    }

    if (wordCount === 0) {
      toast.error('Please enter your post text');
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
      setCreatedPostId(response.data.id);
      setPostData(response.data);
      setEvaluationResult(evaluation);
      
      // Show analysis modal before publishing
      setShowAnalysis(true);
      setSubmitting(false);
      
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create post');
      setSubmitting(false);
    }
  };

  const handleEditPost = () => {
    setShowAnalysis(false);
    // User can edit the form
  };

  const handlePublishPost = () => {
    setShowAnalysis(false);
    if (createdPostId) {
      toast.success('Post published successfully!');
      navigate(`/posts/${createdPostId}`);
    } else {
      navigate('/feed');
    }
  };

  const handleDismissAnalysis = () => {
    setShowAnalysis(false);
    navigate('/feed');
  };

  return (
    <div data-testid="create-claim-page" className="max-w-3xl mx-auto px-4 md:px-6 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ArrowLeft size={20} />
        <span>Back</span>
      </button>

      <div className="mb-8">
        <h1 className="playfair text-3xl md:text-4xl font-bold tracking-tight mb-2">Create a Post</h1>
        <p className="text-muted-foreground">
          Share your perspective. Posts are analyzed by AI for clarity, context, and evidence quality.
        </p>
      </div>

      <form data-testid="create-post-form" onSubmit={handleSubmit} className="bg-card border border-border p-6 md:p-8 rounded-sm">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Post Text (max 250 words)</label>
          <textarea
            data-testid="post-text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background"
            rows="6"
            placeholder="Share your perspective here..."
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
            💡 Domain will be automatically classified by AI based on your post content and any media
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
          <label className="block text-sm font-medium mb-2">Supporting Media</label>
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
                Max 50MB. Supports images and short videos.
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
            <strong>Note:</strong> Posts can be deleted from your profile, but doing so will reverse any impact gained.
            The community will add annotations to verify or refute your post over time.
          </p>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-sm mb-6">
          <div className="flex items-start gap-3">
            <Sparkles size={20} className="text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">AI Post Analysis</p>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Before posting, your content will be analyzed for clarity, context, evidence quality, originality, and relevance.
                High-quality posts earn an impact boost. You'll see detailed feedback with visual analysis.
                This is separate from community verification.
              </p>
            </div>
          </div>
        </div>

        <button
          type="submit"
          data-testid="submit-post-btn"
          disabled={submitting || wordCount > 250 || !text.trim()}
          className="w-full px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Analyzing Your Post...
            </>
          ) : (
            'Review & Analyze Post'
          )}
        </button>
      </form>

      {/* Post Analysis Modal - Shows before publishing */}
      {showAnalysis && (
        <PostAnalysisModal
          postData={postData}
          evaluationResult={evaluationResult}
          onPublish={handlePublishPost}
          onEdit={handleEditPost}
          onDismiss={handleDismissAnalysis}
          isLoading={false}
        />
      )}
    </div>
  );
};

export default CreateClaim;
