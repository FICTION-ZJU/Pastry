import sympy as sp
from collections import deque
import math

    
class DIV(sp.Function):
    nargs = 2
    @classmethod
    def eval(cls, a, b):
        if b == 1:
            return a
        if a.is_number and b.is_number:
            return a // b
        return None

class MOD(sp.Function):
    nargs = 2
    @classmethod
    def eval(cls, a, b):
        if b == 1:
            return 0
        if a.is_number and b.is_number:
            return a % b
        return None


global_dict = sp.__dict__.copy()
global_dict["DIV"] = DIV
global_dict["MOD"] = MOD


class GuardExpr():
    """
    We introduce a new type to represent guards in PCPs.
    """
    def __init__(self, guard):
        if isinstance(guard, str):
            self.sp_expr = sp.parse_expr(guard, global_dict = global_dict)
        else:
            self.sp_expr = guard

        variables = self.sp_expr.free_symbols
        if len(variables) == 1:
            self.sp_var = next(iter(variables))
        else:
            self.sp_var = None

    def evaluate(self, value):
        if isinstance(value, int):
            if self.sp_var:
                return bool(self.sp_expr.subs(self.sp_var, value))
            else:
                return bool(self.sp_expr)
        else:
            raise TypeError(f"Input must be an int.(value_type={type(value)})")

    def __str__(self):
        return str(self.sp_expr)

    def negate(self):
        negated_guard = sp.logic.boolalg.Not(self.sp_expr)
        return GuardExpr(negated_guard)


def analyze_innermost_MOD_DIV(expr, var, var_tmp):
    first_op = None

    def traverse(expr):
        nonlocal first_op
        if isinstance(expr, (MOD, DIV)) and not expr.args[0].has(MOD) and not expr.args[0].has(DIV):
            op = expr.args[1]
            if first_op is None:
                first_op = op
            if op == first_op:
                new_arg0 = expr.args[0].subs(var, var_tmp)
                if isinstance(expr, MOD):
                    return MOD(new_arg0, op)
                else:
                    return DIV(new_arg0, op)
        if expr.args:
            new_args = tuple(traverse(arg) for arg in expr.args)
            return expr.func(*new_args)
        return expr
    return traverse(expr), first_op


def cauchy_root_bound(polynomial):
    coeffs = sp.Poly(polynomial).all_coeffs()
    leading_coeff = coeffs[0]
    ratios = [abs(c / leading_coeff) for c in coeffs[1:]]
    M = 1 + max(ratios)
    M_int = int(sp.ceiling(M))
    return M_int


def remove_innermost_MOD_DIV(expr, var, var_tmp, xr, A):
    if isinstance(expr, MOD) and not expr.args[0].has(MOD) and not expr.args[0].has(DIV):
        if expr.args[1] == A:
            coeffs = reversed(sp.Poly(expr.args[0], var_tmp).all_coeffs())
            return sum(coef * xr ** k for k, coef in enumerate(coeffs)) % A

    elif isinstance(expr, DIV) and not expr.args[0].has(MOD) and not expr.args[0].has(DIV):
        if expr.args[1] == A:
            coeffs = list(reversed(sp.Poly(expr.args[0], var_tmp).all_coeffs()))
            sum_result = 0
            for k in range(len(coeffs)):
                sum_result += (coeffs[k] * xr) // A
                if k > 0:
                    for i in range(1, k + 1):
                        sum_result += sp.binomial(k, i) * (A ** (i - 1)) * (var ** i) * (xr ** (k - i))
            return sum_result

    if expr.args:
        return expr.func(*[remove_innermost_MOD_DIV(arg, var, var_tmp, xr, A) for arg in expr.args])
    return expr


