import React from 'react';
import { useNavigate } from 'react-router-dom';
import TruthBadge from './TruthBadge';
import AiGeneratedBadge from './AiGeneratedBadge';
import { MessageSquare } from 'lucide-react';

const ClaimCard = ({ claim }) => {
  const navigate = useNavigate();

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
      
      {claim.media && claim.media.length > 0 && (
        <div className="flex gap-2 mb-3">
          {claim.media.slice(0, 3).map((media, idx) => (
            <div key={idx} className="relative">
              {media.file_type?.startsWith('image/') && (
                <img
                  src={`/api/media/${media.id}`}
                  alt="Evidence"
                  className="w-16 h-16 object-cover rounded-sm border border-border"
                />
              )}
              {media.is_ai_generated && (
                <div className="absolute -top-1 -right-1">
                  <AiGeneratedBadge />
                </div>
              )}
            </div>
          ))}
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