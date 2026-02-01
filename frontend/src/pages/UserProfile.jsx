import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Loader2, TrendingUp, Settings, ChevronDown, ChevronUp, Trash2, MessageSquare, ThumbsUp, ExternalLink } from 'lucide-react';
import UserAvatar from '../components/UserAvatar';
import TruthBadge from '../components/TruthBadge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserProfile = ({ currentUser }) => {
  const params = useParams();
  const navigate = useNavigate();
  const userId = params.userId;
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [allClaims, setAllClaims] = useState([]);
  const [allAnnotations, setAllAnnotations] = useState([]);
  const [showAllClaims, setShowAllClaims] = useState(false);
  const [showAllAnnotations, setShowAllAnnotations] = useState(false);
  const [loadingClaims, setLoadingClaims] = useState(false);
  const [loadingAnnotations, setLoadingAnnotations] = useState(false);

  useEffect(() => {
    axios.get(`${API}/users/${userId}`)
      .then(response => {
        setUser(response.data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [userId]);

  const loadAllClaims = async () => {
    if (allClaims.length > 0) {
      setShowAllClaims(!showAllClaims);
      return;
    }
    
    setLoadingClaims(true);
    try {
      const response = await axios.get(`${API}/users/${userId}/claims`);
      setAllClaims(response.data);
      setShowAllClaims(true);
    } catch (err) {
      toast.error('Failed to load claims');
    } finally {
      setLoadingClaims(false);
    }
  };

  const loadAllAnnotations = async () => {
    if (allAnnotations.length > 0) {
      setShowAllAnnotations(!showAllAnnotations);
      return;
    }
    
    setLoadingAnnotations(true);
    try {
      const response = await axios.get(`${API}/users/${userId}/annotations`);
      setAllAnnotations(response.data);
      setShowAllAnnotations(true);
    } catch (err) {
      toast.error('Failed to load annotations');
    } finally {
      setLoadingAnnotations(false);
    }
  };

  const handleDeleteClaim = async (claimId) => {
    if (!window.confirm('Are you sure you want to delete this claim? This will reverse any reputation gained.')) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(`${API}/claims/${claimId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.reputation_reversed > 0) {
        toast.success(`Claim deleted. ${response.data.reputation_reversed.toFixed(1)} reputation reversed.`);
      } else {
        toast.success('Claim deleted successfully.');
      }
      
      setAllClaims(prev => prev.filter(c => c.id !== claimId));
      // Update user stats
      setUser(prev => ({
        ...prev,
        contribution_stats: {
          ...prev.contribution_stats,
          claims_posted: Math.max(0, prev.contribution_stats.claims_posted - 1)
        },
        reputation_score: prev.reputation_score - (response.data.reputation_reversed || 0)
      }));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete claim');
    }
  };

  if (loading) {
    return <div data-testid="loading-spinner" className="flex items-center justify-center min-h-[400px]"><Loader2 className="animate-spin" size={32} /></div>;
  }

  if (!user) {
    return <div data-testid="user-not-found" className="text-center py-12"><p>User not found</p></div>;
  }

  const isOwnProfile = currentUser && currentUser.id === userId;

  return (
    <div data-testid="user-profile-page" className="max-w-5xl mx-auto px-4 md:px-6 py-8">
      <div className="bg-card border border-border p-6 md:p-8 rounded-sm mb-6">
        <div className="flex flex-col md:flex-row justify-between items-start gap-6 mb-6">
          <div className="flex items-center gap-4 md:gap-6">
            <UserAvatar user={user} size="xl" />
            <div>
              <h1 className="playfair text-2xl md:text-3xl font-bold mb-2">{user.username}</h1>
              <p className="text-muted-foreground text-sm">{user.email}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Member since {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="text-left md:text-right w-full md:w-auto">
            <div className="flex items-center gap-2 md:justify-end mb-1">
              <TrendingUp size={20} className="text-green-600" />
              <span className="text-3xl font-bold jetbrains-mono">{user.reputation_score.toFixed(1)}</span>
            </div>
            <p className="text-sm text-muted-foreground mb-3">Reputation Score</p>
            {isOwnProfile && (
              <button
                onClick={() => navigate('/settings')}
                className="px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-sm text-sm font-medium flex items-center gap-2"
              >
                <Settings size={16} />
                Edit Profile
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 md:gap-6 pt-6 border-t border-border">
          <div className="text-center p-3 md:p-4 bg-secondary rounded-sm">
            <p className="text-xs md:text-sm text-muted-foreground mb-1">Claims</p>
            <p className="text-xl md:text-3xl font-bold jetbrains-mono">{user.contribution_stats.claims_posted}</p>
          </div>
          <div className="text-center p-3 md:p-4 bg-secondary rounded-sm">
            <p className="text-xs md:text-sm text-muted-foreground mb-1">Annotations</p>
            <p className="text-xl md:text-3xl font-bold jetbrains-mono">{user.contribution_stats.annotations_added}</p>
          </div>
          <div className="text-center p-3 md:p-4 bg-secondary rounded-sm">
            <p className="text-xs md:text-sm text-muted-foreground mb-1">Helpful</p>
            <p className="text-xl md:text-3xl font-bold jetbrains-mono">{user.contribution_stats.helpful_votes_received}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Claims Section */}
        <div className="bg-card border border-border rounded-sm">
          <button
            onClick={loadAllClaims}
            data-testid="toggle-claims-btn"
            className="w-full p-6 flex items-center justify-between hover:bg-secondary/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <h2 className="playfair text-xl font-semibold">Claims</h2>
              <span className="text-sm text-muted-foreground">({user.contribution_stats.claims_posted})</span>
            </div>
            {loadingClaims ? (
              <Loader2 size={20} className="animate-spin" />
            ) : showAllClaims ? (
              <ChevronUp size={20} />
            ) : (
              <ChevronDown size={20} />
            )}
          </button>
          
          {showAllClaims && (
            <div className="border-t border-border">
              {allClaims.length === 0 ? (
                <p className="p-6 text-sm text-muted-foreground italic">No claims yet</p>
              ) : (
                <div className="divide-y divide-border max-h-[500px] overflow-y-auto">
                  {allClaims.map((claim) => (
                    <div key={claim.id} className="p-4 hover:bg-secondary/30 transition-colors">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <p 
                          className="text-sm line-clamp-2 cursor-pointer hover:text-primary"
                          onClick={() => navigate(`/claims/${claim.id}`)}
                        >
                          {claim.text}
                        </p>
                        <TruthBadge label={claim.truth_label} />
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span>{claim.domain}</span>
                          <span>•</span>
                          <span>{new Date(claim.created_at).toLocaleDateString()}</span>
                          {claim.baseline_evaluation?.reputation_boost > 0 && (
                            <>
                              <span>•</span>
                              <span className="text-green-600 dark:text-green-400 font-medium">
                                +{claim.baseline_evaluation.reputation_boost.toFixed(1)}
                              </span>
                            </>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => navigate(`/claims/${claim.id}`)}
                            className="p-1.5 hover:bg-secondary rounded-sm"
                            title="View claim"
                          >
                            <ExternalLink size={14} />
                          </button>
                          {isOwnProfile && (
                            <button
                              onClick={() => handleDeleteClaim(claim.id)}
                              className="p-1.5 hover:bg-red-100 dark:hover:bg-red-950/30 rounded-sm text-red-600"
                              title="Delete claim"
                            >
                              <Trash2 size={14} />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Annotations Section */}
        <div className="bg-card border border-border rounded-sm">
          <button
            onClick={loadAllAnnotations}
            data-testid="toggle-annotations-btn"
            className="w-full p-6 flex items-center justify-between hover:bg-secondary/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <h2 className="playfair text-xl font-semibold">Annotations</h2>
              <span className="text-sm text-muted-foreground">({user.contribution_stats.annotations_added})</span>
            </div>
            {loadingAnnotations ? (
              <Loader2 size={20} className="animate-spin" />
            ) : showAllAnnotations ? (
              <ChevronUp size={20} />
            ) : (
              <ChevronDown size={20} />
            )}
          </button>
          
          {showAllAnnotations && (
            <div className="border-t border-border">
              {allAnnotations.length === 0 ? (
                <p className="p-6 text-sm text-muted-foreground italic">No annotations yet</p>
              ) : (
                <div className="divide-y divide-border max-h-[500px] overflow-y-auto">
                  {allAnnotations.map((annotation) => (
                    <div 
                      key={annotation.id} 
                      className="p-4 hover:bg-secondary/30 transition-colors cursor-pointer"
                      onClick={() => navigate(`/claims/${annotation.claim_id}`)}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-sm ${
                          annotation.annotation_type === 'support' 
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                            : annotation.annotation_type === 'contradict'
                            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                            : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                        }`}>
                          {annotation.annotation_type}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(annotation.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm line-clamp-2 mb-2">{annotation.text}</p>
                      {annotation.claim_preview && (
                        <p className="text-xs text-muted-foreground line-clamp-1">
                          On: "{annotation.claim_preview}"
                        </p>
                      )}
                      <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <ThumbsUp size={12} />
                          {annotation.helpful_votes}
                        </span>
                        <span className="flex items-center gap-1">
                          <MessageSquare size={12} />
                          {annotation.not_helpful_votes}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
