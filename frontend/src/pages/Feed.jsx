import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ClaimCard from '../components/ClaimCard';
import { Loader2 } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { getApiData, getApiList, getApiErrorMessage } from '../lib/api';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Feed = ({ user }) => {
  const location = useLocation();
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('top');
  const tabList = [
    { key: 'top', label: 'Top' },
    { key: 'impact', label: 'Impact' },
    { key: 'recent', label: 'Recent' }
  ];
  const tabRefs = React.useRef([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Helper for retry logic
  async function fetchWithRetry(fn, retries = 6, delay = 2000) {
    let lastErr;
    for (let i = 0; i < retries; i++) {
      try {
        return await fn();
      } catch (err) {
        lastErr = err;
        await new Promise(res => setTimeout(res, delay));
      }
    }
    throw lastErr;
  }

  // Only load claims when user loading is complete (user !== undefined)
  useEffect(() => {
    // If user is still undefined (loading), do not load claims yet
    if (typeof user === 'undefined') return;
    loadClaims();
  }, [searchQuery, user]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const qParam = params.get('q');
    setSearchQuery(qParam || '');
  }, [location.search]);

  // Keyboard navigation for tabs
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['ArrowLeft', 'ArrowRight'].includes(e.key)) {
        const idx = tabList.findIndex(t => t.key === activeTab);
        let nextIdx = idx;
        if (e.key === 'ArrowLeft') nextIdx = (idx - 1 + tabList.length) % tabList.length;
        if (e.key === 'ArrowRight') nextIdx = (idx + 1) % tabList.length;
        setActiveTab(tabList[nextIdx].key);
        tabRefs.current[nextIdx]?.focus();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [activeTab]);

  const loadClaims = () => {
    setLoading(true);
    setError(null);

    const token = localStorage.getItem('token');
    const hasAuth = Boolean(token && user);
    const hasQuery = Boolean(searchQuery && searchQuery.trim().length > 0);

    if (!hasAuth) {
      fetchWithRetry(() => axios.get(`${API}/claims`, { timeout: 10000, params: { standard: true } }))
        .then(response => {
          setClaims(getApiList(response));
          setLoading(false);
        })
        .catch((err) => {
          const message = getApiErrorMessage(err, 'Failed to load posts');
          setError(message);
          setLoading(false);
        });
      return;
    }

    const headers = { Authorization: `Bearer ${token}` };
    if (hasQuery) {
      fetchWithRetry(() => axios.post(
        `${API}/discover`,
        {
          query: searchQuery,
          algorithm: 'relevance',
          diversity_preference: 0.35,
          limit: 20
        },
        { headers, timeout: 15000, params: { standard: true } }
      ))
        .then(response => {
          const data = getApiData(response);
          setClaims(data?.claims || []);
          setLoading(false);
        })
        .catch((err) => {
          const message = getApiErrorMessage(err, 'Failed to load posts');
          setError(message);
          setLoading(false);
        });
      return;
    }

    fetchWithRetry(() => axios.post(
      `${API}/discover/feed`,
      { limit: 20, diversity_preference: 0.35 },
      { headers, timeout: 15000, params: { standard: true } }
    ))
      .then(response => {
        const data = getApiData(response);
        setClaims(data?.claims || []);
        setLoading(false);
      })
      .catch((err) => {
        const message = getApiErrorMessage(err, 'Failed to load posts');
        setError(message);
        setLoading(false);
      });
  };

  const handleDeleteClaim = (claimId) => {
    setClaims(prev => prev.filter(c => c.id !== claimId));
  };

  const getFilteredClaims = () => {
    if (activeTab === 'top') {
      return [...claims].sort((a, b) => {
        const aScore = a.post_score ?? a.credibility_score ?? 0;
        const bScore = b.post_score ?? b.credibility_score ?? 0;
        return bScore - aScore;
      });
    } else if (activeTab === 'impact') {
      return [...claims].sort((a, b) => {
        const aImpact = a.impact_score ?? a.post_score ?? a.credibility_score ?? 0;
        const bImpact = b.impact_score ?? b.post_score ?? b.credibility_score ?? 0;
        return bImpact - aImpact;
      });
    } else if (activeTab === 'recent') {
      return [...claims].sort((a, b) => {
        const aTime = new Date(a.created_at).getTime();
        const bTime = new Date(b.created_at).getTime();
        return bTime - aTime;
      });
    }
    return claims;
  };

  const filteredClaims = getFilteredClaims();
  const visibleClaims = filteredClaims.filter((claim) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      claim.text?.toLowerCase().includes(q) ||
      claim.domain?.toLowerCase().includes(q) ||
      claim.category?.primary_path?.join(' ').toLowerCase().includes(q)
    );
  });

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
        <button onClick={loadClaims} className="px-6 py-2 bg-slate-900 text-white rounded shadow mt-4">Retry</button>
      </div>
    );
  }

  return (

    <div data-testid="feed-page" className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 py-6 md:py-8">
      {/* Tabs - optimized for accessibility and clarity */}
      <div className="border-b border-border mb-8 overflow-x-auto">
        <div className="flex gap-4 md:gap-8 min-w-max" role="tablist" aria-label="Feed Tabs">
          {tabList.map((tab, idx) => (
            <button
              key={tab.key}
              data-testid={`tab-${tab.key}`}
              ref={el => tabRefs.current[idx] = el}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-4 px-4 font-semibold transition-colors border-b-4 whitespace-nowrap rounded-t focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/70 ${
                activeTab === tab.key
                  ? 'border-primary text-primary bg-primary/5 shadow-sm scale-105'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/30'
              }`}
              role="tab"
              aria-selected={activeTab === tab.key}
              tabIndex={activeTab === tab.key ? 0 : -1}
            >
              {tab.label}
              <span className="ml-2 text-xs">{claims.length}</span>
            </button>
          ))}
        </div>
      </div>

      {visibleClaims.length === 0 ? (
        <div data-testid="no-claims" className="text-center py-12 bg-secondary rounded-sm">
          <p className="text-muted-foreground">
            {activeTab === 'top' && 'No top posts yet. Be the first to share!'}
            {activeTab === 'impact' && 'No high-impact posts yet. Be the first to share!'}
            {activeTab === 'recent' && 'No posts yet. Be the first to share!'}
            {/* Removed debated/uncertain empty state messages */}
          </p>
        </div>
      ) : (
        <div className="max-w-2xl mx-auto space-y-4">
          {visibleClaims.map((claim) => (
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
