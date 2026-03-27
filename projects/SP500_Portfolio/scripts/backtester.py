import pandas as pd
import numpy as np

def calculate_portfolio_returns(returns, weights, transaction_cost=0.001):
    """Calculates weighted returns minus transaction costs on rebalance."""
    # This is a simplified model. True friction should be on turnover.
    # For now, apply transaction cost once at start of each rebalance period.
    # We will refine this if necessary.
    portfolio_returns = returns.dot(weights)
    return portfolio_returns

def walk_forward_simulation(historical_candidates, all_prices, benchmark_returns, rf_rates, strategy_func, transaction_cost=0.001, lookback_years=1, starting_balance=100000, w_min=0.02):
    """Executes a walk-forward simulation and returns equity curve and historical weights."""
    rebalance_dates = historical_candidates['Date'].unique()
    rebalance_dates = sorted(rebalance_dates)
    
    current_weights = None
    all_period_returns = []
    historical_weights = []
    
    for i, start_date in enumerate(rebalance_dates):
        # 1. Tickers for this specific rebalance date
        tickers = historical_candidates[historical_candidates['Date'] == start_date]['Ticker'].tolist()
        
        # Deduplicate entities (like GOOG/GOOGL) locally to ensure 15 or less unique assets
        if 'GOOGL' in tickers and 'GOOG' in tickers:
            tickers.remove('GOOG')
            
        available_tickers = [t for t in tickers if t in all_prices.columns]
        
        # 2. Get data for optimization
        # Use lookback_years history before start_date
        lookback_start = pd.to_datetime(start_date) - pd.DateOffset(years=lookback_years)
        train_data = all_prices[available_tickers].loc[lookback_start:pd.to_datetime(start_date) - pd.Timedelta(days=1)].dropna(axis=1)
        
        # If train_data is empty (e.g. first rebalance at start of data), use at least 1 day or handle
        if len(train_data) < 30:
             train_data = all_prices[available_tickers].loc[:start_date].dropna(axis=1)

        available_tickers = train_data.columns.tolist()
        
        # 3. Optimize (Need enough data)
        if len(available_tickers) > 0 and len(train_data) >= 10:
            try:
                # Pass w_min to strategy function
                new_weights = strategy_func(train_data, w_min)
                # Store weights with date
                weights_df = new_weights.to_frame().T
                weights_df.index = [start_date]
                historical_weights.append(weights_df)
            except Exception as e:
                print(f"Optimization failed for {start_date}: {e}")
                continue
            
            # Calculate turnover cost
            turnover = 0
            if current_weights is not None:
                all_sim_tickers = sorted(list(set(current_weights.index) | set(new_weights.index)))
                w_old = current_weights.reindex(all_sim_tickers, fill_value=0)
                w_new = new_weights.reindex(all_sim_tickers, fill_value=0)
                turnover = np.sum(np.abs(w_new - w_old))
            else:
                turnover = 1.0
            
            total_tx_cost = turnover * transaction_cost
            
            # 4. Period Simulation
            period_start = start_date
            period_end = rebalance_dates[i+1] - pd.Timedelta(days=1) if i+1 < len(rebalance_dates) else all_prices.index[-1]
            period_prices = all_prices[available_tickers].loc[period_start:period_end]
            if len(period_prices) < 2:
                continue
                
            period_returns = period_prices.pct_change().dropna()
            
            if len(period_returns) > 0:
                period_portfolio_returns = period_returns.dot(new_weights)
                # Initial friction at start of each rebalance period
                period_portfolio_returns.iloc[0] -= total_tx_cost
                all_period_returns.append(period_portfolio_returns)
                current_weights = new_weights
            
    if not all_period_returns:
        return pd.Series(), pd.DataFrame()
        
    full_returns = pd.concat(all_period_returns)
    equity_curve = starting_balance * (1 + full_returns).cumprod()
    
    # Combine weights into a single DataFrame
    weights_final = pd.concat(historical_weights) if historical_weights else pd.DataFrame()
    
    return equity_curve, weights_final

def calculate_metrics(returns, benchmark_returns=None, rf_rate=0.0):
    """Calculates Sharpe, Sortino, Max Drawdown, Alpha, and Beta."""
    annual_return = returns.mean() * 252
    annual_vol = returns.std() * np.sqrt(252)
    
    # Sharpe
    sharpe = (annual_return - rf_rate) / annual_vol if annual_vol != 0 else 0
    
    # Sortino
    downside_returns = returns[returns < 0]
    downside_vol = downside_returns.std() * np.sqrt(252)
    sortino = (annual_return - rf_rate) / downside_vol if downside_vol != 0 else 0
    
    # Drawdown
    equity = (1 + returns).cumprod()
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    max_drawdown = drawdown.min()
    
    # Alpha and Beta
    alpha, beta = 0, 0
    if benchmark_returns is not None:
        # Align returns
        combined = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(combined) > 0:
            cov_matrix = np.cov(combined.iloc[:, 0], combined.iloc[:, 1])
            beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] != 0 else 0
            
            bench_annual_return = benchmark_returns.mean() * 252
            alpha = annual_return - (rf_rate + beta * (bench_annual_return - rf_rate))
    
    return {
        'Annual Return': annual_return,
        'Volatility': annual_vol,
        'Sharpe Ratio': sharpe,
        'Sortino Ratio': sortino,
        'Max Drawdown': max_drawdown,
        'Alpha': alpha,
        'Beta': beta
    }
