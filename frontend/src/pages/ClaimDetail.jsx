import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import TruthBadge from '../components/TruthBadge';
import CredibilityScore from '../components/CredibilityScore';
import AnnotationCard from '../components/AnnotationCard';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClaimDetail = ({ user }) => {
  const params = useParams();
  const navigate = useNavigate();
  const claimId = params.claimId;
  const [claim, setClaim] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [annotationText, setAnnotationText] = useState('');
  const [annotationType, setAnnotationType] = useState('support');
  const [submitting, setSubmitting] = useState(false);
  const [uploadingAnnotationMedia, setUploadingAnnotationMedia] = useState(false);
  const [annotationMedia, setAnnotationMedia] = useState([]);

  useEffect(() => {
    loadData();
  }, [claimId]);

  const loadData = () => {
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
        toast.error('Failed to load claim');
        setLoading(false);
      });
  };

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
        annotation_type: annotationType, 
        media_ids: annotationMedia.map(m => m.id) 
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then(() => {
        setAnnotationText('');
        setAnnotationMedia([]);
        toast.success('Annotation added');
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
    return <div className="text-center py-12"><p>Claim not found</p></div>;
  }

  const supportAnnotations = annotations.filter(a => a.annotation_type === 'support');
  const contradictAnnotations = annotations.filter(a => a.annotation_type === 'contradict');
  const contextAnnotations = annotations.filter(a => a.annotation_type === 'context');

  const hasMedia = claim.media && claim.media.length > 0;
  const firstMedia = hasMedia ? claim.media[0] : null;

  return (
    <div data-testid="claim-detail-page" className="max-w-7xl mx-auto px-6 py-8">
      {/* Claim Card */}
      <div className="bg-card border border-border p-8 rounded-sm mb-6">
        <div className="mb-4">
          <p className="text-sm text-muted-foreground mb-2">{claim.domain} • {new Date(claim.created_at).toLocaleDateString()}</p>
          <h1 className="playfair text-3xl font-bold mb-4">{claim.text}</h1>
          <TruthBadge label={claim.truth_label} />
        </div>

        {firstMedia && (
          <div className="my-6">
            {firstMedia.file_type && firstMedia.file_type.startsWith('image/') && (
              <img
                src={`${API}/media/${firstMedia.id}`}
                alt="Claim evidence"
                className="max-w-2xl w-full h-auto rounded-sm border border-border shadow-sm"
              />
            )}
            {firstMedia.file_type && firstMedia.file_type.startsWith('video/') && (
              <video
                controls
                className="max-w-2xl w-full h-auto rounded-sm border border-border shadow-sm"
              >
                <source src={`${API}/media/${firstMedia.id}`} type={firstMedia.file_type} />
                Your browser does not support video playback.
              </video>
            )}
          </div>
        )}

        <CredibilityScore score={claim.credibility_score} />
        <p className="text-sm mt-4">by {claim.author.username} (Rep: {claim.author.reputation_score.toFixed(0)})</p>
      </div>

      {/* Add Annotation Form - Right under the post */}
      {user && (
        <form data-testid="annotation-form" onSubmit={handleSubmit} className="bg-card border border-border p-6 rounded-sm mb-8">
          <h2 className="playfair text-xl font-semibold mb-4">Add Your Annotation</h2>
          
          <div className="flex gap-2 mb-4">
            <button 
              type="button" 
              onClick={() => setAnnotationType('support')} 
              className={`px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                annotationType === 'support' 
                  ? 'bg-green-600 text-white' 
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
            >
              Support
            </button>
            <button 
              type="button" 
              onClick={() => setAnnotationType('contradict')} 
              className={`px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                annotationType === 'contradict' 
                  ? 'bg-red-600 text-white' 
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
            >
              Contradict
            </button>
            <button 
              type="button" 
              onClick={() => setAnnotationType('context')} 
              className={`px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                annotationType === 'context' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
            >
              Context
            </button>
          </div>

          <textarea
            data-testid="annotation-text-input"
            value={annotationText}
            onChange={(e) => setAnnotationText(e.target.value)}
            className="w-full px-4 py-3 border rounded-sm mb-4 focus:outline-none focus:ring-2 focus:ring-ring"
            rows="4"
            placeholder="Provide evidence, sources, or context to support your annotation..."
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

      {/* Annotations Grid - Three columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div>
          <h3 className="playfair text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-green-600 rounded-full"></span>
            Supporting Evidence
            <span className="text-sm text-muted-foreground font-normal">({supportAnnotations.length})</span>
          </h3>
          {supportAnnotations.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">No supporting evidence yet</p>
          ) : (
            <div>
              {supportAnnotations.map(ann => (
                <AnnotationCard key={ann.id} annotation={ann} onVote={handleVote} canVote={!!user} />
              ))}
            </div>
          )}
        </div>

        <div>
          <h3 className="playfair text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-red-600 rounded-full"></span>
            Contradictions
            <span className="text-sm text-muted-foreground font-normal">({contradictAnnotations.length})</span>
          </h3>
          {contradictAnnotations.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">No contradictions yet</p>
          ) : (
            <div>
              {contradictAnnotations.map(ann => (
                <AnnotationCard key={ann.id} annotation={ann} onVote={handleVote} canVote={!!user} />
              ))}
            </div>
          )}
        </div>

        <div>
          <h3 className="playfair text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-blue-600 rounded-full"></span>
            Context
            <span className="text-sm text-muted-foreground font-normal">({contextAnnotations.length})</span>
          </h3>
          {contextAnnotations.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">No context yet</p>
          ) : (
            <div>
              {contextAnnotations.map(ann => (
                <AnnotationCard key={ann.id} annotation={ann} onVote={handleVote} canVote={!!user} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClaimDetail;
