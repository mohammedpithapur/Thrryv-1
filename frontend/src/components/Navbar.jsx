import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { User, PlusCircle, Plus, Bell } from 'lucide-react';
import axios from 'axios';
import UserAvatar from './UserAvatar';
import SearchBar from './SearchBar';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (user) {
      fetchUnreadCount();
      // Poll for new notifications every 30 seconds
      const interval = setInterval(fetchUnreadCount, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchUnreadCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/notifications/unread-count`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUnreadCount(response.data.unread_count);
    } catch (err) {
      console.error('Failed to fetch notification count');
    }
  };

  const handleSearch = (query) => {
    const normalized = (query || '').trim();
    if (!normalized) {
      localStorage.removeItem('feedSearchQuery');
      navigate('/feed');
      return;
    }
    localStorage.setItem('feedSearchQuery', normalized);
    navigate(`/feed?q=${encodeURIComponent(normalized)}`);
  };

  return (
    <>
      <nav data-testid="navbar" className="border-b border-border bg-card sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-3 md:py-4">
          <div className="flex items-center justify-between gap-4">
            <Link to="/feed" className="flex items-center gap-2 md:gap-3 shrink-0">
              <img src="/thrryv-logo.jpeg" alt="Thrryv" className="h-8 w-8 md:h-10 md:w-10 object-contain" />
              <span className="playfair text-xl md:text-2xl font-bold tracking-tight">Thrryv</span>
            </Link>

            {/* Desktop Search */}
            <div className="hidden md:flex flex-1 max-w-xl">
              <SearchBar
                placeholder="Search posts, topics, or keywords..."
                onSearch={handleSearch}
                value={new URLSearchParams(location.search).get('q') || ''}
              />
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-4 shrink-0">
              {user ? (
                <>
                  <button
                    data-testid="create-post-btn"
                    onClick={() => navigate('/create-post')}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium text-sm transition-colors"
                  >
                    <PlusCircle size={18} strokeWidth={1.5} />
                    New Post
                  </button>
                  <button
                    data-testid="notifications-btn"
                    onClick={() => navigate('/notifications')}
                    className="relative flex items-center gap-2 px-3 py-2 hover:bg-secondary rounded-sm text-sm transition-colors"
                  >
                    <Bell size={20} strokeWidth={1.5} />
                    {unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-medium">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </button>
                  <button
                    data-testid="profile-btn"
                    onClick={() => navigate(`/profile/${user.id}`)}
                    className="flex items-center gap-2 px-4 py-2 hover:bg-secondary rounded-sm text-sm transition-colors"
                  >
                    <UserAvatar user={user} size="sm" />
                    {user.username}
                  </button>
                </>
              ) : (
                <>
                  <button
                    data-testid="login-btn"
                    onClick={() => navigate('/login')}
                    className="px-4 py-2 hover:bg-secondary rounded-sm text-sm font-medium transition-colors"
                  >
                    Login
                  </button>
                  <button
                    data-testid="register-btn"
                    onClick={() => navigate('/register')}
                    className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm text-sm font-medium transition-colors"
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>

            {/* Mobile Navigation Toggle */}
            <div className="flex md:hidden items-center gap-2">
              {user && (
                <>
                  <button
                    data-testid="mobile-notifications-btn"
                    onClick={() => navigate('/notifications')}
                    className="relative p-2 hover:bg-secondary rounded-sm"
                  >
                    <Bell size={20} strokeWidth={1.5} />
                    {unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-medium">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </button>
                  <button
                    data-testid="mobile-profile-btn"
                    onClick={() => navigate(`/profile/${user.id}`)}
                    className="p-1.5 hover:bg-secondary rounded-sm"
                  >
                    <UserAvatar user={user} size="sm" />
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Mobile Search */}
          <div className="md:hidden mt-3">
            <SearchBar
              placeholder="Search posts, topics, or keywords..."
              onSearch={handleSearch}
              value={new URLSearchParams(location.search).get('q') || ''}
            />
          </div>
        </div>
      </nav>

      {/* Mobile Floating Action Button for New Post */}
      {user && (
        <button
          data-testid="mobile-create-post-fab"
          onClick={() => navigate('/create-post')}
          className="md:hidden fixed bottom-5 left-1/2 -translate-x-1/2 z-50 w-14 h-14 bg-primary text-primary-foreground rounded-full shadow-lg hover:bg-primary/90 flex items-center justify-center transition-all hover:scale-105"
          aria-label="Create new post"
        >
          <Plus size={26} strokeWidth={3} />
        </button>
      )}
    </>
  );
};

export default Navbar;
