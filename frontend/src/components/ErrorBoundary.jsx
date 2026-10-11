import React from 'react';

/**
 * Standard React Error Boundary.
 * Catches rendering errors anywhere in child components and displays
 * a fallback UI instead of crashing the entire screen to blank.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('⚠️ [ErrorBoundary] Caught error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: '24px',
            margin: '20px',
            backgroundColor: '#161b22',
            border: '1px solid #f85149',
            borderRadius: '8px',
            color: '#f0f6fc',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>⚠️</div>
          <h3 style={{ color: '#f85149', margin: '0 0 8px 0' }}>Something went wrong</h3>
          <p style={{ color: '#8b949e', fontSize: '14px', margin: '0 0 16px 0' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred.'}
          </p>
          <button
            onClick={this.handleReset}
            style={{
              padding: '8px 18px',
              backgroundColor: '#238636',
              border: 'none',
              borderRadius: '6px',
              color: '#ffffff',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
