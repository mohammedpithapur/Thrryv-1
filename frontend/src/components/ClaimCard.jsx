import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import TruthBadge from './TruthBadge';
import UserAvatar from './UserAvatar';
import { MessageSquare, TrendingUp, Trash2, MoreVertical } from 'lucide-react';

const ClaimCard = ({ claim, currentUser, onDelete }) => {
  const navigate = useNavigate();
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
  const [showMenu, setShowMenu] = useState(false);
  const [deleting, setDeleting] = useState(false);
  
  const firstMedia = claim.media && claim.media.length > 0 ? claim.media[0] : null;
  const hasImage = firstMedia && firstMedia.file_type && firstMedia.file_type.startsWith('image/');
  const hasVideo = firstMedia && firstMedia.file_type && firstMedia.file_type.startsWith('video/');
  
  const reputationBoost = claim.baseline_evaluation?.reputation_boost || 0;
  const isOwner = currentUser && claim.author.id === currentUser.id;

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this claim? This will reverse any reputation gained.')) {
      return;
    }
    
    setDeleting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(`${API}/claims/${claim.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.reputation_reversed > 0) {
        toast.success(`Claim deleted. ${response.data.reputation_reversed.toFixed(1)} reputation reversed.`);
      } else {
        toast.success('Claim deleted successfully.');
      }
      
      if (onDelete) {
        onDelete(claim.id);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete claim');
    } finally {
      setDeleting(false);
      setShowMenu(false);
    }
  };

  return (
    <div
      data-testid="claim-card"
      onClick={() => navigate(`/claims/${claim.id}`)}
      className="border border-border bg-card p-6 hover:border-primary/50 transition-colors duration-200 cursor-pointer rounded-sm relative"
    >
      {/* Options Menu for Owner */}
      {isOwner && (
        <div className="absolute top-4 right-4 z-10">
          <button
            data-testid="claim-menu-btn"
            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
            className="p-1.5 hover:bg-secondary rounded-sm transition-colors"
          >
            <MoreVertical size={16} />
          </button>
          {showMenu && (
            <div className="absolute right-0 mt-1 bg-card border border-border rounded-sm shadow-lg py-1 min-w-[140px]">
              <button
                data-testid="delete-claim-btn"
                onClick={handleDelete}
                disabled={deleting}
                className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors"
              >
                <Trash2 size={14} />
                {deleting ? 'Deleting...' : 'Delete Post'}
              </button>
            </div>
          )}
        </div>
      )}

      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-muted-foreground font-medium">{claim.domain}</span>
            <span className="text-xs text-muted-foreground">•</span>
            <span className="text-xs text-muted-foreground">
              {new Date(claim.created_at).toLocaleDateString()}
            </span>
            {reputationBoost > 0 && (
              <>
                <span className="text-xs text-muted-foreground">•</span>
                <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium">
                  <TrendingUp size={12} />
                  +{reputationBoost.toFixed(1)}
                </span>
              </>
            )}
          </div>
          <h3 className="playfair text-lg font-semibold tracking-tight leading-snug line-clamp-3">
            {claim.text}
          </h3>
        </div>
        <TruthBadge label={claim.truth_label} />
      </div>
      
      {firstMedia && (
        <div className="mb-3">
          {hasImage && (
            <img
              src={`${API}/media/${firstMedia.id}`}
              alt="Evidence"
              className="w-full h-48 object-cover rounded-sm border border-border"
              onClick={(e) => e.stopPropagation()}
            />
          )}
          {hasVideo && (
            <video
              src={`${API}/media/${firstMedia.id}`}
              className="w-full h-48 object-cover rounded-sm border border-border"
              autoPlay
              muted
              loop
              playsInline
              onClick={(e) => e.stopPropagation()}
            />
          )}
        </div>
      )}
      
      <div className="flex items-center justify-between pt-3 border-t border-border">
        <div className="flex items-center gap-2">
          <UserAvatar user={claim.author} size="sm" />
          <div>
            <span className="text-sm font-medium block">{claim.author.username}</span>
            <span className="text-xs text-muted-foreground jetbrains-mono">
              Rep: {claim.author.reputation_score.toFixed(0)}
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-muted-foreground">
            <MessageSquare size={16} strokeWidth={1.5} />
            <span className="text-xs">{claim.annotation_count}</span>
          </div>
          <div className="text-xs jetbrains-mono">
            Score: {claim.credibility_score.toFixed(0)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClaimCard;
