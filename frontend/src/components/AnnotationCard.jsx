import React from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

const AnnotationCard = ({ annotation, onVote, canVote }) => {
  const typeConfig = {
    support: { label: 'Support', borderColor: '#10B981', bg: '#ECFDF5' },
    contradict: { label: 'Contradict', borderColor: '#EF4444', bg: '#FEF2F2' },
    context: { label: 'Context', borderColor: '#6366F1', bg: '#EEF2FF' }
  };

  const config = typeConfig[annotation.annotation_type] || typeConfig.context;

  return (
    <div
      data-testid="annotation-card"
      className="p-4 rounded-sm border-l-4 mb-3"
      style={{
        borderLeftColor: config.borderColor,
        backgroundColor: config.bg
      }}
    >
      <div className="mb-2">
        <span className="text-xs font-medium" style={{ color: config.borderColor }}>
          {config.label}
        </span>
        <p className="text-sm mt-1">{annotation.text}</p>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-slate-200">
        <div className="text-xs text-muted-foreground">
          <span className="font-medium">{annotation.author.username}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onVote(annotation.id, true)}
            disabled={!canVote}
            className="flex items-center gap-1 px-2 py-1 text-xs hover:bg-white rounded-sm disabled:opacity-50"
          >
            <ThumbsUp size={14} strokeWidth={1.5} />
            <span>{annotation.helpful_votes}</span>
          </button>
          <button
            onClick={() => onVote(annotation.id, false)}
            disabled={!canVote}
            className="flex items-center gap-1 px-2 py-1 text-xs hover:bg-white rounded-sm disabled:opacity-50"
          >
            <ThumbsDown size={14} strokeWidth={1.5} />
            <span>{annotation.not_helpful_votes}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AnnotationCard;