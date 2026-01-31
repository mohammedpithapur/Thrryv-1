import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2, TrendingUp, Settings } from 'lucide-react';
import UserAvatar from '../components/UserAvatar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserProfile = () => {
  const params = useParams();
  const navigate = useNavigate();
  const userId = params.userId;
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/users/${userId}`)
      .then(response => {
        setUser(response.data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, [userId]);

  if (loading) {
    return <div data-testid="loading-spinner" className="flex items-center justify-center min-h-[400px]"><Loader2 className="animate-spin" size={32} /></div>;
  }

  if (!user) {
    return <div data-testid="user-not-found" className="text-center py-12"><p>User not found</p></div>;
  }

  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
  const isOwnProfile = currentUser.id === userId;

  return (
    <div data-testid="user-profile-page" className="max-w-5xl mx-auto px-6 py-8">
      <div className="bg-card border border-border p-8 rounded-sm mb-6">
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-6">
            <UserAvatar user={user} size="xl" />
            <div>
              <h1 className="playfair text-3xl font-bold mb-2">{user.username}</h1>
              <p className="text-muted-foreground">{user.email}</p>
              <p className="text-xs text-muted-foreground mt-1">
                Member since {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 justify-end mb-1">
              <TrendingUp size={20} className="text-green-600" />
              <span className="text-3xl font-bold jetbrains-mono">{user.reputation_score.toFixed(0)}</span>
            </div>
            <p className="text-sm text-muted-foreground mb-3">Reputation Score</p>
            {isOwnProfile && (
              <button
                onClick={() => navigate('/settings')}
                className="px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-sm text-sm font-medium flex items-center gap-2 ml-auto"
              >
                <Settings size={16} />
                Edit Profile
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 pt-6 border-t border-border">
          <div className="text-center p-4 bg-secondary rounded-sm">
            <p className="text-sm text-muted-foreground mb-1">Claims Posted</p>
            <p className="text-3xl font-bold jetbrains-mono">{user.contribution_stats.claims_posted}</p>
          </div>
          <div className="text-center p-4 bg-secondary rounded-sm">
            <p className="text-sm text-muted-foreground mb-1">Annotations</p>
            <p className="text-3xl font-bold jetbrains-mono">{user.contribution_stats.annotations_added}</p>
          </div>
          <div className="text-center p-4 bg-secondary rounded-sm">
            <p className="text-sm text-muted-foreground mb-1">Helpful Votes</p>
            <p className="text-3xl font-bold jetbrains-mono">{user.contribution_stats.helpful_votes_received}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <h2 className="playfair text-2xl font-semibold mb-4">Recent Claims</h2>
          {(!user.recent_claims || user.recent_claims.length === 0) ? (
            <p className="text-sm text-muted-foreground italic bg-secondary p-6 rounded-sm">No claims yet</p>
          ) : (
            <p className="text-sm text-muted-foreground bg-secondary p-6 rounded-sm">{user.recent_claims.length} claims posted</p>
          )}
        </div>

        <div>
          <h2 className="playfair text-2xl font-semibold mb-4">Recent Annotations</h2>
          {(!user.recent_annotations || user.recent_annotations.length === 0) ? (
            <p className="text-sm text-muted-foreground italic bg-secondary p-6 rounded-sm">No annotations yet</p>
          ) : (
            <p className="text-sm text-muted-foreground bg-secondary p-6 rounded-sm">{user.recent_annotations.length} annotations added</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
