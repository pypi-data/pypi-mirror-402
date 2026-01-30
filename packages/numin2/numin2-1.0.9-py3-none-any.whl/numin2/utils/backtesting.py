import posix
import numpy as np
import torch

def compute_pnl(new_positions, old_positions, returns, txn_cost=.1):
    """
    Computes PnL for a single day/batch based on positions and raw targets.
    positions: (51,) array of {p, -q, 0} - with 'Cash' at position 0.
    Returns are returns e.g. (50,0) for theNifty 50 stocks, a Torch Tensor
    """
    sum_new = sum([abs(p) for p in new_positions])
    sum_old = sum([abs(p) for p in new_positions])
    positions = new_positions/sum_new ## positions as allocation weights
    old_positions = old_positions/sum_old ## positions as allocation weights
    
    targets = torch.concat([torch.zeros(1),returns]) # add zero return for cash

    targets = targets.cpu().numpy().flatten() # (51,) raw returns
    
    long_indices = np.where(positions > 0)[0]
    short_indices = np.where(positions < 0)[0]
    
    # Calculate Profit
    incremental_pnl = 0.0
    
    total_long = 0.0
    if len(long_indices) > 0:
        total_long = np.sum(targets[long_indices]*positions[long_indices])
        
    total_short = 0.0
    if len(short_indices) > 0:
        total_short = np.sum(targets[short_indices]*positions[short_indices])
    
    total_positions = len(long_indices) + len(short_indices)
    total_positions = sum(positions[long_indices])-sum(positions[short_indices])
    
    if total_positions > 0:
        incremental_pnl = ((total_long + total_short) / total_positions)
    else:
        incremental_pnl = 0.0
        
    transaction_costL = [abs(p) - abs(op) for p,op in zip(positions, old_positions)]

    transaction_cost = sum(transaction_costL)*txn_cost

    return incremental_pnl - transaction_cost

def gen_pnl(positions, targets, txn_cost=.1, prev_position = None, type='daily'):
    
    # positions: list of numpy arrays, list of lists, or single numpy array (1D/2D)
    # targets: corresponding targets (returns)
    # Note: positions include cash frac; targets do not so len(positions[i]) = len(targets[i]) +1
    
    # Convert to numpy first to check dims easily
    if isinstance(positions, list):
        positions = np.array(positions)
    if isinstance(targets, list):
        targets = np.array(targets)
        
    # If 1D array provided (e.g. single day), wrap it to make it iterable over days
    if positions.ndim == 1:
        positions = positions[np.newaxis, :] # (1, 50)
    if targets.ndim == 1:
        targets = targets[np.newaxis, :]
        
    incremental_profits = []
    
    # initialize position (if not provided)
    if prev_position is None:
        prev_position = [0]*positions.shape[1]
        prev_position[1] = 1
    else:
        prev_position = prev_position/sum(prev_position)
    
    prev_position = np.array(prev_position)
    
    # Iterate over the days / ticks (rows)
    for pos, tgt in zip(positions, targets):
        # pos, tgt are (50,) arrays now
        
        # Convert targets to tensor as required by compute_pnl logic
        tgt_tensor = torch.from_numpy(tgt)
        
        # compute_pnl expects positions as numpy (50,) and targets as tensor

        pnl = compute_pnl(pos, prev_position, tgt_tensor, txn_cost=txn_cost)
        incremental_profits.append(pnl)

        prev_position = pos
        
    incremental_profits = np.array(incremental_profits)
    total_profit = np.sum(incremental_profits)
    mean_profit = np.mean(incremental_profits)
    sharpe_factor = np.sqrt(252)
    sharpe = mean_profit / (np.std(incremental_profits) + 1e-9) * sharpe_factor
    
    return {
        'incremental_pnl': incremental_profits.tolist(),
        'total_profit': float(total_profit),
        'sharpe_ratio': float(sharpe),
        'mean_return': float(mean_profit)
    }