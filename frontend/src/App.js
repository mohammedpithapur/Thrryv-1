import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "sonner";
import { ThemeProvider } from "./context/ThemeContext";
import ErrorBoundary from "./components/ErrorBoundary";
import Navbar from "./components/Navbar";
import Welcome from "./pages/Welcome";
import Feed from "./pages/Feed";
import ClaimDetail from "./pages/ClaimDetail";
import CreateClaim from "./pages/CreateClaim";
import Login from "./pages/Login";
import Register from "./pages/Register";
import UserProfile from "./pages/UserProfile";
import ProfileSettings from "./pages/ProfileSettings";
import Notifications from "./pages/Notifications";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
    } catch (err) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleUserUpdate = (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <ThemeProvider>
      <ErrorBoundary>
        <div className="App min-h-screen bg-background">
          <BrowserRouter>
            <Routes>
              {/* Welcome page without navbar */}
              <Route path="/" element={<Welcome />} />
              
              {/* Pages with navbar - each wrapped in its own ErrorBoundary */}
              <Route path="/feed" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><Feed user={user} /></ErrorBoundary></>} />
              <Route path="/posts/:postId" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><ClaimDetail user={user} /></ErrorBoundary></>} />
              <Route path="/create-post" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><CreateClaim user={user} /></ErrorBoundary></>} />
              <Route path="/claims/:claimId" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><ClaimDetail user={user} /></ErrorBoundary></>} />
              <Route path="/create-claim" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><CreateClaim user={user} /></ErrorBoundary></>} />
              <Route path="/login" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><Login onLogin={handleLogin} /></ErrorBoundary></>} />
              <Route path="/register" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><Register onLogin={handleLogin} /></ErrorBoundary></>} />
              <Route path="/profile/:userId" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><UserProfile currentUser={user} onLogout={handleLogout} /></ErrorBoundary></>} />
              <Route path="/settings" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><ProfileSettings user={user} onUserUpdate={handleUserUpdate} onLogout={handleLogout} /></ErrorBoundary></>} />
              <Route path="/notifications" element={<><Navbar user={user} onLogout={handleLogout} /><ErrorBoundary><Notifications /></ErrorBoundary></>} />
            </Routes>
            <Toaster position="top-center" />
          </BrowserRouter>
        </div>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;
