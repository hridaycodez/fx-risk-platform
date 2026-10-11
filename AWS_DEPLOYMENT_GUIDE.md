# FX Risk Platform — AWS Cloud Production Deployment Guide

This guide provides end-to-end instructions for deploying the **FX Risk Platform** to AWS under the **AWS Free Tier / Student Account (AWS Academy / Learner Lab)** using an enterprise, decoupled cloud architecture designed for maximum resume impact.

---

## Architecture Overview

```
                        +---------------------------------------+
                        |           End User Browser            |
                        +---------------------------------------+
                                  /                   \
        HTTPS / Static Assets    /                     \   REST API / WebSockets
                                v                       v
               +-----------------------+      +-------------------------------+
               |     AWS CloudFront    |      |         AWS EC2 Instance       |
               |     (Global CDN)      |      |   (Ubuntu 22.04 LTS t2.micro) |
               +-----------------------+      |                               |
                           |                  |  +-------------------------+  |
                           v                  |  |  Node.js API Gateway    |  |
               +-----------------------+      |  |  (Express + Socket.io)  |  |
               |     AWS S3 Bucket     |      |  |  Port: 4000 / 80        |  |
               |  (React SPA Hosting)  |      |  +-------------------------+  |
               +-----------------------+      |               |               |
                                              |               v               |
                                              |  +-------------------------+  |
                                              |  |  FastAPI Python Engine  |  |
                                              |  |  (Monte Carlo / Greeks) |  |
                                              |  |  Port: 8000 (Internal)  |  |
                                              |  +-------------------------+  |
                                              +-------------------------------+
                                                              |
                                                              v
                                              +-------------------------------+
                                              |       MongoDB Atlas (M0)      |
                                              |       (Cloud Database)        |
                                              +-------------------------------+
```

---

## Phase 1: Launch & Configure AWS EC2 (Backend + ML Engine)

### Step 1: Launch EC2 Instance
1. Open the **AWS Management Console** and navigate to **EC2**.
2. Click **Launch Instance**.
3. Configure the following parameters:
   - **Name:** `fx-risk-backend`
   - **Application and OS Images (AMI):** `Ubuntu Server 22.04 LTS (HVM), SSD Volume Type` (64-bit x86).
   - **Instance Type:** `t2.micro` (Free Tier eligible) or `t3.micro`.
   - **Key Pair:** Select **Create new key pair**:
     - Key pair name: `fx-risk-key`
     - Private key file format: `.pem` (for OpenSSH / Mac / Linux / Windows PowerShell).
     - Click **Create key pair** and save the downloaded `fx-risk-key.pem` file to a secure directory (e.g., `~/.ssh/` or your project folder).
4. **Network Settings (Security Group):**
   - Click **Edit** and select **Create security group**.
   - Security group name: `fx-risk-backend-sg`
   - Description: `Security group for FX Risk Node API and ML Engine`
   - Add the following Inbound Rules:
     | Type | Protocol | Port Range | Source | Description |
     | :--- | :--- | :--- | :--- | :--- |
     | **SSH** | TCP | `22` | `My IP` (or `0.0.0.0/0`) | SSH administrative access |
     | **HTTP** | TCP | `80` | `Anywhere-IPv4 (0.0.0.0/0)` | Web HTTP traffic |
     | **Custom TCP** | TCP | `4000` | `Anywhere-IPv4 (0.0.0.0/0)` | Node.js Backend API & Socket.io |
5. **Storage:**
   - 1x 8 GiB gp3 (or gp2) Root volume (Free tier includes up to 30 GiB).
6. Click **Launch Instance**.

---

### Step 2: Connect to Your EC2 Instance
Once the instance status is **Running**:
1. Copy its **Public IPv4 address** (e.g., `54.210.120.45`).
2. Connect using one of two methods:
   - **Option A (AWS Console - Easiest):** Select your instance -> Click **Connect** -> Choose **EC2 Instance Connect** -> Click **Connect**. A terminal will open right in your web browser.
   - **Option B (SSH via Terminal / PowerShell):**
     ```bash
     chmod 400 fx-risk-key.pem   # Linux/macOS only
     ssh -i fx-risk-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
     ```

---

