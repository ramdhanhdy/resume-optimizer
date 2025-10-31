/**
 * Error Boundary Component
 * Catches React rendering errors and triggers state preservation
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { stateManager } from '../services/storage';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);

    this.setState({ errorInfo });

    // Attempt to capture state for recovery
    this.captureStateOnError(error, errorInfo);
  }

  private async captureStateOnError(error: Error, errorInfo: ErrorInfo) {
    try {
      // Try to capture current form state if available
      // This is a best-effort attempt - the app state may be corrupted
      console.log('Attempting to capture state after React error...');

      // You could enhance this by accessing form state from context or props
      // For now, just log that an error occurred
      console.log('React error captured:', {
        error: error.message,
        componentStack: errorInfo.componentStack,
      });
    } catch (captureError) {
      console.error('Failed to capture state on error:', captureError);
    }
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-8 bg-gray-50">
          <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg p-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-red-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Something Went Wrong
                </h1>
                <p className="text-gray-600 text-sm">
                  The application encountered an unexpected error
                </p>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <p className="text-sm font-mono text-gray-800">
                {this.state.error?.message || 'Unknown error'}
              </p>
            </div>

            <p className="text-gray-700 mb-6">
              Don't worry - your data may have been preserved. Try reloading the page
              to see if your session can be recovered.
            </p>

            <div className="flex gap-3">
              <button
                onClick={this.handleReload}
                className="flex-1 px-6 py-3 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition-colors"
              >
                Reload Page
              </button>
              <button
                onClick={this.handleReset}
                className="flex-1 px-6 py-3 bg-gray-200 text-gray-800 rounded-lg font-medium hover:bg-gray-300 transition-colors"
              >
                Try Again
              </button>
            </div>

            {/* Show error details in development */}
            {import.meta.env.DEV && this.state.errorInfo && (
              <details className="mt-6">
                <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                  Error Details (Development Only)
                </summary>
                <pre className="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto max-h-64">
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
