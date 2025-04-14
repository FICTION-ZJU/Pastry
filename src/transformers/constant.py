from probably.pgcl.ast import *
from src.utils.project_utils import create_AsgnInstr_rhs
from src.analysis.guard_analysis import GuardExpr
import sympy as sp


def check_const_guard(replacement_map):
    """
    Check the consistency of variable coefficients across different guards and prepare intermediate results
    for the conversion of constant k-d PCP to 1-d PCP.
    """
    ct_guard_dict = {}
    bench_coeff_dict = {}
    z_ct = sp.Symbol('z_ct')
    is_first = True  # Flag to mark the first guard for benchmark initialization
    
    for label, spguard in replacement_map.items():
        spguard_symbols = spguard.free_symbols
        
        # Check if the outermost symbol of the guard expression is of an acceptable type (e.g., Eq, Ne, etc.)
        if spguard_symbols:
            if not isinstance(spguard, (sp.Eq, sp.Ne, sp.Gt, sp.Lt, sp.Ge, sp.Le)):
                return False, None, None
            
            # Simplify the guard expression
            spguard = sp.expand(spguard)
            expr = sp.simplify(spguard.lhs - spguard.rhs)
            
            if expr.free_symbols:
                # Convert to a polynomial form to check linearity
                poly = sp.Poly(expr)
                if not poly.is_linear:
                    return False, None, None
                
                if is_first:  # Initialize the benchmark guard if it's the first one
                    is_first = False
                    bench_symbols = spguard_symbols
                    bench_coeff_dict = {var: poly.coeff_monomial(var) for var in bench_symbols}
                    ct_guard_dict[label] = GuardExpr(spguard.func(z_ct + poly.coeff_monomial(1), 0))    
                else:
                    # Compare the current coefficients with the benchmark coefficients for consistency
                    is_reversed = -1
                    for var, coeff in bench_coeff_dict.items():
                        cur_coeff = poly.coeff_monomial(var)
                        if cur_coeff != coeff:
                            if not (cur_coeff == -coeff and is_reversed == -1):
                                return False, None, None
                        else:
                            if cur_coeff != 0:
                                is_reversed = 1
                    ct_guard_dict[label] = GuardExpr(spguard.func(z_ct + is_reversed*poly.coeff_monomial(1), 0))      
            else:
                ct_guard_dict[label] = GuardExpr(spguard)
        else:
            ct_guard_dict[label] = GuardExpr(spguard)                                            
    return True, ct_guard_dict, bench_coeff_dict


def convert_const_AST(syntax_tree, ct_guard_dict, bench_coeff_dict):
    """
    Convert the syntax tree of a constant k-d PCP to a 1-d PCP syntax tree by replacing guards
    and assignments.
    """
    if isinstance(syntax_tree, list):
        for item in syntax_tree:
            convert_const_AST(item, ct_guard_dict, bench_coeff_dict)

    elif isinstance(syntax_tree, WhileInstr):
        syntax_tree.cond = ct_guard_dict[syntax_tree.cond.var]
        for body in syntax_tree.body:
            convert_const_AST(body, ct_guard_dict, bench_coeff_dict)

    elif isinstance(syntax_tree, IfInstr):
        syntax_tree.cond = ct_guard_dict[syntax_tree.cond.var]
        for body in syntax_tree.true:
            convert_const_AST(body, ct_guard_dict, bench_coeff_dict)
        for body in syntax_tree.false:
            convert_const_AST(body, ct_guard_dict, bench_coeff_dict)

    elif isinstance(syntax_tree, ChoiceInstr):
        for body in syntax_tree.lhs:
            convert_const_AST(body, ct_guard_dict, bench_coeff_dict)
        for body in syntax_tree.rhs:
            convert_const_AST(body, ct_guard_dict, bench_coeff_dict)

    elif isinstance(syntax_tree, AsgnInstr):
        ovar = syntax_tree.lhs
        new_value = int(syntax_tree.rhs.rhs.value * bench_coeff_dict[sp.Symbol(ovar)])
        syntax_tree.lhs = 'z_ct'
        syntax_tree.rhs = create_AsgnInstr_rhs('z_ct', new_value)
        
        
def convert_const_pcp(sd_pgcl_prog, ct_guard_dict, bench_coeff_dict):
    """
    Convert a constant k-d PCP to a 1-d PCP.
    """
    # Update the program's variables and their initial values.
    init_val = 0
    for var, var_init in sd_pgcl_prog.variables.items():
        init_val += int(bench_coeff_dict[sp.Symbol(var)] * var_init)
    sd_pgcl_prog.variables = {'z_ct': init_val}
    
    # Transform the program's instructions by updating guards and assignments.
    convert_const_AST(sd_pgcl_prog.instructions, ct_guard_dict, bench_coeff_dict)
