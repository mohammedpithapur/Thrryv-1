import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import TruthBadge from '../components/TruthBadge';
import CredibilityScore from '../components/CredibilityScore';
import AnnotationCard from '../components/AnnotationCard';
import AiGeneratedBadge from '../components/AiGeneratedBadge';
import { Loader2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ClaimDetail = ({ user }) => {
  const { claimId } = useParams();
  const [claim, setClaim] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [annotationText, setAnnotationText] = useState('');
  const [annotationType, setAnnotationType] = useState('support');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchClaimAndAnnotations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claimId]);

  const fetchClaimAndAnnotations = async () => {
    try {
      const [claimRes, annotationsRes] = await Promise.all([
        axios.get(`${API}/claims/${claimId}`),
        axios.get(`${API}/claims/${claimId}/annotations`)
      ]);
      setClaim(claimRes.data);
      setAnnotations(annotationsRes.data);
      setLoading(false);
    } catch (err) {
      toast.error('Failed to load claim');
      setLoading(false);
    }
  };

  const handleSubmitAnnotation = async (e) => {
    e.preventDefault();
    if (!user) {
      toast.error('Please login to add annotations');
      return;
    }

    if (!annotationText.trim()) {
      toast.error('Annotation text is required');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/claims/${claimId}/annotations`,
        {
          text: annotationText,
          annotation_type: annotationType,
          media_ids: []
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setAnnotationText('');
      toast.success('Annotation added successfully');
      fetchClaimAndAnnotations();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add annotation');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVote = async (annotationId, helpful) => {
    if (!user) {
      toast.error('Please login to vote');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/annotations/${annotationId}/vote`,
        { helpful },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      toast.success('Vote recorded');
      fetchClaimAndAnnotations();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to vote');
    }
  };

  if (loading) {
    return (
      <div data-testid="loading-spinner" className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  if (!claim) {
    return (
      <div data-testid="claim-not-found" className="text-center py-12">
        <AlertCircle className="mx-auto mb-4" size={48} />
        <p className="text-muted-foreground">Claim not found</p>
      </div>
    );
  }

  const supportAnnotations = annotations.filter(a => a.annotation_type === 'support');
  const contradictAnnotations = annotations.filter(a => a.annotation_type === 'contradict');
  const contextAnnotations = annotations.filter(a => a.annotation_type === 'context');

  return (
    <div data-testid="claim-detail-page" className="max-w-7xl mx-auto px-6 py-8">
      <div className="bg-card border border-border p-8 rounded-sm mb-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm text-muted-foreground font-medium">{claim.domain}</span>
              <span className="text-sm text-muted-foreground">•</span>
              <span className="text-sm text-muted-foreground">
                {new Date(claim.created_at).toLocaleDateString()}
              </span>
            </div>
            <h1 className="playfair text-3xl font-bold tracking-tight leading-tight mb-4">
              {claim.text}
            </h1>
            <div className="flex items-center gap-3 mb-4">
              <TruthBadge label={claim.truth_label} />
              <span className="text-sm text-muted-foreground">
                Confidence: <span className="jetbrains-mono">{claim.confidence_level}%</span>
              </span>
            </div>
          </div>
        </div>

        {claim.media && claim.media.length > 0 && (
          <div className="flex gap-3 mb-6">
            {claim.media.map((media, idx) => (
              <div key={idx} className="relative">
                {media.file_type?.startsWith('image/') && (
                  <img
                    src={`/api/media/${media.id}`}
                    alt="Claim evidence"
                    className="w-32 h-32 object-cover rounded-sm border border-border"
                  />
                )}
                {media.is_ai_generated && (
                  <div className="absolute -top-2 -right-2">
                    <AiGeneratedBadge confidence={media.ai_confidence} />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="border-t border-border pt-6">
          <CredibilityScore score={claim.credibility_score} />
        </div>

        <div className="flex items-center gap-4 mt-6 pt-6 border-t border-border">
          <span className="text-sm text-muted-foreground">Posted by</span>
          <span className="font-medium">{claim.author.username}</span>
          <span className="text-xs text-muted-foreground jetbrains-mono">
            Reputation: {claim.author.reputation_score.toFixed(0)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div>
          <h2 className="playfair text-xl font-semibold mb-4">Supporting Evidence</h2>
          {supportAnnotations.length === 0 ? (
            <p className="text-sm text-muted-foreground">No supporting evidence yet</p>
          ) : (
            supportAnnotations.map(ann => (
              <AnnotationCard
                key={ann.id}
                annotation={ann}
                onVote={handleVote}
                canVote={!!user}
              />
            ))
          )}
        </div>

        <div>
          <h2 className="playfair text-xl font-semibold mb-4">Contradictions</h2>
          {contradictAnnotations.length === 0 ? (
            <p className="text-sm text-muted-foreground">No contradictions yet</p>
          ) : (
            contradictAnnotations.map(ann => (
              <AnnotationCard
                key={ann.id}
                annotation={ann}
                onVote={handleVote}
                canVote={!!user}
              />
            ))
          )}
        </div>

        <div>
          <h2 className="playfair text-xl font-semibold mb-4">Context</h2>
          {contextAnnotations.length === 0 ? (
            <p className="text-sm text-muted-foreground">No context yet</p>
          ) : (
            contextAnnotations.map(ann => (
              <AnnotationCard
                key={ann.id}
                annotation={ann}
                onVote={handleVote}
                canVote={!!user}
              />
            ))
          )}
        </div>
      </div>

      {user && (
        <div className="bg-card border border-border p-6 rounded-sm">
          <h2 className="playfair text-xl font-semibold mb-4">Add Your Annotation</h2>
          <form data-testid="annotation-form" onSubmit={handleSubmitAnnotation}>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Annotation Type</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setAnnotationType('support')}
                  className={`px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                    annotationType === 'support'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                  data-testid="type-support-btn"
                >
                  Support
                </button>
                <button
                  type="button"
                  onClick={() => setAnnotationType('contradict')}
                  className={`px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                    annotationType === 'contradict'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                  data-testid="type-contradict-btn"
                >
                  Contradict
                </button>
                <button
                  type="button"
                  onClick={() => setAnnotationType('context')}
                  className={`px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                    annotationType === 'context'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                  }`}
                  data-testid="type-context-btn"
                >
                  Context
                </button>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Your Evidence or Context</label>
              <textarea
                data-testid="annotation-text-input"
                value={annotationText}
                onChange={(e) => setAnnotationText(e.target.value)}
                className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
                rows="4"
                placeholder="Provide evidence, sources, or context to support your annotation..."
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              data-testid="submit-annotation-btn"
              className="px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Submitting...' : 'Add Annotation'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default ClaimDetail;