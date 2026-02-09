import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

const AnnotationCard = ({ annotation, onVote, canVote }) => {
  const navigate = useNavigate();
  const typeConfig = {
    support: { 
      label: 'Support', 
      borderClass: 'border-l-green-500', 
      bgClass: 'bg-green-50/80 dark:bg-green-950/30',
      textClass: 'text-green-700 dark:text-green-300',
      pillClass: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-200'
    },
    contradict: { 
      label: 'Contradict', 
      borderClass: 'border-l-red-500', 
      bgClass: 'bg-red-50/80 dark:bg-red-950/30',
      textClass: 'text-red-700 dark:text-red-300',
      pillClass: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200'
    },
    context: { 
      label: 'Context', 
      borderClass: 'border-l-indigo-500', 
      bgClass: 'bg-indigo-50/80 dark:bg-indigo-950/30',
      textClass: 'text-indigo-700 dark:text-indigo-300',
      pillClass: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-200'
    }
  };

  const config = typeConfig[annotation.annotation_type] || typeConfig.context;

  return (
    <div
      data-testid="annotation-card"
      className={`p-4 rounded-md border border-border shadow-sm ${config.borderClass} ${config.bgClass}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className={`text-[10px] font-semibold px-2 py-1 rounded-full ${config.pillClass}`}>
          {config.label}
        </span>
        <div className="text-[10px] text-muted-foreground">
          <button
            type="button"
            onClick={() => annotation.author?.id && navigate(`/profile/${annotation.author.id}`)}
            className="font-medium hover:text-primary transition-colors"
          >
            {annotation.author.username}
          </button>
        </div>
      </div>
      <p className="text-sm text-foreground leading-relaxed">{annotation.text}</p>

      <div className="flex items-center justify-between pt-3 mt-3 border-t border-border/60">
        <span className={`text-xs ${config.textClass}`}>Community feedback</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onVote(annotation.id, true)}
            disabled={!canVote}
            className="flex items-center gap-1 px-2.5 py-1 text-xs hover:bg-secondary rounded-sm disabled:opacity-50"
          >
            <ThumbsUp size={14} strokeWidth={1.5} />
            <span>{annotation.helpful_votes}</span>
          </button>
          <button
            onClick={() => onVote(annotation.id, false)}
            disabled={!canVote}
            className="flex items-center gap-1 px-2.5 py-1 text-xs hover:bg-secondary rounded-sm disabled:opacity-50"
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