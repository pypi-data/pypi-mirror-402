import logging
import numpy as np
from torch._refs import true_divide

class TestKiteWrapper:
    def __init__(self, kite, test_mode=True):
        self.kite = kite
        self.test_mode = test_mode

    # def ltp(self, instruments):
    #     if self.kite:
    #         try:
    #             return self.kite.ltp(instruments)
    #         except Exception as e:
    #             print(f"Warning: Could not fetch LTP from Kite: {e}")
    #     # Return mock LTPs if kite fails or is None or we are just testing logic without connection
    #     print("Using mock LTPs (100.0)")
    #     return {inst: {'last_price': 100.0} for inst in instruments}

    def place_order(self, **kwargs):
        if self.test_mode:
            print(f"[TEST MODE] Order Request: {kwargs}")
            return "TEST_ORDER_ID_123"
        else:
            return self.kite.place_order(**kwargs)

def rebalance_positions(kite, capital, cf, current_positionsD, desired_positionsD, product_type='MIS', test_mode=True, weighted_allocation=False):
    """
    Rebalance positions.
    
    Args:
        kite: KiteConnect instance
        capital: Total capital available (cash balance)
        cf: DataFrame where columns are trading symbols (assumes cf['close'][symbol] exists)
        current_positions: Array/List. 
                           If weighted_allocation=False (default), exact SHARE COUNTS.
                           If weighted_allocation=True, weights/states (e.g. -1, 0, 1 or 0.5, 2.0).
        desired_positions: Array/List.
                           If weighted_allocation=False, exact SHARE COUNTS.
                           If weighted_allocation=True, weights/states.
        weighted_allocation: If True, allocates capital based on ratio of desired_positions values.
                             If False, assumes inputs are exact number of shares.
                           
    Returns:
        remaining_cash: Capital after trades (capital - cost_of_trades)
        actual_positions: List of final share counts (if weighted=False) or weights (if weighted=True)?
                          Usually returning 'actual shares held' is most useful, but if inputs were weights, 
                          user might expect weights returned? 
                          The previous prompt asked for "actual positions taken in terms of number of shares".
                          So always return SHARES.
    """
    # Wrap kite instance
    kite_app = TestKiteWrapper(kite, test_mode=test_mode)
    
    # 1. Identify symbols and initialize lists

    symbols = cf['close'].columns
    current_positions,desired_positions,actual_positions,actual_positionsD=[],[],[],{}
    for s in symbols:
        current_positions.append(current_positionsD[s])
        desired_positions.append(desired_positionsD[s])
        actual_positionsD[s]=current_positionsD[s]

    # Validate input lengths
    if len(current_positions) != len(symbols) or len(desired_positions) != len(symbols):
        print(f"Error: Mismatch in lengths. Symbols: {len(symbols)}, Current: {len(current_positions)}, Desired: {len(desired_positions)}")
        return capital, current_positions

    remaining_cash = capital
    actual_positions = [] # This will store actual SHARES held after rebalance

    # Calculate Allocation Unit if weighted
    allocation_unit = 0
    if weighted_allocation:
        # Sum of absolute Desired Weights to find denominator
        # If user wants "equal division across non-zero", inputs are 1s and 0s. Sum is count.
        # If user passes 2 and 1. Sum is 3. 2/3 capital and 1/3 capital.
        total_weight = sum(abs(p) for p in desired_positions)
        if total_weight == 0:
            total_weight = sum(abs(p) for p in current_positions)
        if total_weight > 0:
            allocation_unit = capital / total_weight
            print(f"Weighted Allocation Mode. Total Weight: {total_weight}. Unit Capital: {allocation_unit:.2f}")
        else:
            print("Weighted Allocation Mode: Total weight is 0. Exits only.")

    # 4. Rebalance
    for i, symbol in enumerate(symbols):
        try:
            # key assumption: cf contains prices (e.g. close)
            # taking the last available non-NaN value or just the last row
            price = float(cf['close'][symbol].iloc[-1])
            if price is None:
                continue
        except Exception as e:
            print(f"Warning: Could not fetch price from cf for {symbol}: {e}. Skipping.")
            # If we simply skip, actual position is undefined? Or assume current? 
            # If inputs are weights, we can't easily return 'current shares' unless we know them.
            # But the prompt implies inputs are consistent.
            # We'll just append 0 or None? Safer to not append and let length mismatch warn user?
            # Or assume current_positions[i] is 'shares' if weighted=False?
            # If weighted=True, current_positions[i] is a weight. We don't know shares.
            # We'll return empty/partial list or just log.
            continue
            
        current_val = current_positions[i]
        desired_val = desired_positions[i]
        
        quantity_diff = 0
        
        if weighted_allocation:
            # Logic: Trade Value derived from Weight Difference
            # diff_weight = desired_val - current_val
            # trade_value_cash = diff_weight * allocation_unit
            
            # However, simpler to calculate Target Shares directly from Desired Weight
            # But we also need to account for 'current_val' (weight) to know the delta?
            # "based on the difference between the current and desired position"
            
            if True:
                diff_weight = desired_val - current_val
                trade_value_cash = diff_weight * allocation_unit
                
                # Convert cash value to shares
                # floor/int division by price
                if np.isnan(price):
                    quantity_diff = 0
                else:
                    quantity_diff = int(trade_value_cash / price) 
                
                print(symbol,price,quantity_diff)
                
                # Note: This approach calculates 'shares to trade'. 
                # Calculating 'actual_shares_held' requires knowing 'current_shares'.
                # IF current_positions passed in were WEIGHTS, we don't strictly know 'current_shares'
                # unless we back-calculate: current_shares ~ (current_weight * unit) / price?
                # Or maybe the user accepts that 'actual_positions' returned will be 'shares resulting from trade'.
                # Let's assume we start with 0 shares if we can't infer? 
                # OR, perhaps we should just return the list of 'active shares held' assuming perfect execution?
                
                # Refined Logic for 'actual_positions' return in weighted mode:
                # We can't know exact 'current shares' from 'current weight' without price history or assumption.
                # BUT, we can track the 'shares bought/sold'.
                # If we assume we hold 'current_weight' worth of stock, effectively:
                # current_shares_est = int((current_val * allocation_unit) / price)
                # desired_shares_est = int((desired_val * allocation_unit) / price)
                # quantity_diff = desired_shares_est - current_shares_est
                pass
            else:
                quantity_diff = 0
                
        else:
            # Direct Share Counts
            quantity_diff = desired_val - current_val

        # Execute Trade
        if quantity_diff == 0:
            # What to append to actual_positions?
            # If weighted, we assume we hold 'desired' amount? 
            # If shares, we hold desired_val (== current_val).
            if weighted_allocation:
                 # Estimate held shares
                 shares_held = int((desired_val * allocation_unit) / price) if price > 0 and total_weight > 0 else 0
                 actual_positions.append(shares_held)
            else:
                 actual_positions.append(current_val)
            continue
            
        # Cost of trade
        trade_cost = quantity_diff * price
        
        # Determine Trade Params
        quantity = int(abs(quantity_diff))
        is_buy = quantity_diff > 0
        
        remaining_cash -= trade_cost

        # Safe access to kite constants if available, else literal strings
        try:
            tx_type = kite.TRANSACTION_TYPE_BUY if is_buy else kite.TRANSACTION_TYPE_SELL
            exch = kite.EXCHANGE_NSE
            prod = kite.PRODUCT_MIS # Defaulting to MIS as per plan, user can change if needed
            order_type = kite.ORDER_TYPE_MARKET
            validity = kite.VALIDITY_DAY
        except AttributeError:
            tx_type = "BUY" if is_buy else "SELL"
            exch = "NSE"
            prod = product_type
            order_type = "MARKET"
            validity = "DAY"

        order_params = {
            "tradingsymbol": symbol,
            "exchange": exch,
            "transaction_type": tx_type,
            "quantity": quantity,
            "product": prod,
            "order_type": order_type,
            "validity": validity
        }
        
        print(f"Rebalancing {symbol}: (Diff Shares: {quantity_diff}). Price: {price:.2f}. Trade Cost: {trade_cost:.2f}")
        try:
            kite_app.place_order(**order_params)
            
            # Record Position
            if weighted_allocation:
                 # If we successfully traded to match desired weight
                 shares_held = int((desired_val * allocation_unit) / price)
                 actual_positions.append(shares_held)
                 actual_positionsD[symbol]=shares_held
            else:
                 # We moved from current to desired
                 actual_positions.append(desired_val)
                 actual_positionsD[symbol]=desired_val
                 
        except Exception as e:
            print(f"Error placing order for {symbol}: {e}")
            # Revert cost
            remaining_cash += trade_cost 
            
            # Record Position (Failure)
            if weighted_allocation:
                 # Reverted to current
                 shares_held = int((current_val * allocation_unit) / price) if price > 0 else 0
                 actual_positions.append(shares_held)
                 actual_positionsD[symbol]=shares_held
            else:
                 actual_positions.append(current_val)
                 actual_positionsD[symbol]=desired_val
            
    return remaining_cash, actual_positionsD
