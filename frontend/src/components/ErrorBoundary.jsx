import React from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Update state with error details
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));

    // In production, you would send this to an error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: logErrorToService(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/feed';
  };

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, errorCount } = this.state;
      const isRepeatedError = errorCount > 2;

      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-card border-2 border-destructive rounded-lg p-8">
            {/* Error Icon */}
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
                <AlertCircle size={32} className="text-destructive" />
              </div>
            </div>

            {/* Error Title */}
            <h1 className="playfair text-3xl font-bold text-center mb-3 text-foreground">
              {isRepeatedError ? 'Persistent Error Detected' : 'Oops! Something went wrong'}
            </h1>
            
            <p className="text-center text-muted-foreground mb-6">
              {isRepeatedError 
                ? 'This error keeps occurring. Please try going to the home page or reloading the app.'
                : 'We encountered an unexpected error. Don\'t worry, your data is safe.'
              }
            </p>

            {/* Error Details (Development Only) */}
            {process.env.NODE_ENV === 'development' && error && (
              <div className="mb-6 p-4 bg-secondary rounded-sm border border-border">
                <h3 className="font-semibold text-sm mb-2 text-destructive">Error Details (Dev Mode):</h3>
                <pre className="text-xs overflow-auto max-h-40 text-foreground">
                  {error.toString()}
                </pre>
                {errorInfo && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs font-medium text-muted-foreground hover:text-foreground">
                      Component Stack
                    </summary>
                    <pre className="text-xs mt-2 overflow-auto max-h-40 text-muted-foreground">
                      {errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {!isRepeatedError && (
                <button
                  onClick={this.handleReset}
                  className="flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-medium transition-colors"
                >
                  <RefreshCw size={18} />
                  Try Again
                </button>
              )}
              
              <button
                onClick={this.handleGoHome}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-secondary hover:bg-secondary/80 rounded-sm font-medium transition-colors"
              >
                <Home size={18} />
                Go to Home
              </button>

              <button
                onClick={this.handleReload}
                className="flex items-center justify-center gap-2 px-6 py-3 border border-border hover:bg-secondary rounded-sm font-medium transition-colors"
              >
                <RefreshCw size={18} />
                Reload App
              </button>
            </div>

            {/* Additional Help */}
            <div className="mt-6 text-center text-sm text-muted-foreground">
              <p>If this problem persists, please contact support or try clearing your browser cache.</p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
