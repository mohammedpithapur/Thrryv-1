import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import UserAvatar from './UserAvatar';
import VideoPlayer from './VideoPlayer';
import { MessageSquare, TrendingUp, Trash2, MoreVertical } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction
} from './ui/alert-dialog';

const ClaimCard = ({ claim, currentUser, onDelete }) => {
  const navigate = useNavigate();
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
  const [showMenu, setShowMenu] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [commentsExpanded, setCommentsExpanded] = useState(false);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [comments, setComments] = useState([]);
  
  const firstMedia = claim.media && claim.media.length > 0 ? claim.media[0] : null;
  const hasImage = firstMedia && firstMedia.file_type && firstMedia.file_type.startsWith('image/');
  const hasVideo = firstMedia && firstMedia.file_type && firstMedia.file_type.startsWith('video/');
  
  const reputationBoost = claim.baseline_evaluation?.reputation_boost || 0;
  const isOwner = currentUser && claim.author.id === currentUser.id;
  const topAnnotations = claim.top_annotations || [];
  const annotationTypeConfig = {
    support: { label: 'Support', className: 'text-green-600 dark:text-green-400' },
    contradict: { label: 'Contradict', className: 'text-red-600 dark:text-red-400' },
    context: { label: 'Context', className: 'text-blue-600 dark:text-blue-400' }
  };
  
  // Get simple tag from category
  const categoryTag = claim.category?.primary_path?.[0] || claim.domain || 'General';

  const handleDelete = async (e) => {
    e.stopPropagation();
    setDeleting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(`${API}/claims/${claim.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.reputation_reversed > 0) {
        toast.success(`Post deleted. ${response.data.reputation_reversed.toFixed(1)} impact reversed.`);
      } else {
        toast.success('Post deleted successfully.');
      }
      
      if (onDelete) {
        onDelete(claim.id);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete post');
    } finally {
      setDeleting(false);
      setShowMenu(false);
      setShowDeleteDialog(false);
    }
  };

  const loadComments = async () => {
    if (commentsLoading) return;
    setCommentsLoading(true);
    try {
      const response = await axios.get(`${API}/claims/${claim.id}/annotations`);
      setComments(response.data || []);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load comments');
    } finally {
      setCommentsLoading(false);
    }
  };

  const handleToggleComments = async (e) => {
    e.stopPropagation();
    const nextExpanded = !commentsExpanded;
    setCommentsExpanded(nextExpanded);
    if (nextExpanded && comments.length === 0) {
      await loadComments();
    }
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!currentUser) {
      toast.error('Please login to comment');
      return;
    }
    if (!commentText.trim()) return;

    setSubmittingComment(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/claims/${claim.id}/annotations`,
        { text: commentText },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCommentText('');
      await loadComments();
      toast.success('Comment added (AI classified)');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add comment');
    } finally {
      setSubmittingComment(false);
    }
  };

  return (
    <div
      data-testid="claim-card"
      className="border border-border bg-card p-6 hover:border-primary/50 transition-colors duration-200 rounded-sm relative"
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
                onClick={(e) => {
                  e.stopPropagation();
                  setShowMenu(false);
                  setShowDeleteDialog(true);
                }}
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

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete post?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the post and reverse any impact gained.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 text-white hover:bg-red-700"
              disabled={deleting}
              onClick={handleDelete}
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          {/* Single Descriptive Tag */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20">
              {categoryTag}
            </span>
            <span className="text-xs text-muted-foreground">
              {new Date(claim.created_at).toLocaleDateString()}
            </span>
            {reputationBoost > 0 && (
              <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium">
                <TrendingUp size={12} />
                +{reputationBoost.toFixed(1)}
              </span>
            )}
          </div>
          <h3 className="playfair text-lg font-semibold tracking-tight leading-snug line-clamp-3">
            {claim.text}
          </h3>
        </div>
      </div>
      
      {firstMedia && (
        <div className="mb-3 -mx-6">
          {hasImage && (
            <img
              src={`${API}/media/${firstMedia.id}`}
              alt="Evidence"
              className="w-full h-auto max-h-[600px] object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          )}
          {hasVideo && (
            <div className="w-full">
              <VideoPlayer
                src={`${API}/media/${firstMedia.id}`}
                autoPlay={true}
                fit="contain"
                screenFit={true}
                className="w-full"
              />
            </div>
          )}
        </div>
      )}

      {topAnnotations.length > 0 && (
        <div className="mt-2 space-y-2">
          <p className="text-xs text-muted-foreground font-medium">Top comments</p>
          {topAnnotations.map((ann) => {
            const typeConfig = annotationTypeConfig[ann.annotation_type] || annotationTypeConfig.context;
            return (
              <div key={ann.id} className="rounded-md border border-border bg-secondary/30 px-3 py-2 shadow-sm">
                <div className="flex items-center gap-2 text-[11px] mb-1">
                  <span className={`font-semibold ${typeConfig.className}`}>{typeConfig.label}</span>
                  <span className="text-muted-foreground">by {ann.author?.username}</span>
                </div>
                <p className="text-xs text-foreground line-clamp-2 leading-relaxed">{ann.text}</p>
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-3 flex items-center justify-between text-xs">
        <button
          type="button"
          onClick={handleToggleComments}
          className="text-primary hover:underline"
        >
          {commentsExpanded ? 'Hide comments' : 'See more comments'}
        </button>
        <span className="text-muted-foreground">{claim.annotation_count} total</span>
      </div>

      {commentsExpanded && (
        <div className="mt-3 space-y-2">
          {commentsLoading ? (
            <p className="text-xs text-muted-foreground">Loading comments...</p>
          ) : comments.length === 0 ? (
            <p className="text-xs text-muted-foreground">No comments yet</p>
          ) : (
            comments.map((ann) => {
              const typeConfig = annotationTypeConfig[ann.annotation_type] || annotationTypeConfig.context;
              return (
                <div key={ann.id} className="rounded-md border border-border bg-secondary/30 px-3 py-2 shadow-sm">
                  <div className="flex items-center gap-2 text-[11px] mb-1">
                    <span className={`font-semibold ${typeConfig.className}`}>{typeConfig.label}</span>
                    <span className="text-muted-foreground">by {ann.author?.username}</span>
                  </div>
                  <p className="text-xs text-foreground leading-relaxed">{ann.text}</p>
                </div>
              );
            })
          )}
        </div>
      )}

      <form onSubmit={handleSubmitComment} className="mt-3 flex items-center gap-2">
        <input
          type="text"
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          placeholder="Add a comment..."
          className="flex-1 px-3 py-2 border border-border rounded-sm text-xs focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          type="submit"
          disabled={submittingComment}
          className="px-3 py-2 text-xs bg-primary text-primary-foreground rounded-sm hover:bg-primary/90 disabled:opacity-50"
        >
          {submittingComment ? 'Posting...' : 'Post'}
        </button>
      </form>
      
      <div className="flex items-center justify-between pt-3 border-t border-border">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/profile/${claim.author.id}`);
          }}
          className="flex items-center gap-2 text-left hover:text-primary transition-colors"
        >
          <UserAvatar user={claim.author} size="sm" />
          <div>
            <span className="text-sm font-medium block">{claim.author.username}</span>
            <span className="text-xs text-muted-foreground jetbrains-mono">
              Impact: {claim.author.reputation_score.toFixed(0)}
            </span>
          </div>
        </button>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 text-muted-foreground">
            <MessageSquare size={16} strokeWidth={1.5} />
            <span className="text-xs">{claim.annotation_count}</span>
          </div>
          <div className="text-xs jetbrains-mono">
            Post Score: {claim.credibility_score.toFixed(0)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClaimCard;
