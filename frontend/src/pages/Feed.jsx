import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ClaimCard from '../components/ClaimCard';
import { Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Feed = () => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchClaims();
  }, []);

  const fetchClaims = async () => {
    try {
      const response = await axios.get(`${API}/claims`);
      setClaims(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to load claims');
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

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  return (
    <div data-testid="feed-page" className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="playfair text-4xl font-bold tracking-tight mb-2">Recent Claims</h1>
        <p className="text-muted-foreground">
          Evidence-based fact-checking platform. Every claim is immutable and verified by the community.
        </p>
      </div>

      {claims.length === 0 ? (
        <div data-testid="no-claims" className="text-center py-12">
          <p className="text-muted-foreground">No claims yet. Be the first to post!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {claims.map((claim) => (
            <ClaimCard key={claim.id} claim={claim} />
          ))}
        </div>
      )}
    </div>
  );
};

export default Feed;