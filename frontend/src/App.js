import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "sonner";
import { ThemeProvider } from "./context/ThemeContext";
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
      <div className="App min-h-screen bg-background">
        <BrowserRouter>
          <Routes>
            {/* Welcome page without navbar */}
            <Route path="/" element={<Welcome />} />
            
            {/* Pages with navbar */}
            <Route path="/feed" element={<><Navbar user={user} onLogout={handleLogout} /><Feed user={user} /></>} />
            <Route path="/claims/:claimId" element={<><Navbar user={user} onLogout={handleLogout} /><ClaimDetail user={user} /></>} />
            <Route path="/create-claim" element={<><Navbar user={user} onLogout={handleLogout} /><CreateClaim user={user} /></>} />
            <Route path="/login" element={<><Navbar user={user} onLogout={handleLogout} /><Login onLogin={handleLogin} /></>} />
            <Route path="/register" element={<><Navbar user={user} onLogout={handleLogout} /><Register onLogin={handleLogin} /></>} />
            <Route path="/profile/:userId" element={<><Navbar user={user} onLogout={handleLogout} /><UserProfile currentUser={user} /></>} />
            <Route path="/settings" element={<><Navbar user={user} onLogout={handleLogout} /><ProfileSettings user={user} onUserUpdate={handleUserUpdate} onLogout={handleLogout} /></>} />
            <Route path="/notifications" element={<><Navbar user={user} onLogout={handleLogout} /><Notifications /></>} />
          </Routes>
          <Toaster position="top-center" />
        </BrowserRouter>
      </div>
    </ThemeProvider>
  );
}

export default App;
