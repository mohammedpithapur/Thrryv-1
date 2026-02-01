import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import UserAvatar from '../components/UserAvatar';
import { useTheme } from '../context/ThemeContext';
import { Camera, Moon, Sun, AlertTriangle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfileSettings = ({ user, onUserUpdate, onLogout }) => {
  const navigate = useNavigate();
  const { darkMode, toggleDarkMode } = useTheme();
  const [username, setUsername] = useState(user?.username || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleting, setDeleting] = useState(false);

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

  const handleToggleDarkMode = () => {
    toggleDarkMode();
    toast.success(darkMode ? 'Light mode enabled' : 'Dark mode enabled');
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'Delete Account') {
      toast.error('Please type "Delete Account" exactly to confirm');
      return;
    }

    setDeleting(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/users/account?confirmation=${encodeURIComponent(deleteConfirmation)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Account deleted successfully');
      localStorage.removeItem('token');
      if (onLogout) {
        onLogout();
      }
      navigate('/');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete account');
    } finally {
      setDeleting(false);
      setShowDeleteModal(false);
    }
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
            onClick={handleToggleDarkMode}
            data-testid="dark-mode-toggle"
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

      {/* Danger Zone - Delete Account */}
      <div className="bg-card border border-red-200 dark:border-red-900 p-8 rounded-sm">
        <h2 className="text-xl font-semibold mb-2 text-red-600 dark:text-red-400">Danger Zone</h2>
        <p className="text-sm text-muted-foreground mb-6">
          Irreversible actions that affect your account permanently.
        </p>
        
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium mb-1">Delete Account</h3>
            <p className="text-sm text-muted-foreground">
              Permanently delete your account, all your claims, and annotations.
            </p>
          </div>
          <button
            onClick={() => setShowDeleteModal(true)}
            data-testid="delete-account-btn"
            className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-sm font-medium text-sm transition-colors"
          >
            Delete Account
          </button>
        </div>
      </div>

      {/* Delete Account Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-border rounded-sm p-8 max-w-md w-full">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                <AlertTriangle size={24} className="text-red-600 dark:text-red-400" />
              </div>
              <h2 className="text-xl font-bold">Delete Account</h2>
            </div>

            <div className="mb-6 space-y-3 text-sm text-muted-foreground">
              <p>This action <strong className="text-foreground">cannot be undone</strong>. This will permanently delete:</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>Your account and profile</li>
                <li>All your claims and posts</li>
                <li>All your annotations</li>
                <li>Your reputation history</li>
              </ul>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                Type <span className="font-mono bg-secondary px-2 py-0.5 rounded">Delete Account</span> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmation}
                onChange={(e) => setDeleteConfirmation(e.target.value)}
                data-testid="delete-confirmation-input"
                className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                placeholder="Delete Account"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => { setShowDeleteModal(false); setDeleteConfirmation(''); }}
                className="flex-1 px-4 py-3 border border-border hover:bg-secondary rounded-sm font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleting || deleteConfirmation !== 'Delete Account'}
                data-testid="confirm-delete-btn"
                className="flex-1 px-4 py-3 bg-red-600 text-white hover:bg-red-700 rounded-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {deleting ? 'Deleting...' : 'Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfileSettings;