def get_threshold_and_period_from_expr(expr, var, var_tmp):
    if isinstance(expr, (sp.logic.boolalg.BooleanTrue, sp.logic.boolalg.BooleanFalse)):
        return 0, 1

    if expr.free_symbols == set():
        return 0, 1
    elif not expr.has(MOD, DIV):
        return cauchy_root_bound(expr), 1
    else:
        expr_modified, first_op = analyze_innermost_MOD_DIV(expr, var, var_tmp)

        exprs_subs = []
        for i in range(first_op):
            exprs_subs.append(expr_modified.subs(var, i + (first_op * var)))

        thresholds = []
        periods = []
        for i, expr_subs in enumerate(exprs_subs):
            threshold, period = get_threshold_and_period_from_expr(
                remove_innermost_MOD_DIV(expr_subs, var, var_tmp, i, first_op), var, var_tmp)
            thresholds.append(threshold)
            periods.append(period)
        return first_op * (1 + max(thresholds)), first_op * math.lcm(*periods)


def get_exprs(spguard):
    exprs = []
    get_exprs_from_subtree(spguard, exprs)
    return exprs


def get_exprs_from_subtree(subtree, exprs):
    if isinstance(subtree, (sp.Eq, sp.Ne, sp.Gt, sp.Lt, sp.Ge, sp.Le)):
        exprs.append(subtree.lhs - subtree.rhs)
    elif isinstance(subtree, (sp.And, sp.Or, sp.Not)):
        for arg in subtree.args:
            get_exprs_from_subtree(arg, exprs)
    else:
        raise ValueError("Unsupported expression type", type(subtree))


def find_minimum_period(value_list):
    T = len(value_list)
    if T <= 1:
        return T
    for T_prime in range(1, T):
        if T % T_prime == 0:
            sub_period = value_list[:T_prime]
            repeated = sub_period * (T // T_prime)
            if repeated == value_list:
                return T_prime
    return T


def minimize_guard_threshold_and_period(spguard, var, guard_threshold, guard_period):
    p_bools = [evaluate_predicate(spguard, {var: j}) for j in [guard_threshold + i for i in range(guard_period)]]
    n_bools = [evaluate_predicate(spguard, {var: j}) for j in [(-1) * guard_threshold - i for i in range(guard_period)]]

    guard_period_p = find_minimum_period(p_bools)
    guard_period_n = find_minimum_period(n_bools)

    p_counter = guard_threshold
    n_counter = -guard_threshold
    deque_p = deque()
    for i in range(p_counter - 1 + guard_period_p, p_counter - 1, -1):
        deque_p.append(evaluate_predicate(spguard, {var: i}))
    deque_n = deque()
    for i in range(n_counter + 1 - guard_period_n, n_counter + 1):
        deque_n.append(evaluate_predicate(spguard, {var: i}))

    p_counter -= 1
    n_counter += 1
    while (p_counter >= n_counter):
        deque_p.append(evaluate_predicate(spguard, {var: p_counter}))
        deque_n.append(evaluate_predicate(spguard, {var: n_counter}))
        if deque_p[0] != deque_p[-1] or deque_n[0] != deque_n[-1]:
            break
        else:
            guard_threshold -= 1
            deque_p.popleft()
            deque_n.popleft()
            p_counter -= 1
            n_counter += 1
    return guard_threshold, guard_period_p, guard_period_n


def evaluate_predicate(guard, variable_value=None):
    if variable_value:
        guard = guard.subs(variable_value)
    return bool(guard)


def get_threshold_and_period_from_spguard(spguard):
    if isinstance(spguard, (sp.logic.boolalg.BooleanTrue, sp.logic.boolalg.BooleanFalse)):
        return 0, 1, 1

    var_set = spguard.free_symbols
    if len(var_set) == 0:
        return 0, 1, 1
    elif len(var_set) > 1:
        raise ValueError("Expressions with more than one variable are not supported.")
    else:
        var = next(iter(var_set))
        var_tmp = sp.symbols(var.name + '_tmp')
    exprs = get_exprs(spguard)

    thresholds = []
    periods = []
    for expr in exprs:
        threshold, period = get_threshold_and_period_from_expr(expr, var, var_tmp)
        thresholds.append(threshold)
        periods.append(period)

    guard_threshold = max(thresholds)
    guard_period = math.lcm(*periods)
    guard_threshold, guard_period_positive, guard_period_negative = minimize_guard_threshold_and_period(spguard, var,
                                                                                                        guard_threshold,
                                                                                                        guard_period)
    return int(guard_threshold), int(guard_period_positive), int(guard_period_negative)
