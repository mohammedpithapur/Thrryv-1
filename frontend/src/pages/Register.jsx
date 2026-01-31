import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Register = ({ onLogin }) => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/register`, {
        username,
        email,
        password
      });

      localStorage.setItem('token', response.data.token);
      onLogin(response.data.user);
      toast.success('Registration successful');
      navigate('/feed');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="register-page" className="max-w-md mx-auto px-6 py-12">
      <div className="mb-8 text-center">
        <h1 className="playfair text-4xl font-bold tracking-tight mb-2">Sign Up</h1>
        <p className="text-muted-foreground">Join the truth-seeking community</p>
      </div>

      <form data-testid="register-form" onSubmit={handleSubmit} className="bg-card border border-border p-8 rounded-sm">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Username</label>
          <input
            data-testid="username-input"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="johndoe"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Email</label>
          <input
            data-testid="email-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="your@email.com"
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Password</label>
          <input
            data-testid="password-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3 border border-border rounded-sm focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="••••••••"
            required
            minLength={6}
          />
          <p className="text-xs text-muted-foreground mt-1">Minimum 6 characters</p>
        </div>

        <button
          type="submit"
          data-testid="register-submit-btn"
          disabled={loading}
          className="w-full px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed mb-4"
        >
          {loading ? 'Creating account...' : 'Create Account'}
        </button>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="text-primary hover:underline">
            Login
          </Link>
        </p>
      </form>
    </div>
  );
};

export default Register;