import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, MessageSquare, TrendingUp, Shield, Users, Eye } from 'lucide-react';

const Welcome = () => {
  const navigate = useNavigate();

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
                Thrryv
              </h1>
            </div>
            <p className="text-2xl md:text-3xl text-slate-700 mb-4 font-light leading-relaxed">
              Evidence-Based Truth, Verified by the Community
            </p>
            <p className="text-lg md:text-xl text-slate-600 mb-12 max-w-3xl mx-auto leading-relaxed">
              A transparent fact-checking platform where claims are immutable, evidence is everything,
              and your reputation is built on accuracy—not volume.
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
              <h3 className="text-2xl font-bold mb-4 text-slate-900">Post Claims</h3>
              <p className="text-slate-600 leading-relaxed">
                Share factual assertions with evidence. Claims are immutable once posted—truth is permanent.
              </p>
            </div>

            <div className="text-center group">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6 group-hover:bg-green-200 transition-colors">
                <CheckCircle size={36} strokeWidth={1.5} className="text-green-600" />
              </div>
              <div className="mb-2 text-sm font-semibold text-green-600 tracking-wider">STEP 2</div>
              <h3 className="text-2xl font-bold mb-4 text-slate-900">Add Evidence</h3>
              <p className="text-slate-600 leading-relaxed">
                Community members annotate with supporting evidence, contradictions, or context. Quality matters.
              </p>
            </div>

            <div className="text-center group">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-purple-100 rounded-full mb-6 group-hover:bg-purple-200 transition-colors">
                <TrendingUp size={36} strokeWidth={1.5} className="text-purple-600" />
              </div>
              <div className="mb-2 text-sm font-semibold text-purple-600 tracking-wider">STEP 3</div>
              <h3 className="text-2xl font-bold mb-4 text-slate-900">Build Reputation</h3>
              <p className="text-slate-600 leading-relaxed">
                Your reputation grows when your contributions age well—accuracy over time, not quick likes.
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
                <h3 className="font-bold text-xl mb-3 text-slate-900">Immutable Claims</h3>
                <p className="text-slate-600 leading-relaxed">
                  Once posted, claims cannot be edited or deleted. This ensures accountability and prevents
                  revisionist history.
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
                <h3 className="font-bold text-xl mb-3 text-slate-900">Transparent Scoring</h3>
                <p className="text-slate-600 leading-relaxed">
                  Every credibility score and truth label is calculated transparently from community evidence.
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
                  Reputation is earned through accurate, well-evidenced contributions—not by posting the most.
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
                <h3 className="font-bold text-xl mb-3 text-slate-900">Time-Tested Truth</h3>
                <p className="text-slate-600 leading-relaxed">
                  Your contributions earn more reputation as they age well. Accuracy over time is rewarded.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Truth Labels - Improved visual hierarchy */}
      <div className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="playfair text-4xl md:text-5xl font-bold text-center mb-6 text-slate-900">
            Non-Binary Truth Labels
          </h2>
          <p className="text-center text-slate-600 text-lg mb-16 max-w-2xl mx-auto">
            Reality isn't black and white. Our 6-tier truth system reflects the nuance of evidence.
          </p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            <div className="p-6 rounded-lg border-l-4 shadow-sm hover:shadow-md transition-shadow" style={{backgroundColor: '#ECFDF5', borderColor: '#10B981'}}>
              <p className="font-bold text-lg mb-2" style={{color: '#065F46'}}>True</p>
              <p className="text-sm" style={{color: '#065F46'}}>Strong consensus with evidence</p>
            </div>
            <div className="p-6 rounded-lg border-l-4 shadow-sm hover:shadow-md transition-shadow" style={{backgroundColor: '#F0FDF4', borderColor: '#22C55E'}}>
              <p className="font-bold text-lg mb-2" style={{color: '#166534'}}>Likely True</p>
              <p className="text-sm" style={{color: '#166534'}}>Preponderance of evidence</p>
            </div>
            <div className="p-6 rounded-lg border-l-4 shadow-sm hover:shadow-md transition-shadow" style={{backgroundColor: '#FFFBEB', borderColor: '#F59E0B'}}>
              <p className="font-bold text-lg mb-2" style={{color: '#92400E'}}>Mixed Evidence</p>
              <p className="text-sm" style={{color: '#92400E'}}>Conflicting quality evidence</p>
            </div>
            <div className="p-6 rounded-lg border-l-4 shadow-sm hover:shadow-md transition-shadow" style={{backgroundColor: '#F3F4F6', borderColor: '#9CA3AF'}}>
              <p className="font-bold text-lg mb-2" style={{color: '#374151'}}>Uncertain</p>
              <p className="text-sm" style={{color: '#374151'}}>Insufficient evidence</p>
            </div>
            <div className="p-6 rounded-lg border-l-4 shadow-sm hover:shadow-md transition-shadow" style={{backgroundColor: '#FEF2F2', borderColor: '#EF4444'}}>
              <p className="font-bold text-lg mb-2" style={{color: '#991B1B'}}>Likely False</p>
              <p className="text-sm" style={{color: '#991B1B'}}>Evidence leans against</p>
            </div>
            <div className="p-6 rounded-lg border-l-4 shadow-sm hover:shadow-md transition-shadow" style={{backgroundColor: '#450A0A', borderColor: '#7F1D1D'}}>
              <p className="font-bold text-lg mb-2" style={{color: '#FEF2F2'}}>False</p>
              <p className="text-sm" style={{color: '#FEF2F2'}}>Strong evidence of falsehood</p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section - Improved contrast and spacing */}
      <div className="py-24 border-t border-slate-200">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="playfair text-4xl md:text-5xl font-bold mb-6 text-slate-900">
            Ready to Seek Truth?
          </h2>
          <p className="text-xl text-slate-600 mb-12 leading-relaxed">
            Join academics, journalists, and truth-seekers building a transparent knowledge base.
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
              Explore Claims
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
