import React from 'react';

const truthLabelConfig = {
  'True': {
    bg: '#ECFDF5',
    text: '#065F46',
    border: '#6EE7B7'
  },
  'Likely True': {
    bg: '#F0FDF4',
    text: '#166534',
    border: '#86EFAC'
  },
  'Mixed Evidence': {
    bg: '#FFFBEB',
    text: '#92400E',
    border: '#FCD34D'
  },
  'Uncertain': {
    bg: '#F3F4F6',
    text: '#374151',
    border: '#D1D5DB'
  },
  'Likely False': {
    bg: '#FEF2F2',
    text: '#991B1B',
    border: '#FCA5A5'
  },
  'False': {
    bg: '#450A0A',
    text: '#FEF2F2',
    border: '#991B1B'
  }
};

const TruthBadge = ({ label }) => {
  const config = truthLabelConfig[label] || truthLabelConfig['Uncertain'];
  
  return (
    <span
      data-testid="truth-badge"
      className="inline-block px-3 py-1 text-xs font-medium tracking-wide rounded-sm"
      style={{
        backgroundColor: config.bg,
        color: config.text,
        border: `1px solid ${config.border}`
      }}
    >
      {label}
    </span>
  );
};

export default TruthBadge;