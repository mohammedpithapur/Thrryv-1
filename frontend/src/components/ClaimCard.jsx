import React from 'react';
import { useNavigate } from 'react-router-dom';
import TruthBadge from './TruthBadge';
import UserAvatar from './UserAvatar';
import { MessageSquare } from 'lucide-react';

const ClaimCard = ({ claim }) => {
  const navigate = useNavigate();
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
  
  const firstMedia = claim.media && claim.media.length > 0 ? claim.media[0] : null;
  const hasImage = firstMedia && firstMedia.file_type && firstMedia.file_type.startsWith('image/');
  const hasVideo = firstMedia && firstMedia.file_type && firstMedia.file_type.startsWith('video/');

  return (
    <div
      data-testid="claim-card"
      onClick={() => navigate(`/claims/${claim.id}`)}
      className="border border-border bg-card p-6 hover:border-primary/50 transition-colors duration-200 cursor-pointer rounded-sm"
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-muted-foreground font-medium">{claim.domain}</span>
            <span className="text-xs text-muted-foreground">•</span>
            <span className="text-xs text-muted-foreground">
              {new Date(claim.created_at).toLocaleDateString()}
            </span>
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
          <span className="text-sm font-medium">{claim.author.username}</span>
          <span className="text-xs text-muted-foreground jetbrains-mono">
            Rep: {claim.author.reputation_score.toFixed(0)}
          </span>
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