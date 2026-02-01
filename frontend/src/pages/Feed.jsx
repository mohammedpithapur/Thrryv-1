import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ClaimCard from '../components/ClaimCard';
import { Loader2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Feed = ({ user }) => {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('recent');

  useEffect(() => {
    loadClaims();
  }, []);

  const loadClaims = () => {
    axios.get(`${API}/claims`)
      .then(response => {
        setClaims(response.data);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load claims');
        setLoading(false);
      });
  };

  const handleDeleteClaim = (claimId) => {
    setClaims(prev => prev.filter(c => c.id !== claimId));
  };

  const getFilteredClaims = () => {
    if (activeTab === 'recent') {
      return claims;
    } else if (activeTab === 'debated') {
      return claims.filter(claim => 
        claim.annotation_count >= 3 && 
        (claim.truth_label === 'Mixed Evidence' || claim.credibility_score >= 30 && claim.credibility_score <= 70)
      );
    } else if (activeTab === 'uncertain') {
      return claims.filter(claim => 
        claim.truth_label === 'Uncertain' || claim.annotation_count < 3
      );
    }
    return claims;
  };

  const filteredClaims = getFilteredClaims();

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
    <div data-testid="feed-page" className="max-w-7xl mx-auto px-4 md:px-6 py-8">
      <div className="mb-8">
        <h1 className="playfair text-3xl md:text-4xl font-bold tracking-tight mb-2">Claims Feed</h1>
        <p className="text-muted-foreground text-sm md:text-base">
          Evidence-based fact-checking platform. Every claim is immutable and verified by the community.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-border mb-8 overflow-x-auto">
        <div className="flex gap-4 md:gap-8 min-w-max">
          <button
            data-testid="tab-recent"
            onClick={() => setActiveTab('recent')}
            className={`pb-4 px-2 font-medium transition-colors border-b-2 whitespace-nowrap ${
              activeTab === 'recent'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Recent
            <span className="ml-2 text-xs">{claims.length}</span>
          </button>
          <button
            data-testid="tab-debated"
            onClick={() => setActiveTab('debated')}
            className={`pb-4 px-2 font-medium transition-colors border-b-2 whitespace-nowrap ${
              activeTab === 'debated'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Debated
            <span className="ml-2 text-xs">
              {claims.filter(c => c.annotation_count >= 3 && (c.truth_label === 'Mixed Evidence' || (c.credibility_score >= 30 && c.credibility_score <= 70))).length}
            </span>
          </button>
          <button
            data-testid="tab-uncertain"
            onClick={() => setActiveTab('uncertain')}
            className={`pb-4 px-2 font-medium transition-colors border-b-2 whitespace-nowrap ${
              activeTab === 'uncertain'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Uncertain
            <span className="ml-2 text-xs">
              {claims.filter(c => c.truth_label === 'Uncertain' || c.annotation_count < 3).length}
            </span>
          </button>
        </div>
      </div>

      {filteredClaims.length === 0 ? (
        <div data-testid="no-claims" className="text-center py-12 bg-secondary rounded-sm">
          <p className="text-muted-foreground">
            {activeTab === 'recent' && 'No claims yet. Be the first to post!'}
            {activeTab === 'debated' && 'No debated claims yet. Claims with 3+ annotations and mixed evidence appear here.'}
            {activeTab === 'uncertain' && 'No uncertain claims. Claims with few annotations or unclear evidence appear here.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {filteredClaims.map((claim) => (
            <ClaimCard 
              key={claim.id} 
              claim={claim} 
              currentUser={user}
              onDelete={handleDeleteClaim}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Feed;
