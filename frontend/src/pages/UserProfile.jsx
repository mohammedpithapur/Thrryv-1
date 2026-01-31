import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Loader2, TrendingUp } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserProfile = () => {
  const { userId } = useParams();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/users/${userId}`);
      setUser(response.data);
      setLoading(false);
    } catch (err) {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div data-testid="loading-spinner" className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  if (!user) {
    return (
      <div data-testid="user-not-found" className="text-center py-12">
        <p className="text-muted-foreground">User not found</p>
      </div>
    );
  }

  const radarData = [
    { subject: 'Claims', value: user.contribution_stats.claims_posted },
    { subject: 'Annotations', value: user.contribution_stats.annotations_added },
    { subject: 'Helpful Votes', value: user.contribution_stats.helpful_votes_received },
    { subject: 'Reputation', value: Math.min(user.reputation_score, 100) }
  ];

  return (
    <div data-testid="user-profile-page" className="max-w-5xl mx-auto px-6 py-8">
      <div className="bg-card border border-border p-8 rounded-sm mb-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="playfair text-3xl font-bold tracking-tight mb-2">{user.username}</h1>
            <p className="text-muted-foreground">{user.email}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Member since {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp size={20} className="text-green-600" />
              <span className="text-3xl font-bold jetbrains-mono">{user.reputation_score.toFixed(0)}</span>
            </div>
            <p className="text-sm text-muted-foreground">Reputation Score</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h2 className="text-lg font-semibold mb-4">Contribution Stats</h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-sm text-muted-foreground">Claims Posted</span>
                <span className="font-semibold jetbrains-mono">{user.contribution_stats.claims_posted}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-sm text-muted-foreground">Annotations Added</span>
                <span className="font-semibold jetbrains-mono">{user.contribution_stats.annotations_added}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-sm text-muted-foreground">Helpful Votes Received</span>
                <span className="font-semibold jetbrains-mono">{user.contribution_stats.helpful_votes_received}</span>
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold mb-4">Contribution Radar</h2>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 'auto']} />
                <Radar
                  name="Contributions"
                  dataKey="value"
                  stroke="#0F172A"
                  fill="#0F172A"
                  fillOpacity={0.3}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h2 className="playfair text-xl font-semibold mb-4">Recent Claims</h2>
          {user.recent_claims.length === 0 ? (
            <p className="text-sm text-muted-foreground">No claims yet</p>
          ) : (
            <div className="space-y-3">
              {user.recent_claims.map((claim) => (
                <div
                  key={claim.id}
                  className="border border-border p-4 rounded-sm hover:border-primary/50 transition-colors"
                >
                  <p className="text-sm line-clamp-2">{claim.text}</p>
                  <p className="text-xs text-muted-foreground mt-2">
                    {claim.domain} • {new Date(claim.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h2 className="playfair text-xl font-semibold mb-4">Recent Annotations</h2>
          {user.recent_annotations.length === 0 ? (
            <p className="text-sm text-muted-foreground">No annotations yet</p>
          ) : (
            <div className="space-y-3">
              {user.recent_annotations.map((ann) => (
                <div
                  key={ann.id}
                  className="border border-border p-4 rounded-sm hover:border-primary/50 transition-colors"
                >
                  <p className="text-sm line-clamp-2">{ann.text}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs font-medium">{ann.annotation_type}</span>
                    <span className="text-xs text-muted-foreground">
                      {ann.helpful_votes} helpful
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;