from src.analysis.guard_analysis import get_threshold_and_period_from_spguard
from probably.pgcl.ast import *
import math
import logging

logger = logging.getLogger("pastry")

def create_AsgnInstr(var_name, value):
    if value == 0:
        raise ValueError(f"Creating AsgnInstr for {var_name} with value 0 is meaningless.")
    return AsgnInstr(lhs=var_name, rhs=BinopExpr(operator=(Binop.MINUS if value<0 else Binop.PLUS), lhs=VarExpr(var_name), rhs=NatLitExpr(abs(value))))

def create_AsgnInstr_rhs(var_name, value):
    if value == 0:
        raise ValueError(f"Creating rhs of AsgnInstr for {var_name} with value 0 is meaningless.")
    return BinopExpr(operator=(Binop.MINUS if value<0 else Binop.PLUS), lhs=VarExpr(var_name), rhs=NatLitExpr(abs(value)))



def analyze_threshold_and_period_from_pts(pts):
    
    # If no non-trivial guards, return the initial value and unit period
    if len(pts.non_trivial_guards) == 0:
        return abs(pts.init_val), 1, 1

    # Initialize lists for thresholds and periods
    thresholds = [pts.init_val]
    positive_periods = []
    negative_periods = []
    
    # Compute thresholds and periods from non-trivial guards
    for guard in pts.non_trivial_guards:
        guard_threshold, guard_period_positive, guard_period_negative = get_threshold_and_period_from_spguard(
            guard.sp_expr)
        thresholds.append(guard_threshold)
        positive_periods.append(guard_period_positive)
        negative_periods.append(guard_period_negative)

    # Compute the maximum threshold and least common multiples of the periods
    pts_threshold = max(thresholds)
    pts_positive_period = math.lcm(*positive_periods)
    pts_negative_period = math.lcm(*negative_periods)
    
    logger.info("Probabilistic Transition System threshold: %d, Positive axis period: %d, Negative axis period: %d", pts_threshold, pts_positive_period, pts_negative_period)
    return pts_threshold, pts_positive_period, pts_negative_period