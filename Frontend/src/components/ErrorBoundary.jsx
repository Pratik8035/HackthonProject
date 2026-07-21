import React from 'react';
import { MdErrorOutline } from 'react-icons/md';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // You can also log the error to an error reporting service
    console.error("ErrorBoundary caught an error", error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div className="d-flex flex-column justify-content-center align-items-center vh-100 p-4 text-center">
          <div className="glass-card shadow-lg border-danger p-5" style={{ maxWidth: '600px' }}>
            <MdErrorOutline size={80} className="text-danger mb-4" />
            <h2 className="fw-bold text-danger mb-3">Something went wrong.</h2>
            <p className="text-muted mb-4">A critical error occurred while rendering this page.</p>
            <div className="bg-dark text-danger p-3 rounded text-start overflow-auto" style={{ maxHeight: '200px' }}>
              <code>{this.state.error && this.state.error.toString()}</code>
              <br />
              <code className="small text-muted">{this.state.errorInfo?.componentStack}</code>
            </div>
            <button className="btn btn-danger mt-4 rounded-pill px-4 py-2 fw-bold" onClick={() => window.location.reload()}>
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children; 
  }
}

export default ErrorBoundary;
