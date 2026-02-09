import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import CredibilityScore from '../components/CredibilityScore';
import AnnotationCard from '../components/AnnotationCard';
import VideoPlayer from '../components/VideoPlayer';
import { Loader2, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClaimDetail = ({ user }) => {
  const params = useParams();
  const navigate = useNavigate();
  const claimId = params.postId || params.claimId;
  const [claim, setClaim] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [annotationText, setAnnotationText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [uploadingAnnotationMedia, setUploadingAnnotationMedia] = useState(false);
  const [annotationMedia, setAnnotationMedia] = useState([]);

  const loadData = useCallback(() => {
    axios.get(`${API}/claims/${claimId}`)
      .then(claimRes => {
        setClaim(claimRes.data);
        return axios.get(`${API}/claims/${claimId}/annotations`);
      })
      .then(annotationsRes => {
        setAnnotations(annotationsRes.data);
        setLoading(false);
      })
      .catch(() => {
        toast.error('Failed to load post');
        setLoading(false);
      });
  }, [claimId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!user) {
      toast.error('Please login');
      return;
    }
    if (!annotationText.trim()) return;

    setSubmitting(true);
    const token = localStorage.getItem('token');
    axios.post(
      `${API}/claims/${claimId}/annotations`,
      { 
        text: annotationText, 
        media_ids: annotationMedia.map(m => m.id) 
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((response) => {
        setAnnotationText('');
        setAnnotationMedia([]);
        toast.success('Annotation added (AI classified)');
        loadData();
        setSubmitting(false);
      })
      .catch(() => {
        toast.error('Failed to add annotation');
        setSubmitting(false);
      });
  };

  const handleAnnotationMediaUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      toast.error('File size must be less than 50MB');
      return;
    }

    setUploadingAnnotationMedia(true);
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

      setAnnotationMedia([...annotationMedia, response.data]);
      toast.success('Media uploaded');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload');
    } finally {
      setUploadingAnnotationMedia(false);
    }
  };

  const handleVote = (annotationId, helpful) => {
    if (!user) {
      toast.error('Please login to vote');
      return;
    }

    const token = localStorage.getItem('token');
    axios.post(
      `${API}/annotations/${annotationId}/vote?helpful=${helpful}`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then(() => {
        toast.success('Vote recorded');
        loadData();
      })
      .catch(err => {
        toast.error(err.response?.data?.detail || 'Failed to vote');
      });
  };

  if (loading) {
    return <div data-testid="loading-spinner" className="flex items-center justify-center min-h-[400px]"><Loader2 className="animate-spin" size={32} /></div>;
  }

  if (!claim) {
    return <div className="text-center py-12"><p>Post not found</p></div>;
  }

  const sortedAnnotations = [...annotations].sort(
    (a, b) => (b.helpful_votes || 0) - (a.helpful_votes || 0)
  );

  const hasMedia = claim.media && claim.media.length > 0;
  const firstMedia = hasMedia ? claim.media[0] : null;

  return (
    <div data-testid="claim-detail-page" className="max-w-7xl mx-auto px-6 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ArrowLeft size={20} />
        <span>Back</span>
      </button>

      {/* Post Card */}
      <div className="bg-card border border-border p-8 rounded-sm mb-6">
        <div className="mb-4">
          <p className="text-sm text-muted-foreground mb-2">{claim.domain} • {new Date(claim.created_at).toLocaleDateString()}</p>
          <h1 className="playfair text-3xl font-bold mb-4">{claim.text}</h1>
        </div>

        {firstMedia && (
          <div className="my-6">
            {firstMedia.file_type && firstMedia.file_type.startsWith('image/') && (
              <img
                src={`${API}/media/${firstMedia.id}`}
                alt="Post evidence"
                className="max-w-2xl w-full h-auto rounded-lg shadow-lg"
              />
            )}
            {firstMedia.file_type && firstMedia.file_type.startsWith('video/') && (
              <div className="max-w-2xl w-full mx-auto rounded-lg shadow-lg">
                <VideoPlayer
                  src={`${API}/media/${firstMedia.id}`}
                  autoPlay={false}
                  fit="contain"
                  screenFit={true}
                  className="w-full"
                />
              </div>
            )}
          </div>
        )}

        <CredibilityScore score={claim.credibility_score} />
        <div className="text-sm mt-4">
          <span className="text-muted-foreground">by </span>
          <button
            type="button"
            onClick={() => navigate(`/profile/${claim.author.id}`)}
            className="font-medium hover:text-primary transition-colors"
          >
            {claim.author.username}
          </button>
          <span className="text-muted-foreground"> (Impact: {claim.author.reputation_score.toFixed(0)})</span>
        </div>
      </div>

      {/* Add Annotation Form - Right under the post */}
      {user && (
        <form data-testid="annotation-form" onSubmit={handleSubmit} className="bg-card border border-border p-6 rounded-sm mb-8">
          <h2 className="playfair text-xl font-semibold mb-4">Add Your Annotation</h2>
          
          <p className="text-xs text-muted-foreground mb-3">
            AI will automatically classify your annotation as Support, Contradict, or Context.
          </p>

          <textarea
            data-testid="annotation-text-input"
            value={annotationText}
            onChange={(e) => setAnnotationText(e.target.value)}
            className="w-full px-4 py-3 border rounded-sm mb-4 focus:outline-none focus:ring-2 focus:ring-ring"
            rows="4"
            placeholder="Provide evidence, sources, or context for your annotation..."
          />
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Upload Evidence (Optional)</label>
            <input
              type="file"
              onChange={handleAnnotationMediaUpload}
              accept="image/*,video/*"
              disabled={uploadingAnnotationMedia}
              className="w-full px-4 py-2 border rounded-sm text-sm"
            />
            {uploadingAnnotationMedia && <p className="text-xs text-muted-foreground mt-2">Uploading...</p>}
            {annotationMedia.length > 0 && (
              <div className="mt-3 flex gap-2">
                {annotationMedia.map((media, idx) => (
                  <div key={idx} className="text-xs bg-secondary px-3 py-2 rounded-sm">
                    {media.file_name}
                  </div>
                ))}
              </div>
            )}
          </div>

          <button 
            type="submit" 
            disabled={submitting} 
            data-testid="submit-annotation-btn" 
            className="px-6 py-3 bg-primary text-primary-foreground rounded-sm hover:bg-primary/90 font-medium disabled:opacity-50"
          >
            {submitting ? 'Submitting...' : 'Add Annotation'}
          </button>
        </form>
      )}

      {!user && (
        <div className="bg-secondary border border-border p-6 rounded-sm mb-8 text-center">
          <p className="text-muted-foreground mb-3">Want to add evidence or context?</p>
          <button 
            onClick={() => navigate('/login')}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-sm hover:bg-primary/90 font-medium"
          >
            Sign In to Annotate
          </button>
        </div>
      )}

      {/* Community Annotations Header */}
      <div className="mb-6">
        <h2 className="playfair text-2xl font-bold mb-2">Community Annotations</h2>
        <p className="text-sm text-muted-foreground">
          {annotations.length} {annotations.length === 1 ? 'annotation' : 'annotations'} from the community
        </p>
      </div>

      {/* Annotations List */}
      <div className="space-y-3">
        {sortedAnnotations.length === 0 ? (
          <p className="text-sm text-muted-foreground italic">No annotations yet</p>
        ) : (
          sortedAnnotations.map(ann => (
            <AnnotationCard key={ann.id} annotation={ann} onVote={handleVote} canVote={!!user} />
          ))
        )}
      </div>
    </div>
  );
};

export default ClaimDetail;
