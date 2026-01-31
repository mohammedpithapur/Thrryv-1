import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import UserAvatar from '../components/UserAvatar';
import { useTheme } from '../context/ThemeContext';
import { Camera, Moon, Sun } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfileSettings = ({ user, onUserUpdate }) => {
  const navigate = useNavigate();
  const { darkMode, toggleDarkMode } = useTheme();
  const [username, setUsername] = useState(user?.username || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);

  if (!user) {
    navigate('/login');
    return null;
  }

  const handleProfilePictureUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB');
      return;
    }

    setUploading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      await axios.post(`${API}/users/profile-picture`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`
        }
      });

      toast.success('Profile picture updated!');
      // Force reload to show new picture
      window.location.reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();

    if (newPassword && newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.patch(
        `${API}/users/settings`,
        {
          username: username !== user.username ? username : null,
          current_password: currentPassword || null,
          new_password: newPassword || null
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      toast.success('Settings updated successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      
      // Update user data
      if (onUserUpdate) {
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        onUserUpdate(response.data);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    toast.info('Dark mode coming soon!');
  };

  return (
    <div data-testid="profile-settings-page" className="max-w-4xl mx-auto px-6 py-8">
      <h1 className="playfair text-4xl font-bold mb-8">Profile Settings</h1>

      {/* Profile Picture Section */}
      <div className="bg-card border border-border p-8 rounded-sm mb-6">
        <h2 className="text-xl font-semibold mb-6">Profile Picture</h2>
        <div className="flex items-center gap-6">
          <div className="relative group cursor-pointer" onClick={() => document.getElementById('profile-pic-input').click()}>
            <UserAvatar user={user} size="xl" />
            <div className="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Camera size={32} className="text-white" />
            </div>
            {uploading && (
              <div className="absolute inset-0 bg-black/70 rounded-full flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
              </div>
            )}
          </div>
          <div>
            <h3 className="font-medium mb-2">{user.username}</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Click on your profile picture to change it
            </p>
            <input
              type="file"
              id="profile-pic-input"
              accept="image/*"
              onChange={handleProfilePictureUpload}
              className="hidden"
            />
            <button
              onClick={() => document.getElementById('profile-pic-input').click()}
              disabled={uploading}
              className="px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-sm text-sm font-medium disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : 'Change Picture'}
            </button>
          </div>
        </div>
      </div>

      {/* Account Settings */}
      <form onSubmit={handleSaveSettings} className="bg-card border border-border p-8 rounded-sm mb-6">
        <h2 className="text-xl font-semibold mb-6">Account Settings</h2>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Your username"
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Current Password</label>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Enter current password to change it"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Leave blank if you don't want to change your password
          </p>
        </div>

        {currentPassword && (
          <>
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Enter new password"
                minLength={6}
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="Confirm new password"
                minLength={6}
              />
            </div>
          </>
        )}

        <button
          type="submit"
          disabled={saving}
          className="px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </form>

      {/* Appearance Settings */}
      <div className="bg-card border border-border p-8 rounded-sm">
        <h2 className="text-xl font-semibold mb-6">Appearance</h2>
        
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium mb-1">Dark Mode</h3>
            <p className="text-sm text-muted-foreground">
              Toggle between light and dark theme
            </p>
          </div>
          <button
            onClick={toggleDarkMode}
            className={`relative inline-flex h-12 w-20 items-center rounded-full transition-colors ${
              darkMode ? 'bg-slate-800' : 'bg-slate-200'
            }`}
          >
            <span
              className={`inline-flex h-10 w-10 transform items-center justify-center rounded-full bg-white shadow-lg transition-transform ${
                darkMode ? 'translate-x-9' : 'translate-x-1'
              }`}
            >
              {darkMode ? (
                <Moon size={20} className="text-slate-800" />
              ) : (
                <Sun size={20} className="text-yellow-500" />
              )}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileSettings;
