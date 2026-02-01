import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import UserAvatar from '../components/UserAvatar';
import { useTheme } from '../context/ThemeContext';
import { Camera, Moon, Sun, AlertTriangle, Check, X, Loader2, Save } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProfileSettings = ({ user, onUserUpdate, onLogout }) => {
  const navigate = useNavigate();
  const { darkMode, toggleDarkMode } = useTheme();
  const [username, setUsername] = useState(user?.username || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savingUsername, setSavingUsername] = useState(false);
  const [savingBio, setSavingBio] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleting, setDeleting] = useState(false);
  
  // Username availability state
  const [checkingUsername, setCheckingUsername] = useState(false);
  const [usernameAvailable, setUsernameAvailable] = useState(null);
  const [usernameSuggestions, setUsernameSuggestions] = useState([]);

  if (!user) {
    navigate('/login');
    return null;
  }

  // Check username availability with debounce
  useEffect(() => {
    if (username === user?.username) {
      setUsernameAvailable(null);
      setUsernameSuggestions([]);
      return;
    }

    if (username.length < 3) {
      setUsernameAvailable(null);
      setUsernameSuggestions([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setCheckingUsername(true);
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API}/users/check-username/${encodeURIComponent(username)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUsernameAvailable(response.data.available);
        setUsernameSuggestions(response.data.suggestions || []);
      } catch (err) {
        console.error('Failed to check username');
      } finally {
        setCheckingUsername(false);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [username, user?.username]);

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
      window.location.reload();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveUsername = async () => {
    if (username === user?.username) {
      toast.info('No changes to save');
      return;
    }

    if (username.length < 3) {
      toast.error('Username must be at least 3 characters');
      return;
    }

    if (!usernameAvailable) {
      toast.error('Please choose an available username');
      return;
    }

    setSavingUsername(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.patch(
        `${API}/users/settings`,
        { username },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Username updated successfully!');
      if (onUserUpdate && response.data.user) {
        onUserUpdate({ ...user, username: response.data.user.username });
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update username');
    } finally {
      setSavingUsername(false);
    }
  };

  const handleSaveBio = async () => {
    if (bio === (user?.bio || '')) {
      toast.info('No changes to save');
      return;
    }

    if (bio.length > 60) {
      toast.error('Bio must be 60 characters or less');
      return;
    }

    setSavingBio(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.patch(
        `${API}/users/settings`,
        { bio },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Bio updated successfully!');
      if (onUserUpdate && response.data.user) {
        onUserUpdate({ ...user, bio: response.data.user.bio });
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update bio');
    } finally {
      setSavingBio(false);
    }
  };

  const handleSavePassword = async (e) => {
    e.preventDefault();

    if (!currentPassword || !newPassword) {
      toast.error('Please fill in all password fields');
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.patch(
        `${API}/users/settings`,
        {
          current_password: currentPassword,
          new_password: newPassword
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Password updated successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update password');
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
    <div data-testid="profile-settings-page" className="max-w-3xl mx-auto px-4 md:px-6 py-8 pb-24">
      <h1 className="playfair text-3xl md:text-4xl font-bold tracking-tight mb-8">Profile Settings</h1>

      {/* Profile Picture & Bio Section */}
      <div className="bg-card border border-border p-6 md:p-8 rounded-sm mb-6">
        <h2 className="text-xl font-semibold mb-6">Profile Picture & Bio</h2>
        
        <div className="flex flex-col md:flex-row items-start gap-6 mb-6">
          <div className="relative">
            <UserAvatar user={user} size="xl" />
            <label className="absolute bottom-0 right-0 p-2 bg-primary text-primary-foreground rounded-full cursor-pointer hover:bg-primary/90 transition-colors">
              <Camera size={18} />
              <input
                type="file"
                accept="image/*"
                onChange={handleProfilePictureUpload}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>
          <div className="flex-1">
            <p className="text-sm text-muted-foreground mb-2">
              Click the camera icon to upload a new profile picture
            </p>
            <p className="text-xs text-muted-foreground">
              Supported formats: JPG, PNG, GIF. Max size: 5MB
            </p>
          </div>
        </div>

        {/* Bio Field */}
        <div className="space-y-3">
          <label className="block text-sm font-medium">Bio</label>
          <div className="relative">
            <textarea
              data-testid="bio-input"
              value={bio}
              onChange={(e) => setBio(e.target.value.slice(0, 60))}
              placeholder="Describe yourself in 60 characters..."
              className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background resize-none"
              rows="2"
              maxLength={60}
            />
            <span className={`absolute bottom-2 right-2 text-xs ${bio.length >= 55 ? 'text-yellow-600' : 'text-muted-foreground'}`}>
              {bio.length}/60
            </span>
          </div>
          <div className="flex justify-end">
            <button
              onClick={handleSaveBio}
              disabled={savingBio || bio === (user?.bio || '')}
              data-testid="save-bio-btn"
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {savingBio ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              Save Bio
            </button>
          </div>
        </div>
      </div>

      {/* Username Section */}
      <div className="bg-card border border-border p-6 md:p-8 rounded-sm mb-6">
        <h2 className="text-xl font-semibold mb-6">Username</h2>
        
        <div className="space-y-3">
          <label className="block text-sm font-medium">Display Name</label>
          <div className="relative">
            <input
              type="text"
              data-testid="username-input"
              value={username}
              onChange={(e) => setUsername(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
              className={`w-full px-4 py-3 border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background pr-12 ${
                usernameAvailable === false ? 'border-red-500' : 
                usernameAvailable === true ? 'border-green-500' : 'border-border'
              }`}
              placeholder="your_username"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {checkingUsername && <Loader2 size={20} className="animate-spin text-muted-foreground" />}
              {!checkingUsername && usernameAvailable === true && <Check size={20} className="text-green-500" />}
              {!checkingUsername && usernameAvailable === false && <X size={20} className="text-red-500" />}
            </div>
          </div>
          
          {/* Username availability message */}
          {usernameAvailable === false && (
            <div className="space-y-2">
              <p className="text-sm text-red-600 dark:text-red-400">
                This username is not available.
              </p>
              {usernameSuggestions.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs text-muted-foreground">Try:</span>
                  {usernameSuggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setUsername(suggestion)}
                      className="text-xs px-2 py-1 bg-secondary hover:bg-secondary/80 rounded-sm transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {usernameAvailable === true && username !== user?.username && (
            <p className="text-sm text-green-600 dark:text-green-400">
              This username is available!
            </p>
          )}

          <div className="flex justify-end pt-2">
            <button
              onClick={handleSaveUsername}
              disabled={savingUsername || username === user?.username || usernameAvailable === false || username.length < 3}
              data-testid="save-username-btn"
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {savingUsername ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              Save Changes
            </button>
          </div>
        </div>
      </div>

      {/* Email Display (Read-only) */}
      <div className="bg-card border border-border p-6 md:p-8 rounded-sm mb-6">
        <h2 className="text-xl font-semibold mb-6">Email Address</h2>
        <div className="space-y-2">
          <label className="block text-sm font-medium">Your Email (Private)</label>
          <input
            type="email"
            value={user?.email || ''}
            disabled
            className="w-full px-4 py-3 border border-border rounded-sm bg-secondary text-muted-foreground cursor-not-allowed"
          />
          <p className="text-xs text-muted-foreground">
            Your email address is private and will never be shown to other users.
          </p>
        </div>
      </div>

      {/* Password Section */}
      <div className="bg-card border border-border p-6 md:p-8 rounded-sm mb-6">
        <h2 className="text-xl font-semibold mb-6">Change Password</h2>
        
        <form onSubmit={handleSavePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background"
              placeholder="Enter current password"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background"
              placeholder="Enter new password"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background"
              placeholder="Confirm new password"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={saving || !currentPassword || !newPassword || !confirmPassword}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              Update Password
            </button>
          </div>
        </form>
      </div>

      {/* Appearance Settings */}
      <div className="bg-card border border-border p-6 md:p-8 rounded-sm mb-6">
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
      <div className="bg-card border border-red-200 dark:border-red-900 p-6 md:p-8 rounded-sm">
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
          <div className="bg-card border border-border rounded-sm p-6 md:p-8 max-w-md w-full">
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
