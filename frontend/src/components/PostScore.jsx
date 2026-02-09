import React from 'react';
import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts';

const PostScore = ({ score }) => {
  const data = [
    {
      name: 'Post Score',
      value: score,
      fill: score >= 65 ? '#10B981' : score >= 45 ? '#F59E0B' : '#EF4444'
    }
  ];

  return (
    <div data-testid="post-score" className="flex items-center gap-4">
      <div className="relative w-24 h-24">
        <RadialBarChart
          width={96}
          height={96}
          cx={48}
          cy={48}
          innerRadius={32}
          outerRadius={44}
          barSize={8}
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            angleAxisId={0}
            tick={false}
          />
          <RadialBar
            background
            dataKey="value"
            cornerRadius={8}
          />
        </RadialBarChart>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-semibold jetbrains-mono">{score.toFixed(0)}</span>
        </div>
      </div>
      <div>
        <p className="text-sm font-medium">Post Score</p>
        <p className="text-xs text-muted-foreground">
          Based on clarity, context, and evidence quality
        </p>
      </div>
    </div>
  );
};

export default PostScore;
