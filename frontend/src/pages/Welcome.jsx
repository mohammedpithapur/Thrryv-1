import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, MessageSquare, TrendingUp, Shield, Users, Eye } from 'lucide-react';

const Welcome = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to feed if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/feed');
    }
  }, [navigate]);

  return (
    <div data-testid="welcome-page" className="min-h-screen bg-white">
      {/* Minimal Header */}
      <header className="px-8 py-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <img src="/thrryv-logo.jpeg" alt="Thrryv" className="h-8 w-8 object-contain" />
          <h1 className="playfair text-2xl font-semibold tracking-tight text-slate-900">
            Thrryv
          </h1>
        </div>
      </header>
      {/* Hero Section - Improved spacing and typography */}
      <div className="border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-20 md:py-32">
          <div className="text-center max-w-4xl mx-auto">
            <div className="flex flex-col items-center justify-center mb-6">
              <img src="/thrryv-logo.jpeg" alt="Thrryv" className="h-20 w-20 md:h-24 md:w-24 object-contain mb-4" />
              <h1 className="playfair text-5xl md:text-7xl font-bold tracking-tight text-slate-900">
                Where Your Impact Matters
              </h1>
            </div>
            <p className="text-lg md:text-xl text-slate-600 mb-12 max-w-3xl mx-auto leading-relaxed">
              A transparent social media platform where posts are analyzed by AI, evidence is everything,
              and your impact is built on quality content, not volume.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                data-testid="welcome-register-btn"
                onClick={() => navigate('/register')}
                className="px-10 py-4 bg-slate-900 text-white hover:bg-slate-800 font-medium text-lg transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                Join the Community
              </button>
              <button
                data-testid="welcome-login-btn"
                onClick={() => navigate('/login')}
                className="px-10 py-4 bg-white text-slate-900 hover:bg-slate-50 border-2 border-slate-900 font-medium text-lg transition-all duration-200"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works - Improved layout and icons */}
      <div className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="playfair text-4xl md:text-5xl font-bold text-center mb-6 text-slate-900">
            How Thrryv Works
          </h2>
          <p className="text-center text-slate-600 text-lg mb-16 max-w-2xl mx-auto">
            A simple three-step process for community-driven fact verification
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center group">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 rounded-full mb-6 group-hover:bg-blue-200 transition-colors">
                <MessageSquare size={36} strokeWidth={1.5} className="text-blue-600" />
              </div>
              <div className="mb-2 text-sm font-semibold text-blue-600 tracking-wider">STEP 1</div>
              <h3 className="text-2xl font-bold mb-4 text-slate-900">Share Posts</h3>
              <p className="text-slate-600 leading-relaxed">
                Share your perspectives with supporting evidence. Posts are analyzed by AI for clarity, context, and quality.
              </p>
            </div>

            <div className="text-center group">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6 group-hover:bg-green-200 transition-colors">
                <CheckCircle size={36} strokeWidth={1.5} className="text-green-600" />
              </div>
              <div className="mb-2 text-sm font-semibold text-green-600 tracking-wider">STEP 2</div>
              <h3 className="text-2xl font-bold mb-4 text-slate-900">Get Feedback</h3>
              <p className="text-slate-600 leading-relaxed">
                Receive AI-powered signals on clarity, context, and evidence quality. Community members annotate with insights.
              </p>
            </div>

            <div className="text-center group">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-purple-100 rounded-full mb-6 group-hover:bg-purple-200 transition-colors">
                <TrendingUp size={36} strokeWidth={1.5} className="text-purple-600" />
              </div>
              <div className="mb-2 text-sm font-semibold text-purple-600 tracking-wider">STEP 3</div>
              <h3 className="text-2xl font-bold mb-4 text-slate-900">Build Impact</h3>
              <p className="text-slate-600 leading-relaxed">
                Your impact grows when your posts demonstrate quality and consistency. Recognition over time, not quick likes.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Features - Improved card design */}
      <div className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="playfair text-4xl md:text-5xl font-bold text-center mb-6 text-slate-900">
            What Makes Thrryv Different
          </h2>
          <p className="text-center text-slate-600 text-lg mb-16 max-w-2xl mx-auto">
            Built on principles of transparency, accuracy, and community trust
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="flex gap-6 p-8 bg-white border-2 border-slate-200 hover:border-slate-300 transition-colors group">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                  <Shield size={24} strokeWidth={1.5} className="text-slate-700" />
                </div>
              </div>
              <div>
                <h3 className="font-bold text-xl mb-3 text-slate-900">AI-Powered Analysis</h3>
                <p className="text-slate-600 leading-relaxed">
                  Every post is analyzed before publishing for clarity, context, and evidence quality with detailed feedback.
                </p>
              </div>
            </div>

            <div className="flex gap-6 p-8 bg-white border-2 border-slate-200 hover:border-slate-300 transition-colors group">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                  <Eye size={24} strokeWidth={1.5} className="text-slate-700" />
                </div>
              </div>
              <div>
                <h3 className="font-bold text-xl mb-3 text-slate-900">Transparent Post Scoring</h3>
                <p className="text-slate-600 leading-relaxed">
                  Every post score (0-15.0) is calculated transparently from AI analysis and community feedback.
                  No black boxes.
                </p>
              </div>
            </div>

            <div className="flex gap-6 p-8 bg-white border-2 border-slate-200 hover:border-slate-300 transition-colors group">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                  <Users size={24} strokeWidth={1.5} className="text-slate-700" />
                </div>
              </div>
              <div>
                <h3 className="font-bold text-xl mb-3 text-slate-900">Quality Over Volume</h3>
                <p className="text-slate-600 leading-relaxed">
                  Impact is earned through high-quality, well-evidenced content, not by posting the most.
                </p>
              </div>
            </div>

            <div className="flex gap-6 p-8 bg-white border-2 border-slate-200 hover:border-slate-300 transition-colors group">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                  <TrendingUp size={24} strokeWidth={1.5} className="text-slate-700" />
                </div>
              </div>
              <div>
                <h3 className="font-bold text-xl mb-3 text-slate-900">Content Signals</h3>
                <p className="text-slate-600 leading-relaxed">
                  Get specific feedback on clarity, context, and evidence. Improve your content with actionable insights.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section - Improved contrast and spacing */}
      <div className="py-24 border-t border-slate-200">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="playfair text-4xl md:text-5xl font-bold text-center mb-6 text-slate-900">
            Ready to Build Impact?
          </h2>
          <p className="text-xl text-slate-600 mb-12 leading-relaxed">
            Join content creators, analysts, and contributors building a transparent knowledge community.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate('/register')}
              className="px-10 py-4 bg-slate-900 text-white hover:bg-slate-800 font-medium text-lg transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              Create Free Account
            </button>
            <button
              onClick={() => navigate('/feed')}
              className="px-10 py-4 bg-white text-slate-900 hover:bg-slate-50 border-2 border-slate-900 font-medium text-lg transition-all duration-200"
            >
              Explore Posts
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
