import React from 'react';
import { User } from 'lucide-react';

const UserAvatar = ({ user, size = 'md', className = '' }) => {
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
  
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-16 h-16 text-xl',
    xl: 'w-24 h-24 text-3xl'
  };
  
  const getInitials = (name) => {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const hasProfilePicture = user?.profile_picture || user?.id;

  return (
    <div className={`${sizeClasses[size]} rounded-full overflow-hidden flex items-center justify-center bg-slate-200 ${className}`}>
      {hasProfilePicture && user?.id ? (
        <img
          src={`${API}/users/profile-picture/${user.id}`}
          alt={user.username || 'User'}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.style.display = 'none';
            e.target.nextSibling.style.display = 'flex';
          }}
        />
      ) : null}
      <div 
        className="w-full h-full flex items-center justify-center bg-slate-300 text-slate-700 font-medium"
        style={{ display: hasProfilePicture ? 'none' : 'flex' }}
      >
        {user?.username ? getInitials(user.username) : <User size={size === 'sm' ? 16 : size === 'md' ? 20 : size === 'lg' ? 32 : 48} />}
      </div>
    </div>
  );
};

export default UserAvatar;
