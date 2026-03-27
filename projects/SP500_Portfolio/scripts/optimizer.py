import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, risk_models, expected_returns, HRPOpt
from scipy.optimize import minimize

def deduplicate_entities(tickers):
    """Exclude dual-class shares like GOOG if GOOGL is present."""
    if 'GOOGL' in tickers and 'GOOG' in tickers:
        tickers.remove('GOOG')
    return tickers

def get_performance_model(prices):
    """Estimates expected returns and risk using Ledoit-Wolf Shrinkage."""
    mu = expected_returns.mean_historical_return(prices)
    S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
    return mu, S

def optimize_sharpe(prices, w_min=0.02, w_max=0.25):
    """Optimizes for maximum Sharpe Ratio using a two-pass heuristic."""
    mu, S = get_performance_model(prices)
    
    # Pass 1: Optimize with bounds (0, w_max)
    try:
        ef = EfficientFrontier(mu, S, weight_bounds=(0.0, w_max))
        ef.max_sharpe()
        weights_pass1 = pd.Series(ef.clean_weights())
    except Exception as e:
        print(f"Sharpe optimization pass 1 error: {e}")
        n = len(prices.columns)
        return pd.Series([1.0/n]*n, index=prices.columns)

    # Filter dust
    dust_mask = (weights_pass1 > 1e-5) & (weights_pass1 < w_min)
    if not dust_mask.any():
        return weights_pass1
        
    # Pass 2: Force dust to 0, others to >= w_min
    bounds = []
    for ticker in prices.columns:
        if dust_mask[ticker]:
            bounds.append((0.0, 0.0))
        else:
            bounds.append((w_min, w_max))
            
    try:
        ef2 = EfficientFrontier(mu, S, weight_bounds=bounds)
        ef2.max_sharpe()
        return pd.Series(ef2.clean_weights())
    except Exception as e:
        print(f"Sharpe optimization pass 2 error: {e}")
        # Fallback to normalized pass 1 weights if pass 2 fails
        weights_clean = weights_pass1.copy()
        weights_clean[dust_mask] = 0.0
        if weights_clean.sum() > 0:
            return weights_clean / weights_clean.sum()
        n = len(prices.columns)
        return pd.Series([1.0/n]*n, index=prices.columns)

def optimize_hrp(prices, w_min=0.02):
    """Optimizes using Hierarchical Risk Parity with an iterative dust filter."""
    returns = prices.pct_change().dropna()
    hrp = HRPOpt(returns)
    weights = hrp.optimize()
    clean_w = pd.Series(hrp.clean_weights())
    
    # Iterative dust filter
    if w_min > 0:
        while ((clean_w > 1e-5) & (clean_w < w_min)).any():
            dust_mask = (clean_w > 1e-5) & (clean_w < w_min)
            clean_w[dust_mask] = 0.0
            if clean_w.sum() > 0:
                clean_w = clean_w / clean_w.sum()
            else:
                break
                
    return clean_w

def optimize_sortino(prices, w_min=0.02, rf_rate=0.0, w_max=0.25):
    """Optimizes for maximum Sortino Ratio using a two-pass heuristic."""
    returns = prices.pct_change().dropna()
    num_assets = prices.shape[1]
    
    def sortino_objective(weights):
        portfolio_returns = returns.dot(weights)
        excess_returns = portfolio_returns - rf_rate
        avg_excess = np.mean(excess_returns)
        # Downside risk
        downside_returns = np.minimum(excess_returns, 0)
        downside_vol = np.sqrt(np.mean(downside_returns**2)) * np.sqrt(252)
        if downside_vol == 0:
            return 0
        return - (avg_excess * 252) / downside_vol

    constraints = [
        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
    ]
    
    # Pass 1: bounds (0, w_max)
    bounds_pass1 = [(0.0, w_max) for _ in range(num_assets)]
    initial_weights = np.array([1.0 / num_assets] * num_assets)
    
    result1 = minimize(sortino_objective, initial_weights, method='SLSQP', bounds=bounds_pass1, constraints=constraints)
    weights_pass1 = pd.Series(result1.x, index=prices.columns)
    
    # Filter dust
    dust_mask = (weights_pass1 > 1e-4) & (weights_pass1 < w_min)
    if not dust_mask.any():
        return weights_pass1
        
    # Pass 2: Force dust to 0, others to >= w_min
    bounds_pass2 = []
    for ticker in prices.columns:
        if dust_mask[ticker]:
            bounds_pass2.append((0.0, 0.0))
        else:
            bounds_pass2.append((w_min, w_max))
            
    # Try Pass 2 - Recalculate initial weights
    valid_assets = sum(1 for b in bounds_pass2 if b[1] > 0)
    if valid_assets == 0:
         return weights_pass1 # fallback
         
    init_w2 = [1.0 / valid_assets if b[1] > 0 else 0.0 for b in bounds_pass2]
    
    result2 = minimize(sortino_objective, np.array(init_w2), method='SLSQP', bounds=bounds_pass2, constraints=constraints)
    if result2.success:
        return pd.Series(result2.x, index=prices.columns)
    else:
        # Fallback
        weights_clean = weights_pass1.copy()
        weights_clean[dust_mask] = 0.0
        if weights_clean.sum() > 0:
            return weights_clean / weights_clean.sum()
        return weights_pass1
