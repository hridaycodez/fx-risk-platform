"""
train_models.py — One-time ML Model Training Script
=====================================================
Run ONCE on your laptop to train and save models:
    python ml/train_models.py

Trains two models:
  1. Risk Classifier (Random Forest) — classifies simulation outcomes as LOW/MEDIUM/HIGH
  2. Volatility Estimator (statistical) — estimates forward-looking volatility

Total training time: < 5 minutes on any laptop. No GPU needed.
Saved models are committed to the repo and loaded at runtime for millisecond inference.
"""

import os
import sys
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Add parent directory so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trained_models")


def train_risk_classifier():
    """
    Train a Random Forest classifier on synthetic simulation data.
    
    Features (per simulation run):
        - downside_probability (%)
        - var_95 / mean_profit ratio
        - portfolio_volatility (std / mean)
        - sharpe_ratio
    
    Labels:
        - LOW:    downside_prob < 15% AND loss_ratio < 0.25
        - MEDIUM: 15% <= downside_prob < 30% OR 0.25 <= loss_ratio < 0.5
        - HIGH:   downside_prob >= 30% OR loss_ratio >= 0.5
    """
    print("=" * 60)
    print("🤖 Training Risk Classifier (Random Forest)")
    print("=" * 60)

    np.random.seed(42)
    n_samples = 50000

    # Generate synthetic features
    downside_prob   = np.random.uniform(0, 60, n_samples)      # 0-60%
    loss_ratio      = np.random.uniform(0, 1.0, n_samples)     # |VaR| / |mean|
    portfolio_vol   = np.random.uniform(0.01, 0.5, n_samples)  # std / mean
    sharpe_ratio    = np.random.uniform(-1.0, 3.0, n_samples)  # mean / std

    X = np.column_stack([downside_prob, loss_ratio, portfolio_vol, sharpe_ratio])

    # Label based on rules (ground truth for training)
    labels = []
    for i in range(n_samples):
        dp = downside_prob[i]
        lr = loss_ratio[i]
        sr = sharpe_ratio[i]

        if dp >= 30 or lr >= 0.5 or sr < 0:
            labels.append("HIGH")
        elif dp >= 15 or lr >= 0.25 or sr < 0.5:
            labels.append("MEDIUM")
        else:
            labels.append("LOW")

    y = np.array(labels)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        n_jobs=-1,  # Use all CPU cores
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    accuracy = clf.score(X_test, y_test)
    print(f"✅ Accuracy: {accuracy:.4f}")

    # Feature importance
    feature_names = ["downside_prob", "loss_ratio", "portfolio_vol", "sharpe_ratio"]
    importances = clf.feature_importances_
    print("\nFeature Importances:")
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
        print(f"  {name}: {imp:.4f}")

    # Save model
    model_path = os.path.join(MODELS_DIR, "risk_classifier.joblib")
    joblib.dump(clf, model_path)
    file_size = os.path.getsize(model_path) / (1024 * 1024)
    print(f"\n💾 Model saved: {model_path} ({file_size:.2f} MB)")

    return clf


def train_volatility_estimator():
    """
    Train a simple volatility estimator.
    
    Uses exponentially weighted moving average (EWMA) approach rather than
    a full GARCH model to avoid the heavy `arch` dependency.
    This is a lightweight statistical estimator, not deep learning.
    
    Saves the estimator parameters for use at runtime.
    """
    print("\n" + "=" * 60)
    print("📈 Training Volatility Estimator (EWMA)")
    print("=" * 60)

    # Generate synthetic daily returns for each currency pair
    np.random.seed(123)
    n_days = 1260  # ~5 years of trading days

    vol_models = {}
    for ccy in config.SUPPORTED_CURRENCIES:
        base_vol = config.FX_VOLATILITY[ccy]
        
        # Simulate daily returns with time-varying volatility
        daily_vol = base_vol / np.sqrt(252)  # annualized → daily
        returns = np.random.normal(0, daily_vol, n_days)
        
        # Fit EWMA (lambda = 0.94 is the RiskMetrics standard)
        ewma_lambda = 0.94
        variance = np.zeros(n_days)
        variance[0] = returns[0] ** 2
        for t in range(1, n_days):
            variance[t] = ewma_lambda * variance[t - 1] + (1 - ewma_lambda) * returns[t] ** 2

        current_daily_vol = np.sqrt(variance[-1])
        current_annual_vol = current_daily_vol * np.sqrt(252)

        vol_models[ccy] = {
            "ewma_lambda": ewma_lambda,
            "current_daily_vol": round(float(current_daily_vol), 6),
            "current_annual_vol": round(float(current_annual_vol), 4),
            "base_annual_vol": base_vol,
            "training_days": n_days,
        }
        print(f"  {ccy}: annual vol = {current_annual_vol:.4f} (base: {base_vol})")

    # Save volatility model parameters
    model_path = os.path.join(MODELS_DIR, "volatility_model.joblib")
    joblib.dump(vol_models, model_path)
    file_size = os.path.getsize(model_path) / 1024
    print(f"\n💾 Model saved: {model_path} ({file_size:.2f} KB)")

    return vol_models


if __name__ == "__main__":
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("🚀 FX Risk Engine — ML Model Training")
    print(f"   Models will be saved to: {MODELS_DIR}\n")

    clf = train_risk_classifier()
    vol_models = train_volatility_estimator()

    print("\n" + "=" * 60)
    print("✅ ALL MODELS TRAINED SUCCESSFULLY")
    print("   You can now start the platform — models load at runtime")
    print("   and predict in milliseconds. No re-training needed!")
    print("=" * 60)
