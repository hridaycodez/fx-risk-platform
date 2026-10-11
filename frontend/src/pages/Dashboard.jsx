import { useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setRates } from '../store/ratesSlice';
import {
  startSimulation,
  addChunk,
  completeSimulation,
  failSimulation,
} from '../store/simulationSlice';
import { useSocket, useSocketEvent } from '../hooks/useSocket';

import LiveRateTicker from '../components/LiveRateTicker';
import MonteCarloChart from '../components/MonteCarloChart';
import RiskMetricsCards from '../components/RiskMetricsCard';
import ScenarioSlider from '../components/ScenarioSlider';
import ExposureForm from '../components/ExposureForm';
import ErrorBoundary from '../components/ErrorBoundary';
import './Dashboard.css';

/**
 * Dashboard — the main simulation page.
 * Connects all components together with Socket.io real-time events.
 */
export default function Dashboard() {
  const dispatch = useDispatch();
  const { socket, connected, emit } = useSocket();
  const { status, exposures, baseCurrency } = useSelector((state) => state.simulation);
  const user = JSON.parse(localStorage.getItem('fx_user') || '{}');

  // ── Subscribe to live rates ─────────────────────────────────────────
  useEffect(() => {
    if (connected) {
      emit('subscribe_rates');
    }
  }, [connected, emit]);

  // ── Socket event handlers ───────────────────────────────────────────
  useSocketEvent(socket, 'rate_update', useCallback((data) => {
    dispatch(setRates(data));
  }, [dispatch]));

  useSocketEvent(socket, 'mc_chunk', useCallback((data) => {
    dispatch(addChunk(data));
  }, [dispatch]));

  useSocketEvent(socket, 'mc_complete', useCallback((metrics) => {
    dispatch(completeSimulation(metrics));
  }, [dispatch]));

  useSocketEvent(socket, 'mc_error', useCallback((data) => {
    dispatch(failSimulation(data?.message || 'Monte Carlo simulation failed'));
  }, [dispatch]));

  // ── Run Monte Carlo ─────────────────────────────────────────────────
  const handleRunSimulation = () => {
    if (exposures.length === 0) return alert('Please set portfolio exposures first!');
    if (status === 'running') return;
    if (!socket?.connected) {
      alert('Connecting to server... please wait a moment and try again.');
      return;
    }

    const iterations = 5000;
    dispatch(startSimulation({ iterations }));

    emit('run_montecarlo', {
      exposures: exposures.map((e) => ({
        name: e.name,
        exp_type: e.expType,
        amount: e.amount,
        currency: e.currency,
      })),
      iterations,
      baseCurrency,
    });
  };

  // ── What-If scenario handler ────────────────────────────────────────
  const handleScenarioChange = useCallback((shocks) => {
    if (exposures.length === 0) return;
    emit('what_if_scenario', {
      exposures: exposures.map((e) => ({
        name: e.name,
        exp_type: e.expType,
        amount: e.amount,
        currency: e.currency,
      })),
      shocks,
      baseCurrency,
    });
  }, [emit, exposures, baseCurrency]);

  const handleLogout = () => {
    localStorage.removeItem('fx_token');
    localStorage.removeItem('fx_user');
    window.location.href = '/login';
  };

  return (
    <div className="dashboard">
      {/* Live Rate Ticker — sticky top */}
      <LiveRateTicker />

      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1 className="dashboard-title">
            <span className="title-icon">📈</span>
            FX Risk Platform
          </h1>
          <span className="header-badge">LIVE</span>
        </div>
        <div className="header-right">
          <span className="user-name">👤 {user.name || 'User'}</span>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Left column — Inputs */}
        <section className="dashboard-left">
          <ExposureForm />
          <ScenarioSlider onScenarioChange={handleScenarioChange} />
        </section>

        {/* Right column — Charts & Metrics */}
        <section className="dashboard-right">
          {/* Run Simulation Button */}
          <button
            className={`run-btn ${status === 'running' ? 'running' : ''}`}
            onClick={handleRunSimulation}
            disabled={status === 'running' || exposures.length === 0}
          >
            {status === 'running' ? (
              <>⏳ Simulation Running...</>
            ) : (
              <>▶ Run Live Monte Carlo</>
            )}
          </button>

          {/* Monte Carlo Chart */}
          <ErrorBoundary>
            <MonteCarloChart />
          </ErrorBoundary>

          {/* Risk Metrics */}
          <ErrorBoundary>
            <RiskMetricsCards />
          </ErrorBoundary>
        </section>
      </main>
    </div>
  );
}
