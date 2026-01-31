import React from 'react';
import { useNavigate } from 'react-router-dom';

const Welcome = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Minimal Header */}
      <header className="px-8 py-6 flex justify-between items-center">
        <h1 className="playfair text-2xl font-semibold tracking-tight text-slate-900">
          Thrryv
        </h1>
        <div className="flex gap-4">
          <button
            onClick={() => navigate('/login')}
            className="px-5 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={() => navigate('/register')}
            className="px-5 py-2 text-sm font-medium bg-slate-900 text-white hover:bg-slate-800 transition-colors"
          >
            Join
          </button>
        </div>
      </header>

      {/* Main Content - Centered with generous whitespace */}
      <main className="flex-1 flex items-center justify-center px-8">
        <div className="max-w-3xl w-full">
          {/* Subtle visual cue - credibility scale */}
          <div className="mb-16 flex items-center justify-center">
            <div className="relative w-64 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div 
                className="absolute inset-y-0 left-0 rounded-full transition-all duration-[3000ms] ease-out"
                style={{
                  width: '75%',
                  background: 'linear-gradient(90deg, rgba(100,116,139,0.3) 0%, rgba(71,85,105,0.6) 50%, rgba(51,65,85,0.8) 100%)'
                }}
              />
            </div>
          </div>

          {/* The carefully crafted paragraph */}
          <div className="text-center space-y-8">
            <p className="text-xl md:text-2xl leading-relaxed text-slate-700 font-light tracking-wide">
              Ideas, images, and short videos arrive here and remain—unchanged, examined. 
              Others bring evidence, add context, question gently. Over time, patterns emerge. 
              What holds up under scrutiny rises. What doesn't, settles. There's no rush, 
              no viral pull, no performative certainty. Just the gradual work of understanding: 
              layered, open, earned through attention rather than declared by authority.
            </p>

            {/* Minimal CTA */}
            <div className="pt-8">
              <button
                onClick={() => navigate('/feed')}
                className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors border-b border-slate-300 hover:border-slate-900 pb-1"
              >
                See what's being examined
              </button>
            </div>
          </div>

          {/* Subtle bottom visual element */}
          <div className="mt-24 flex justify-center space-x-1">
            <div className="w-1.5 h-1.5 rounded-full bg-slate-300" />
            <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            <div className="w-1.5 h-1.5 rounded-full bg-slate-500" />
          </div>
        </div>
      </main>

      {/* Minimal Footer */}
      <footer className="px-8 py-6 text-center">
        <p className="text-xs text-slate-400 font-light tracking-wider">
          CREDIBILITY, BUILT GRADUALLY
        </p>
      </footer>
    </div>
  );
};

export default Welcome;
