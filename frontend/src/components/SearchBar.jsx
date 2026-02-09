import React, { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, Clock, Tag, X } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SearchBar = ({ onSearch, placeholder = "Search posts...", value = undefined }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [trendingTopics, setTrendingTopics] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  const searchRef = useRef(null);

  // Load recent searches from localStorage
  useEffect(() => {
    const recent = JSON.parse(localStorage.getItem('recentSearches') || '[]');
    setRecentSearches(recent.slice(0, 5));
    
    // Load trending topics (mock data - replace with actual API call)
    setTrendingTopics([
      'Climate Change',
      'Technology',
      'Healthcare',
      'Economics',
      'Education'
    ]);
  }, []);

  // Sync external value (e.g., from URL query)
  useEffect(() => {
    if (value !== undefined) {
      setSearchTerm(value);
    }
  }, [value]);

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch suggestions as user types
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (searchTerm.trim().length < 2) {
        setSuggestions([]);
        return;
      }

      try {
        // Mock suggestions - replace with actual API call
        const mockSuggestions = [
          { type: 'post', text: `Posts about "${searchTerm}"` },
          { type: 'user', text: `Users discussing "${searchTerm}"` },
          { type: 'topic', text: `Topic: ${searchTerm}` }
        ];
        setSuggestions(mockSuggestions);
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
      }
    };

    const debounce = setTimeout(() => {
      fetchSuggestions();
    }, 300);

    return () => clearTimeout(debounce);
  }, [searchTerm]);

  const handleSearch = (term) => {
    const normalized = term.trim();
    if (normalized) {
      // Save to recent searches
      const recent = [normalized, ...recentSearches.filter(s => s !== normalized)].slice(0, 5);
      localStorage.setItem('recentSearches', JSON.stringify(recent));
      setRecentSearches(recent);
    }

    if (onSearch) {
      onSearch(normalized);
    }
    setShowSuggestions(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSearch(searchTerm);
  };

  return (
    <div ref={searchRef} className="relative w-full max-w-2xl">
      {/* Search Input */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search 
            size={20} 
            className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground" 
          />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              const next = e.target.value;
              setSearchTerm(next);
              if (!next.trim()) {
                handleSearch('');
              }
            }}
            onFocus={() => setShowSuggestions(true)}
            placeholder={placeholder}
            className="w-full pl-12 pr-10 py-3 border border-border rounded-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          />
          {searchTerm.trim().length > 0 && (
            <button
              type="button"
              aria-label="Clear search"
              onClick={() => {
                setSearchTerm('');
                handleSearch('');
                setShowSuggestions(false);
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </form>

      {/* Suggestions Dropdown */}
      {showSuggestions && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-sm shadow-lg z-50 max-h-[400px] overflow-y-auto">
          {/* Search Suggestions */}
          {searchTerm.trim().length >= 2 && suggestions.length > 0 && (
            <div className="p-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide px-2 py-1">
                Suggestions
              </p>
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSearch(suggestion.text)}
                  className="w-full flex items-center gap-3 px-3 py-2 hover:bg-secondary rounded-sm text-left transition-colors"
                >
                  <Search size={16} className="text-muted-foreground" />
                  <span className="text-sm">{suggestion.text}</span>
                </button>
              ))}
            </div>
          )}

          {/* Recent Searches */}
          {searchTerm.trim().length === 0 && recentSearches.length > 0 && (
            <div className="p-2 border-t border-border">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide px-2 py-1 flex items-center gap-2">
                <Clock size={12} />
                Recent Searches
              </p>
              {recentSearches.map((search, index) => (
                <button
                  key={index}
                  onClick={() => handleSearch(search)}
                  className="w-full flex items-center gap-3 px-3 py-2 hover:bg-secondary rounded-sm text-left transition-colors"
                >
                  <Clock size={16} className="text-muted-foreground" />
                  <span className="text-sm">{search}</span>
                </button>
              ))}
            </div>
          )}

          {/* Trending Topics */}
          {searchTerm.trim().length === 0 && (
            <div className="p-2 border-t border-border">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide px-2 py-1 flex items-center gap-2">
                <TrendingUp size={12} />
                Trending Topics
              </p>
              <div className="flex flex-wrap gap-2 px-2 py-2">
                {trendingTopics.map((topic, index) => (
                  <button
                    key={index}
                    onClick={() => handleSearch(topic)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-primary/10 text-primary hover:bg-primary/20 rounded-full text-sm transition-colors"
                  >
                    <Tag size={12} />
                    {topic}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Content */}
          {searchTerm.trim().length === 0 && (
            <div className="p-2 border-t border-border">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide px-2 py-1">
                Recommended for You
              </p>
              <div className="space-y-1">
                <button
                  onClick={() => handleSearch('verified posts')}
                  className="w-full flex items-center gap-3 px-3 py-2 hover:bg-secondary rounded-sm text-left transition-colors"
                >
                  <span className="text-sm">📊 High-quality verified posts</span>
                </button>
                <button
                  onClick={() => handleSearch('debated topics')}
                  className="w-full flex items-center gap-3 px-3 py-2 hover:bg-secondary rounded-sm text-left transition-colors"
                >
                  <span className="text-sm">💬 Most debated topics</span>
                </button>
                <button
                  onClick={() => handleSearch('recent')}
                  className="w-full flex items-center gap-3 px-3 py-2 hover:bg-secondary rounded-sm text-left transition-colors"
                >
                  <span className="text-sm">🕒 Recent posts</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