### Step 3: Run the EC2 Bootstrap Script
Inside your EC2 terminal:
```bash
# 1. Update packages and clone your repository (or download scripts)
git clone https://github.com/<YOUR_GITHUB_USERNAME>/fx-risk-platform.git
cd fx-risk-platform

# 2. Make the setup script executable and run it
chmod +x scripts/setup-ec2.sh
./scripts/setup-ec2.sh
```
> **What this does:**
> - Installs Docker Engine & the Docker Compose v2 plugin.
> - Adds user `ubuntu` to the `docker` group.
> - Creates and activates a **1GB Swapfile** (essential for preventing Out-Of-Memory crashes on `t2.micro` when compiling Python NumPy/SciPy containers).

Now log out and reconnect (or run `newgrp docker`) so Docker permissions take effect:
```bash
newgrp docker
```

---

### Step 4: Configure Production Backend Environment on EC2
Create the `backend/.env` file on your EC2 instance:
```bash
nano backend/.env
```
Paste the following (replace `<YOUR_MONGODB_URI>` and `<YOUR_JWT_SECRET>` with your actual values):
```ini
NODE_ENV=production
PORT=4000
PYTHON_ENGINE_URL=http://ml-engine:8000
MONGODB_URI=<YOUR_MONGODB_ATLAS_CONNECTION_STRING>
JWT_SECRET=super_secret_jwt_key_fx_risk_platform_2026
CORS_ORIGIN=*
RATES_PROVIDER=mock
UPDATE_INTERVAL_MS=3000
```
Press `Ctrl+O`, `Enter`, then `Ctrl+X` to save.

---

### Step 5: Start the Backend & ML Services via Docker
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Verify containers are healthy:
```bash
docker compose -f docker-compose.prod.yml ps
```
Test the healthcheck endpoint:
```bash
curl http://localhost:4000/health
# Expected Output: {"status":"healthy","timestamp":"...","environment":"production"}
```
Also verify in your browser: `http://<YOUR_EC2_PUBLIC_IP>:4000/health`.

---

## Phase 2: Deploy Frontend to AWS S3 & CloudFront

### Step 1: Create the S3 Bucket
1. Navigate to **Amazon S3** in the AWS Console.
2. Click **Create bucket**.
   - **Bucket name:** `fx-risk-frontend-<YOUR_INITIALS_OR_RANDOM_ID>` (must be globally unique, e.g., `fx-risk-frontend-hr-2026`).
   - **AWS Region:** Select `us-east-1` (N. Virginia) or your current region.
   - **Object Ownership:** ACLs disabled (recommended).
   - **Block Public Access settings:** Keep **Block all public access** checked (CloudFront will access the bucket securely via Origin Access Control).
3. Click **Create bucket**.

---

### Step 2: Create the CloudFront Distribution
1. Navigate to **CloudFront** in the AWS Console.
2. Click **Create distribution**.
3. **Origin Settings:**
   - **Origin domain:** Click the dropdown and select your newly created S3 bucket (e.g., `fx-risk-frontend-hr-2026.s3.us-east-1.amazonaws.com`).
   - **Origin access:** Select **Origin access control settings (recommended)**:
     - Click **Create new OAC** -> leave default name -> click **Create**.
4. **Default Cache Behavior:**
   - **Viewer protocol policy:** Select **Redirect HTTP to HTTPS**.
   - **Allowed HTTP methods:** `GET, HEAD`.
   - **Cache key and origin requests:** Select `CachingOptimized`.
5. **Settings:**
   - **Default root object:** Type `index.html`.
6. Click **Create distribution**.
7. **Copy S3 Bucket Policy:**
   - CloudFront will display a banner saying *"The S3 bucket policy needs to be updated"*.
   - Click **Copy policy**.
   - Go to your S3 bucket -> **Permissions** tab -> **Bucket policy** -> Click **Edit** -> Paste the policy -> Click **Save changes**.

---

### Step 3: Configure SPA Routing (Handling 403 / 404 in CloudFront)
Because React is a Single Page Application (SPA), routes like `/dashboard` must return `/index.html`:
1. In your CloudFront distribution, click the **Error pages** tab.
2. Click **Create custom error response**:
   - **HTTP error code:** `403: Forbidden`
   - **Customize error response:** Select `Yes`
   - **Response page path:** `/index.html`
   - **HTTP Response code:** `200: OK`
   - Click **Create error response**.
