import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, MessageSquare, TrendingUp, Shield, Users, Eye } from 'lucide-react';

const Welcome = () => {
  const navigate = useNavigate();

  return (
    <div data-testid="welcome-page" className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <div className="text-center mb-12">
            <h1 className="playfair text-6xl font-bold tracking-tight mb-4">
              Thrryv
            </h1>
            <p className="text-2xl text-muted-foreground mb-8">
              Evidence-Based Truth, Verified by the Community
            </p>
            <p className="text-lg max-w-2xl mx-auto mb-8">
              A transparent fact-checking platform where claims are immutable, evidence is everything,
              and your reputation is built on accuracy—not volume.
            </p>
            <div className="flex gap-4 justify-center">
              <button
                data-testid="welcome-register-btn"
                onClick={() => navigate('/register')}
                className="px-8 py-4 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium text-lg transition-colors"
              >
                Join the Community
              </button>
              <button
                data-testid="welcome-login-btn"
                onClick={() => navigate('/login')}
                className="px-8 py-4 bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-sm font-medium text-lg transition-colors"
              >
                Login
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="playfair text-3xl font-bold text-center mb-12">How Thrryv Works</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="text-center p-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-sm mb-4">
              <MessageSquare size={32} strokeWidth={1.5} className="text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">1. Post Claims</h3>
            <p className="text-muted-foreground">
              Share factual assertions with evidence. Claims are immutable once posted—truth is permanent.
            </p>
          </div>

          <div className="text-center p-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-sm mb-4">
              <CheckCircle size={32} strokeWidth={1.5} className="text-green-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">2. Add Evidence</h3>
            <p className="text-muted-foreground">
              Community members annotate with supporting evidence, contradictions, or context. Quality matters.
            </p>
          </div>

          <div className="text-center p-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-sm mb-4">
              <TrendingUp size={32} strokeWidth={1.5} className="text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold mb-3">3. Build Reputation</h3>
            <p className="text-muted-foreground">
              Your reputation grows when your contributions age well—accuracy over time, not quick likes.
            </p>
          </div>
        </div>
      </div>

      {/* Key Features */}
      <div className="bg-secondary py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="playfair text-3xl font-bold text-center mb-12">What Makes Thrryv Different</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="flex gap-4 p-6 bg-background rounded-sm border border-border">
              <Shield size={24} strokeWidth={1.5} className="text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg mb-2">Immutable Claims</h3>
                <p className="text-sm text-muted-foreground">
                  Once posted, claims cannot be edited or deleted. This ensures accountability and prevents
                  revisionist history.
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-6 bg-background rounded-sm border border-border">
              <Eye size={24} strokeWidth={1.5} className="text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg mb-2">Transparent Scoring</h3>
                <p className="text-sm text-muted-foreground">
                  Every credibility score and truth label is calculated transparently from community evidence.
                  No black boxes.
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-6 bg-background rounded-sm border border-border">
              <Users size={24} strokeWidth={1.5} className="text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg mb-2">Quality Over Volume</h3>
                <p className="text-sm text-muted-foreground">
                  Reputation is earned through accurate, well-evidenced contributions—not by posting the most.
                </p>
              </div>
            </div>

            <div className="flex gap-4 p-6 bg-background rounded-sm border border-border">
              <TrendingUp size={24} strokeWidth={1.5} className="text-primary flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg mb-2">Time-Tested Truth</h3>
                <p className="text-sm text-muted-foreground">
                  Your contributions earn more reputation as they age well. Accuracy over time is rewarded.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Truth Labels */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="playfair text-3xl font-bold text-center mb-8">Non-Binary Truth Labels</h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
          Reality isn't black and white. Our 6-tier truth system reflects the nuance of evidence.
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="p-4 border rounded-sm" style={{backgroundColor: '#ECFDF5', borderColor: '#6EE7B7'}}>
            <p className="font-semibold" style={{color: '#065F46'}}>True</p>
            <p className="text-xs mt-1" style={{color: '#065F46'}}>Strong consensus with evidence</p>
          </div>
          <div className="p-4 border rounded-sm" style={{backgroundColor: '#F0FDF4', borderColor: '#86EFAC'}}>
            <p className="font-semibold" style={{color: '#166534'}}>Likely True</p>
            <p className="text-xs mt-1" style={{color: '#166534'}}>Preponderance of evidence</p>
          </div>
          <div className="p-4 border rounded-sm" style={{backgroundColor: '#FFFBEB', borderColor: '#FCD34D'}}>
            <p className="font-semibold" style={{color: '#92400E'}}>Mixed Evidence</p>
            <p className="text-xs mt-1" style={{color: '#92400E'}}>Conflicting quality evidence</p>
          </div>
          <div className="p-4 border rounded-sm" style={{backgroundColor: '#F3F4F6', borderColor: '#D1D5DB'}}>
            <p className="font-semibold" style={{color: '#374151'}}>Uncertain</p>
            <p className="text-xs mt-1" style={{color: '#374151'}}>Insufficient evidence</p>
          </div>
          <div className="p-4 border rounded-sm" style={{backgroundColor: '#FEF2F2', borderColor: '#FCA5A5'}}>
            <p className="font-semibold" style={{color: '#991B1B'}}>Likely False</p>
            <p className="text-xs mt-1" style={{color: '#991B1B'}}>Evidence leans against</p>
          </div>
          <div className="p-4 border rounded-sm" style={{backgroundColor: '#450A0A', borderColor: '#991B1B'}}>
            <p className="font-semibold" style={{color: '#FEF2F2'}}>False</p>
            <p className="text-xs mt-1" style={{color: '#FEF2F2'}}>Strong evidence of falsehood</p>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="border-t border-border">
        <div className="max-w-4xl mx-auto px-6 py-16 text-center">
          <h2 className="playfair text-3xl font-bold mb-4">Ready to Seek Truth?</h2>
          <p className="text-lg text-muted-foreground mb-8">
            Join academics, journalists, and truth-seekers building a transparent knowledge base.
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => navigate('/register')}
              className="px-8 py-4 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium text-lg"
            >
              Create Free Account
            </button>
            <button
              onClick={() => navigate('/feed')}
              className="px-8 py-4 bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-sm font-medium text-lg"
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