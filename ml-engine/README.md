# FX Risk Engine

A modular foreign exchange (FX) risk simulation and analytics engine. Computes profit & loss under various FX scenarios, runs Monte Carlo simulations, and calculates statistical risk metrics including Value at Risk (VaR) and Conditional VaR (CVaR).

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
│  POST /exposures  │  GET /scenarios  │  GET /health     │
│  POST /run_pnl    │  POST /run_sensitivity              │
│  POST /run_montecarlo                                   │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │   Service Layer       │
         │  (Session Store +     │
         │   Scenario Manager)   │
         └───────────┬───────────┘
                     │
    ┌────────────────▼────────────────┐
    │      Core Analytics Engine      │
    │  ┌─────────┐  ┌──────────────┐  │
    │  │ PnL     │  │ Sensitivity  │  │
    │  │ Engine  │  │ Engine       │  │
    │  └─────────┘  └──────────────┘  │
    │  ┌─────────┐  ┌──────────────┐  │
    │  │ Stress  │  │ Risk Metrics │  │
    │  │ Testing │  │ (VaR, CVaR)  │  │
    │  └─────────┘  └──────────────┘  │
    │  ┌──────────────────────────┐   │
    │  │  Monte Carlo Simulation  │   │
    │  │  (Independent + Cholesky)│   │
    │  └──────────────────────────┘   │
    └─────────────────────────────────┘
              │
    ┌─────────▼─────────┐
    │   Data Models      │
    │  Exposure │ Profile │
    │  Scenario │ Config  │
    └───────────────────┘
```

## 📁 Project Structure

```
fx_risk_engine/           # Core analytics engine
├── models/               # Data models (Exposure, Profile, Scenario)
├── analytics/            # PnL, sensitivity, stress, risk metrics
├── simulation/           # Monte Carlo (independent + correlated)
└── config/               # Settings & environment loader

api/                      # FastAPI backend
├── routers/              # Endpoint definitions
├── schemas/              # Pydantic request/response models
├── services/             # Business logic & session storage
└── dependencies/         # Dependency injection

ml/                       # ML scaffolding (stubs)
├── volatility_estimator.py
├── scenario_generator.py
└── risk_classifier.py

tests/                    # Test suite (pytest)
infra/                    # Docker & deployment
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+

### Installation
```bash
# Clone the repository
git clone <repo-url>
cd fx-risk-engine

# Install dependencies
make install
# or: pip install -r requirements.txt
```

### Run the API Server
```bash
# Development mode (with auto-reload)
make dev

# Production mode
make run
```

The API will be available at `http://localhost:8000`.
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Run Tests
```bash
make test
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `POST` | `/exposures` | Upload company FX exposures |
| `GET` | `/exposures` | List stored profiles |
| `GET` | `/scenarios` | List predefined + custom scenarios |
| `POST` | `/scenarios` | Create a custom scenario |
| `POST` | `/run_pnl` | Run deterministic P&L |
| `POST` | `/run_sensitivity` | Run sensitivity analysis |
| `POST` | `/run_montecarlo` | Run Monte Carlo simulation |

### Example: Upload Exposures
```bash
curl -X POST http://localhost:8000/exposures \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Acme Corp",
    "base_currency": "EUR",
    "exposures": [
      {"name": "US_Sales", "exp_type": "revenue", "amount": 500000, "currency": "USD"},
      {"name": "UK_Sales", "exp_type": "revenue", "amount": 200000, "currency": "GBP"},
      {"name": "JP_Parts", "exp_type": "cost", "amount": 10000000, "currency": "JPY"}
    ]
  }'
```

### Example: Run Monte Carlo
```bash
curl -X POST http://localhost:8000/run_montecarlo \
  -H "Content-Type: application/json" \
  -d '{
    "exposures": [
      {"name": "US_Sales", "exp_type": "revenue", "amount": 500000, "currency": "USD"},
      {"name": "JP_Parts", "exp_type": "cost", "amount": 10000000, "currency": "JPY"}
    ],
    "iterations": 5000,
    "seed": 42
  }'
```

## 🔧 Configuration

Configuration is loaded from the `.env` file. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_CURRENCY` | EUR | Company's reporting currency |
| `MC_ITERATIONS` | 1000 | Default Monte Carlo iterations |
| `LOSS_THRESHOLD_PERCENT` | 20.0 | Downside threshold (%) |
| `CONFIDENCE_LEVEL` | 0.95 | VaR/CVaR confidence level |
| `API_PORT` | 8000 | API server port |
| `DEBUG` | false | Enable debug mode |

## 🐳 Docker

```bash
# Build
make docker-build

# Run
make docker-run

# Or with Docker Compose
make compose-up
```

## 📊 Risk Metrics

The engine computes the following statistical risk metrics from Monte Carlo simulations:

- **Value at Risk (VaR)**: Maximum loss at 95% confidence
- **Conditional VaR (CVaR)**: Expected loss beyond VaR threshold
- **Downside Probability**: Probability of exceeding loss threshold
- **Profit at Risk**: Difference between base profit and VaR
- **Sharpe-like Ratio**: Mean profit / volatility
- **Skewness & Kurtosis**: Distribution shape metrics

## 📋 License

MIT License
