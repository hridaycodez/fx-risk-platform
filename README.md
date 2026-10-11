# FX Risk Platform — Quantitative Risk & Portfolio Analytics Platform

![Architecture](https://img.shields.io/badge/Architecture-Decoupled%20Cloud-blue?style=for-the-badge)
![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20CloudFront%20%7C%20EC2-orange?style=for-the-badge&logo=amazon-aws)
![Docker](https://img.shields.io/badge/Docker-Compose%20v2-2496ED?style=for-the-badge&logo=docker)
![Node.js](https://img.shields.io/badge/Node.js-Express%20%7C%20Socket.io-339933?style=for-the-badge&logo=node.js)
![Python](https://img.shields.io/badge/Python-FastAPI%20%7C%20NumPy%20%7C%20SciPy-3776AB?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite%20%7C%20Recharts-61DAFB?style=for-the-badge&logo=react)

An enterprise-grade Foreign Exchange (FX) Quantitative Risk Platform capable of computing real-time Value at Risk (VaR), Conditional Value at Risk (CVaR / Expected Shortfall), Greeks sensitivities (Delta, Gamma, Vega, Theta, Rho), and streaming live Monte Carlo simulations across multi-currency portfolios.

---

## Key Features

- **Monte Carlo Risk Engine:** 10,000+ path vectorized simulations parameterized via Geometric Brownian Motion (GBM) with correlated multi-asset returns.
- **Parametric & Historical VaR / CVaR:** 95% and 99% confidence level loss forecasting with interactive shock sliders (+/- 20% currency moves).
- **Greeks & Sensitivity Matrix:** Closed-form Garman-Kohlhagen FX option Greeks and portfolio Delta/Gamma aggregation.
- **Real-Time Market Data & Streaming:** Live socket streams (`Socket.io`) broadcasting pricing ticks and real-time PnL recalculations.
- **Modern Institutional UI:** Dark-mode dashboard built with React 18, Recharts financial visualizations, and responsive metric cards.
- **Enterprise Cloud Deployment:** Fully containerized microservices architecture hosted across AWS (S3, CloudFront, EC2) with automated GitHub Actions CI/CD.

---

## High-Level Architecture

```
                    +-----------------------------+
                    |      User / Client          |
                    +-----------------------------+
                               /               \
         CloudFront CDN (HTTPS)                 WebSockets / REST
                             v                   v
                    +----------------+  +-------------------------------+
                    |  AWS S3 Bucket |  |       AWS EC2 (Ubuntu 22.04)  |
                    |  (React SPA)   |  |                               |
                    +----------------+  |  +-------------------------+  |
                                        |  | Node.js API Gateway     |  |
                                        |  | (Express + Socket.io)   |  |
                                        |  | Port: 4000 / 80         |  |
                                        |  +-------------------------+  |
                                        |               |               |
                                        |               v               |
                                        |  +-------------------------+  |
                                        |  | Python FastAPI Engine   |  |
                                        |  | (Monte Carlo & Greeks)  |  |
                                        |  | Port: 8000              |  |
                                        |  +-------------------------+  |
                                        +-------------------------------+
                                                        |
                                                        v
                                        +-------------------------------+
                                        |    MongoDB Atlas Cloud DB     |
                                        +-------------------------------+
```

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Recharts, Lucide Icons, Redux Toolkit, Socket.io Client |
| **API Gateway** | Node.js, Express, Socket.io, Mongoose, JWT Authentication |
| **Quantitative Engine** | Python 3.11, FastAPI, NumPy, SciPy, Pandas, Uvicorn |
| **Database** | MongoDB Atlas (Cloud M0 Cluster) |
| **Containerization** | Docker Engine, Docker Compose v2, Multi-stage builds |
| **Cloud Hosting** | AWS S3, AWS CloudFront, AWS EC2 (Ubuntu 22.04 LTS), AWS IAM |
| **CI/CD** | GitHub Actions (automated test, build, S3 sync, CloudFront invalidation, SSH deploy) |

---

## Quick Start (Local Development)

### Prerequisites
- Node.js 18+ & npm
- Python 3.10+
- Docker & Docker Compose (optional, for containerized run)

### Running with Docker Compose (Recommended)
```bash
# Clone the repository
git clone https://github.com/<YOUR_USERNAME>/fx-risk-platform.git
cd fx-risk-platform

# Launch all microservices
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Node.js API: `http://localhost:4000`
- Python ML Engine: `http://localhost:8000/docs` (Swagger UI)

### Running Microservices Manually

#### 1. Python ML Engine
```bash
cd ml-engine
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Node.js Backend Gateway
```bash
cd backend
cp .env.example .env
npm install
npm run dev
```

#### 3. React Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

---

## Cloud Deployment Guide

For full step-by-step instructions on deploying this platform to **AWS** under the **Free Tier / Student Account** (EC2, S3, CloudFront, GitHub Actions), refer to:
👉 [AWS Deployment Guide](AWS_DEPLOYMENT_GUIDE.md)

---

## License
MIT License
