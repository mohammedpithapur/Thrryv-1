import React from 'react';
import { TrendingUp, CheckCircle2, Sparkles, AlertCircle, Eye, Target, Lightbulb } from 'lucide-react';

const PostAnalysisModal = ({
  postData,
  evaluationResult,
  onPublish,
  onEdit,
  onDismiss,
  isLoading
}) => {
  const impactBoost = evaluationResult?.reputation_boost || 0;
  const qualifiesForBoost = evaluationResult?.qualifies_for_boost || false;

  // Calculate post score
  const calculatePostScore = () => {
    if (!evaluationResult) return 0;
    const clarity = evaluationResult.clarity_score || 0;
    const context = evaluationResult.originality_score || 0;
    const evidence = evaluationResult.evidentiary_value_score || 0;
    const relevance = evaluationResult.relevance_score || 0;
    
    // Average and scale to 0-15 range
    const avg = (clarity + context + evidence + relevance) / 4;
    return (avg / 100) * 15;
  };

  const postScore = calculatePostScore();
  const scoreColor = postScore >= 10 ? 'text-green-600 dark:text-green-400' : 
                    postScore >= 5 ? 'text-yellow-600 dark:text-yellow-400' : 
                    'text-orange-600 dark:text-orange-400';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-sm p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in duration-300">
        
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${
                qualifiesForBoost 
                  ? 'bg-green-100 dark:bg-green-900/30' 
                  : 'bg-blue-100 dark:bg-blue-900/30'
              }`}>
                {qualifiesForBoost ? (
                  <TrendingUp size={32} className="text-green-600 dark:text-green-400" />
                ) : (
                  <CheckCircle2 size={32} className="text-blue-600 dark:text-blue-400" />
                )}
              </div>
              <div>
                <h2 className="playfair text-2xl font-bold">
                  {qualifiesForBoost ? 'Excellent Content!' : 'Post Analysis Complete'}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {qualifiesForBoost 
                    ? 'Your post demonstrates strong clarity, evidence, and originality'
                    : 'Review your analysis below before publishing'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Original Post Preview */}
        <div className="bg-secondary rounded-sm p-4 mb-6 border border-border">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Original Post</p>
          <p className="text-sm line-clamp-4">{postData?.text}</p>
        </div>

        {/* Post Score - Prominent Display */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20 rounded-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Post Score</p>
                <div className="flex items-baseline gap-2">
                  <span className={`text-4xl font-bold ${scoreColor}`}>
                    {postScore.toFixed(1)}
                  </span>
                </div>
              </div>
              <Target size={32} className={`${scoreColor} opacity-60`} />
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              {postScore >= 10 ? 'High quality content' : 
               postScore >= 5 ? 'Good content with improvements possible' : 
               'Consider revisions below'}
            </p>
          </div>

          {/* Impact Boost */}
          {qualifiesForBoost && impactBoost > 0 ? (
            <div className="bg-gradient-to-br from-green-100 dark:from-green-900/30 to-green-50 dark:to-green-900/20 border border-green-200 dark:border-green-800 rounded-sm p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-green-700 dark:text-green-300 uppercase tracking-wide mb-1">Impact Boost</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-green-600 dark:text-green-400">
                      +{impactBoost.toFixed(1)}
                    </span>
                  </div>
                </div>
                <TrendingUp size={32} className="text-green-600 dark:text-green-400 opacity-60" />
              </div>
              <p className="text-xs text-green-700 dark:text-green-300 mt-3">
                Your post qualifies for an impact boost
              </p>
            </div>
          ) : (
            <div className="bg-gradient-to-br from-blue-100 dark:from-blue-900/30 to-blue-50 dark:to-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-sm p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-blue-700 dark:text-blue-300 uppercase tracking-wide mb-1">Impact Potential</p>
                  <p className="text-sm text-blue-700 dark:text-blue-300 font-medium">No boost this time</p>
                </div>
                <AlertCircle size={32} className="text-blue-600 dark:text-blue-400 opacity-60" />
              </div>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-3">
                Community engagement may increase your impact over time
              </p>
            </div>
          )}
        </div>

        {/* Scoring Breakdown - 3 Signals */}
        <div className="mb-6">
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <Sparkles size={16} />
            Content Signals Analysis
          </h3>
          
          <div className="grid grid-cols-3 gap-4">
            {/* Clarity Signal */}
            <div className="border border-border rounded-sm p-4 bg-secondary/30">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium">Clarity Signal</p>
                <Eye size={16} className="text-primary" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Score</span>
                  <span className="text-sm font-semibold">{evaluationResult?.clarity_score || 0}/100</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-1.5">
                  <div 
                    className="bg-blue-500 h-1.5 rounded-full" 
                    style={{ width: `${evaluationResult?.clarity_score || 0}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground pt-1">
                  How clearly your ideas are expressed
                </p>
              </div>
            </div>

            {/* Context Signal */}
            <div className="border border-border rounded-sm p-4 bg-secondary/30">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium">Context Signal</p>
                <Lightbulb size={16} className="text-primary" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Score</span>
                  <span className="text-sm font-semibold">{evaluationResult?.originality_score || 0}/100</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-1.5">
                  <div 
                    className="bg-purple-500 h-1.5 rounded-full" 
                    style={{ width: `${evaluationResult?.originality_score || 0}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground pt-1">
                  Contextual relevance and background
                </p>
              </div>
            </div>

            {/* Evidence Signal */}
            <div className="border border-border rounded-sm p-4 bg-secondary/30">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium">Evidence Signal</p>
                <Target size={16} className="text-primary" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Score</span>
                  <span className="text-sm font-semibold">{evaluationResult?.evidentiary_value_score || 0}/100</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-1.5">
                  <div 
                    className="bg-green-500 h-1.5 rounded-full" 
                    style={{ width: `${evaluationResult?.evidentiary_value_score || 0}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground pt-1">
                  Quality of supporting evidence
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Category Info */}
        {postData && (
          <div className="bg-secondary/50 rounded-sm p-4 mb-6 border border-border">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Category</p>
            {postData.category?.primary_path ? (
              <div className="flex flex-wrap items-center gap-1">
                {postData.category.primary_path.map((segment, idx) => (
                  <span key={idx} className="flex items-center">
                    <span className={`text-sm px-2 py-0.5 rounded ${
                      idx === 0 
                        ? 'bg-primary/10 text-primary font-medium' 
                        : 'bg-secondary text-foreground'
                    }`}>
                      {segment}
                    </span>
                    {idx < postData.category.primary_path.length - 1 && (
                      <span className="mx-1 text-muted-foreground">→</span>
                    )}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-sm bg-primary/10 text-primary px-3 py-1 rounded-full font-medium">
                {postData.domain}
              </span>
            )}
          </div>
        )}

        {/* Improvement Suggestions */}
        {!qualifiesForBoost && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-sm p-4 mb-6">
            <h4 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200 mb-2">Improvement Suggestions</h4>
            <ul className="text-xs text-yellow-700 dark:text-yellow-300 space-y-1">
              <li>• Add more specific examples or data to strengthen evidence</li>
              <li>• Improve clarity by breaking down complex ideas</li>
              <li>• Include sources or citations where applicable</li>
              <li>• Ensure relevance to the chosen category</li>
            </ul>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onEdit}
            disabled={isLoading}
            className="flex-1 px-6 py-3 border border-border text-foreground hover:bg-secondary rounded-sm font-medium transition-colors disabled:opacity-50"
          >
            ✏️ Edit Post
          </button>
          <button
            onClick={onPublish}
            disabled={isLoading}
            className="flex-1 px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium transition-colors disabled:opacity-50"
          >
            ✓ Publish Post
          </button>
        </div>
      </div>
    </div>
  );
};

export default PostAnalysisModal;