3. Repeat the same for `404: Not Found` (Response page path `/index.html`, HTTP response code `200`).

---

### Step 4: Build and Deploy the Frontend
On your local machine (or via CI/CD):
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Create or update `frontend/.env.production`:
   ```ini
   VITE_API_URL=http://<YOUR_EC2_PUBLIC_IP>:4000
   VITE_SOCKET_URL=http://<YOUR_EC2_PUBLIC_IP>:4000
   ```
3. Compile the production bundle:
   ```bash
   npm run build
   ```
4. Upload `frontend/dist/` to your S3 bucket:
   - **Via AWS CLI:**
     ```bash
     aws s3 sync dist/ s3://<YOUR_S3_BUCKET_NAME> --delete
     ```
   - **Via AWS Web Console:**
     - Open your bucket in AWS S3.
     - Click **Upload**.
     - Drag and drop all files and folders from inside `frontend/dist/` (including `index.html`, `assets/`, etc.).
     - Click **Upload**.

5. Invalidate CloudFront cache (to ensure fresh files):
   - In CloudFront -> **Invalidations** tab -> Click **Create invalidation** -> Enter `/*` -> Click **Create invalidation**.

6. Test your live application:
   - Open your CloudFront distribution domain name (e.g. `https://d123456abcdef8.cloudfront.net`).
   - Your FX Risk Platform is now live worldwide on AWS with HTTPS!

---

## Phase 3: Automated CI/CD with GitHub Actions

The repository includes a production workflow: `.github/workflows/deploy.yml`.

### Step 1: Add GitHub Repository Secrets
Go to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions** -> Click **New repository secret**.

Add the following 9 secrets:

| Secret Name | Value |
| :--- | :--- |
| `AWS_ACCESS_KEY_ID` | Your AWS IAM Access Key ID (from AWS Academy / Learner Lab / IAM) |
| `AWS_SECRET_ACCESS_KEY` | Your AWS IAM Secret Access Key |
| `AWS_SESSION_TOKEN` | *(Only required if using AWS Academy/Learner Lab temporary credentials)* |
| `AWS_REGION` | e.g. `us-east-1` |
| `S3_BUCKET_NAME` | e.g. `fx-risk-frontend-hr-2026` |
| `CLOUDFRONT_DISTRIBUTION_ID` | The ID of your CloudFront distribution (e.g. `E1A2B3C4D5E6F7`) |
| `EC2_HOST` | Your EC2 Public IPv4 Address (e.g. `54.210.120.45`) |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | The raw text of your `fx-risk-key.pem` private key file |
| `VITE_API_URL` | `http://<YOUR_EC2_PUBLIC_IP>:4000` |
| `VITE_SOCKET_URL` | `http://<YOUR_EC2_PUBLIC_IP>:4000` |

### Step 2: Trigger Deployment
Push any commit to `main` (or `master`):
```bash
git push origin master
```
GitHub Actions will automatically:
1. Run backend unit & integration tests.
2. Build the optimized React production bundle with your EC2 API URL.
3. Sync static assets to AWS S3.
4. Invalidate the AWS CloudFront edge cache.
5. SSH into your EC2 instance and trigger zero-downtime container updates via `docker compose pull && docker compose up -d`.

---

## Resume Showcase: Bullet Points & Portfolio Descriptions

Add these high-impact bullet points to your resume under Projects:

- **Distributed FX Risk Management Platform (AWS, Docker, React, Node.js, FastAPI, MongoDB)**
  - *Architected and deployed a multi-tier financial risk simulation platform running Monte Carlo Value-at-Risk (VaR) and Greeks analytics with real-time WebSocket streaming.*
  - *Engineered a decoupled cloud architecture on AWS using S3 and CloudFront for CDN-cached global static hosting, and containerized backend services (Node.js & FastAPI) orchestrated via Docker Compose on EC2 (Ubuntu).*
  - *Implemented automated CI/CD pipelines via GitHub Actions for automated unit testing, S3 deployment, CloudFront edge invalidation, and remote EC2 container redeployment.*
  - *Optimized low-memory resource utilization on AWS Free Tier (`t2.micro`) through OS-level swap partitioning and multi-stage Docker builds.*
