from probably.pgcl.ast import *
from src.analysis.guard_analysis import GuardExpr, MOD, DIV
import sympy as sp


def get_bounded_coeffs(var_comp_dict, var_bound_dict, M_str):
    """
    Calculate intermediate results, preparing for the convertion process.
    """
    var_coeff_dict = {}
    var_sub_dict = {}
    z_bd = sp.Symbol('z_bd')
    cum_expr = 0
    cum_coeff = 1
    
    for i, (var, bound) in enumerate(var_bound_dict.items()):
        comp = var_comp_dict[var]
        ne_cum_coeff = cum_coeff * bound
        var_coeff_dict[var] = cum_coeff
        if (not M_str) & (i == len(var_bound_dict) - 1):
            var_sub_dict[var] = DIV(z_bd, cum_coeff) - comp
        else:
            var_sub_dict[var] = DIV((MOD(z_bd, ne_cum_coeff) - cum_expr), cum_coeff) - comp
            cum_expr += cum_coeff * (sp.Symbol(var) + comp)
        cum_coeff = ne_cum_coeff

    if M_str:
        var_coeff_dict[M_str] = cum_coeff
        var_sub_dict[M_str] = DIV(z_bd, cum_coeff)
    return var_coeff_dict, var_sub_dict

def convert_bounded_AST(syntax_tree, replacement_map, var_coeff_dict, var_sub_dict):
    """
    Convert the syntax tree of a bounded k-d PCP to a 1-d PCP syntax tree by replacing guards and assignments.
    """
    if isinstance(syntax_tree, list):
        for item in syntax_tree:
            convert_bounded_AST(item, replacement_map, var_coeff_dict, var_sub_dict)

    elif isinstance(syntax_tree, WhileInstr):
        init_guard = replacement_map[syntax_tree.cond.var]
        syntax_tree.cond = GuardExpr(init_guard.subs(var_sub_dict))
        convert_bounded_AST(syntax_tree.body, replacement_map, var_coeff_dict, var_sub_dict)

    elif isinstance(syntax_tree, IfInstr):
        init_guard = replacement_map[syntax_tree.cond.var]
        syntax_tree.cond = GuardExpr(init_guard.subs(var_sub_dict))
        convert_bounded_AST(syntax_tree.true, replacement_map, var_coeff_dict, var_sub_dict)
        convert_bounded_AST(syntax_tree.false, replacement_map, var_coeff_dict, var_sub_dict)

    elif isinstance(syntax_tree, ChoiceInstr):
        convert_bounded_AST(syntax_tree.lhs, replacement_map, var_coeff_dict, var_sub_dict)
        convert_bounded_AST(syntax_tree.rhs, replacement_map, var_coeff_dict, var_sub_dict)

    elif isinstance(syntax_tree, AsgnInstr):
        ovar = syntax_tree.lhs
        syntax_tree.lhs = 'z_bd'
        syntax_tree.rhs.lhs = VarExpr('z_bd')
        syntax_tree.rhs.rhs = NatLitExpr(int(syntax_tree.rhs.rhs.value * var_coeff_dict[ovar]))

def convert_bounded_pcp(sd_pgcl_prog, replacement_map, var_comp_dict, var_bound_dict, M_str):
    """
    Convert a bounded k-d PCP to a 1-d PCP.
    """
    # Filter and retain only meaningful annotation data for analysis
    if M_str not in sd_pgcl_prog.variables:
        M_str = None
    
    
    # Calculate intermediate results, preparing for the convertion process.
    var_coeff_dict, var_sub_dict = get_bounded_coeffs(var_comp_dict, var_bound_dict, M_str)
    
    # Compute and update the initial value of the new variable 'z_bd'.
    init_val = 0
    for var, var_coeff in var_coeff_dict.items():
        if var != M_str:
            init_val += var_coeff * (sd_pgcl_prog.variables[var] + var_comp_dict[var])
    if M_str:
        init_val += var_coeff_dict[M_str] * sd_pgcl_prog.variables[M_str]
    sd_pgcl_prog.variables = {'z_bd': init_val}
    
    # Transform the program's instructions by updating guards and assignments.
    convert_bounded_AST(sd_pgcl_prog.instructions, replacement_map, var_coeff_dict, var_sub_dict)
