import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Login.css';

export default function Login() {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isRegister ? '/auth/register' : '/auth/login';
      const payload = isRegister ? form : { email: form.email, password: form.password };
      const { data } = await api.post(endpoint, payload);

      localStorage.setItem('fx_token', data.token);
      localStorage.setItem('fx_user', JSON.stringify(data.user));
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/auth/demo');
      localStorage.setItem('fx_token', data.token);
      localStorage.setItem('fx_user', JSON.stringify(data.user));
      navigate('/');
    } catch (err) {
      setError('Demo login failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <span className="login-icon">📈</span>
          <h1>FX Risk Platform</h1>
          <p className="login-subtitle">
            Live Monte Carlo Simulation & Risk Analytics
          </p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {isRegister && (
            <input
              type="text"
              name="name"
              placeholder="Full Name"
              value={form.name}
              onChange={handleChange}
              required
              className="login-input"
            />
          )}
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={form.email}
            onChange={handleChange}
            required
            className="login-input"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={form.password}
            onChange={handleChange}
            required
            minLength={6}
            className="login-input"
          />

          {error && <p className="login-error">⚠ {error}</p>}

          <button type="submit" className="login-submit" disabled={loading}>
            {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="login-divider">
          <span>or</span>
        </div>

        <button className="demo-btn" onClick={handleDemoLogin} disabled={loading}>
          🚀 Try Demo (No signup needed)
        </button>

        <p className="login-toggle">
          {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button type="button" onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? 'Sign In' : 'Register'}
          </button>
        </p>

        <div className="login-currencies">
          <span>🇪🇺 EUR</span>
          <span>🇺🇸 USD</span>
          <span>🇬🇧 GBP</span>
          <span>🇮🇳 INR</span>
          <span>🇦🇪 AED</span>
          <span>🇯🇵 JPY</span>
          <span>🇨🇭 CHF</span>
        </div>
      </div>
    </div>
  );
}
