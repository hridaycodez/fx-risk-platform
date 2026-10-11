#!/usr/bin/env bash
# ==============================================================================
# FX Risk Platform - EC2 Bootstrap & Setup Script (Ubuntu 22.04)
# ==============================================================================
set -e

echo "=================================================="
echo "🚀 1. Updating System Packages..."
echo "=================================================="
sudo apt-get update -y
sudo apt-get upgrade -y

echo "=================================================="
echo "🐳 2. Installing Docker & Docker Compose..."
echo "=================================================="
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# Add Docker official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Allow current user to run docker without sudo
sudo usermod -aG docker "$USER"

echo "=================================================="
echo "⚙️ 3. Configuring Swap Space (1GB) for t2.micro stability"
echo "=================================================="
if [ ! -f /swapfile ]; then
    sudo fallocate -l 1G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap configured"
fi

echo "=================================================="
echo "✅ EC2 Setup Complete!"
echo "NOTE: Log out and log back in (or run 'newgrp docker') to apply docker group changes."
echo "=================================================="
