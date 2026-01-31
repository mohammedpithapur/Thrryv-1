import React from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

const AnnotationCard = ({ annotation, onVote, canVote }) => {
  const typeConfig = {
    support: { 
      label: 'Support', 
      borderClass: 'border-l-green-500', 
      bgClass: 'bg-green-50 dark:bg-green-950/30',
      textClass: 'text-green-600 dark:text-green-400'
    },
    contradict: { 
      label: 'Contradict', 
      borderClass: 'border-l-red-500', 
      bgClass: 'bg-red-50 dark:bg-red-950/30',
      textClass: 'text-red-600 dark:text-red-400'
    },
    context: { 
      label: 'Context', 
      borderClass: 'border-l-indigo-500', 
      bgClass: 'bg-indigo-50 dark:bg-indigo-950/30',
      textClass: 'text-indigo-600 dark:text-indigo-400'
    }
  };

  const config = typeConfig[annotation.annotation_type] || typeConfig.context;

  return (
    <div
      data-testid="annotation-card"
      className={`p-4 rounded-sm border-l-4 mb-3 ${config.borderClass} ${config.bgClass}`}
    >
      <div className="mb-2">
        <span className={`text-xs font-medium ${config.textClass}`}>
          {config.label}
        </span>
        <p className="text-sm mt-1 text-foreground">{annotation.text}</p>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-border">
        <div className="text-xs text-muted-foreground">
          <span className="font-medium">{annotation.author.username}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onVote(annotation.id, true)}
            disabled={!canVote}
            className="flex items-center gap-1 px-2 py-1 text-xs hover:bg-secondary rounded-sm disabled:opacity-50"
          >
            <ThumbsUp size={14} strokeWidth={1.5} />
            <span>{annotation.helpful_votes}</span>
          </button>
          <button
            onClick={() => onVote(annotation.id, false)}
            disabled={!canVote}
            className="flex items-center gap-1 px-2 py-1 text-xs hover:bg-secondary rounded-sm disabled:opacity-50"
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