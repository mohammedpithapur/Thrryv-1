import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, PlusCircle, LogOut } from 'lucide-react';

const Navbar = ({ user, onLogout }) => {
  const navigate = useNavigate();

  return (
    <nav data-testid="navbar" className="border-b border-border bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/feed" className="playfair text-2xl font-bold tracking-tight">
            Thrryv
          </Link>

          <div className="flex items-center gap-4">
            {user ? (
              <>
                <button
                  data-testid="create-claim-btn"
                  onClick={() => navigate('/create-claim')}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium text-sm transition-colors"
                >
                  <PlusCircle size={18} strokeWidth={1.5} />
                  New Claim
                </button>
                <button
                  data-testid="profile-btn"
                  onClick={() => navigate(`/profile/${user.id}`)}
                  className="flex items-center gap-2 px-4 py-2 hover:bg-secondary rounded-sm text-sm transition-colors"
                >
                  <User size={18} strokeWidth={1.5} />
                  {user.username}
                </button>
                <button
                  data-testid="logout-btn"
                  onClick={onLogout}
                  className="flex items-center gap-2 px-4 py-2 hover:bg-secondary rounded-sm text-sm transition-colors"
                >
                  <LogOut size={18} strokeWidth={1.5} />
                  Logout
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
        </div>
      </div>
    </nav>
  );
};

export default Navbar;