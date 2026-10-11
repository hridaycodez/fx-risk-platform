import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';

import ErrorBoundary from './components/ErrorBoundary';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('fx_token');
  return token ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <Provider store={store}>
      <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    </Provider>
  );
}

export default App;
