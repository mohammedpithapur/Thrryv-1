import React from 'react';
import { Sparkles } from 'lucide-react';

const AiGeneratedBadge = ({ confidence }) => {
  return (
    <span
      data-testid="ai-generated-badge"
      className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium tracking-wide rounded-sm"
      style={{
        backgroundColor: '#F3E8FF',
        color: '#6B21A8',
        border: '1px solid #D8B4FE'
      }}
    >
      <Sparkles size={12} strokeWidth={1.5} />
      AI-Generated
      {confidence && <span className="ml-1">({(confidence * 100).toFixed(0)}%)</span>}
    </span>
  );
};

export default AiGeneratedBadge;