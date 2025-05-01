from src.analysis.guard_analysis import *
from src.transformers.bounded import convert_bounded_pcp
from probably.pgcl.ast import *
from probably.pgcl import parse_pgcl
import sympy as sp
import math


def check_guard_separability(sp_guard, info_dict, var_trend_dict):
    """
    Check if a given guard is a Rectangular Guard using Sympy.
    """
    # Extract all sub-expressions from the guard
    exprs = get_exprs(sp_guard)
    
    # Iterate through each expression to check if it contains more than one variable
    for expr in exprs:
        variables = expr.free_symbols
        
        # If the expression contains no variables, skip it
        if len(variables) == 0:
            continue
            
        # If the expression contains more than one variable, it's not a Rectangular Guard
        elif len(variables) > 1:
            return False
        
        elif len(variables) == 1:
            sp_var = next(iter(variables))
            var_str = str(sp_var)
            
            # If the variable exists in info_dict, compute threshold and period of this expression
            if var_str in info_dict:
                sp_var_tmp = sp.symbols(var_str + '_tmp')
                threshold, period = get_threshold_and_period_from_expr(expr, sp_var, sp_var_tmp)
                threshold, period_p, period_n = minimize_guard_threshold_and_period(expr, sp_var, threshold, period)
                info_dict[var_str]['threshold'].append(threshold)
                if var_trend_dict[var_str]:
                    info_dict[var_str]['period'].append(period_p)
                else:
                    info_dict[var_str]['period'].append(period_n)      
    return True


def check_mono(sd_pgcl_prog, var_trend_dict):
    """
    Check if the program's variable trends are monotone, ensuring that at most one variable is non-monotonic.
    """
    # Initialize the flag to track whether the program is monotone
    is_mono = True
    
    # Helper function to recursively traverse the AST and check the trends of variables
    def traverse_AST_get_trend(syntex_tree):
        nonlocal is_mono, var_trend_dict
        if isinstance(syntex_tree, list):
            for item in syntex_tree:
                if not is_mono:
                    break
                traverse_AST_get_trend(item)

        elif isinstance(syntex_tree, WhileInstr):
            traverse_AST_get_trend(syntex_tree.body)

        elif isinstance(syntex_tree, IfInstr):
            traverse_AST_get_trend(syntex_tree.true)
            traverse_AST_get_trend(syntex_tree.false)

        elif isinstance(syntex_tree, ChoiceInstr):
            traverse_AST_get_trend(syntex_tree.lhs)
            traverse_AST_get_trend(syntex_tree.rhs)
                
        # If the syntax tree is an AsgnInstr, check its trend
        elif isinstance(syntex_tree, AsgnInstr):
            change_value = syntex_tree.rhs.rhs.value
            change_dir = syntex_tree.rhs.operator == Binop.PLUS
            if var_trend_dict[syntex_tree.lhs] is None:
                var_trend_dict[syntex_tree.lhs] = change_dir
            elif var_trend_dict[syntex_tree.lhs] not in {change_dir, 'free'}:
                if 'free' not in var_trend_dict.values():
                    var_trend_dict[syntex_tree.lhs] = 'free'
                else:
                    is_mono = False
        
    traverse_AST_get_trend(sd_pgcl_prog.instructions)
    return is_mono
    
    
def check_separability(replacement_map, var_trend_dict, info_dict):
    """
    Check if all guards in the program are Rectangular Guards.
    """
    for spguard in replacement_map.values():
        result = check_guard_separability(spguard, info_dict, var_trend_dict)
        # If any guard is not separable, return False
        if not result:
            return False
        
    # compute the maximum threshold and LCM of the periods for each variable
    for key, value in info_dict.items():
        value['threshold'] = max(value['threshold'])
        value['period'] = math.lcm(*value['period']) 
    return True
    
    

def create_WhileInstr(var_str, change_dir, threshold, period, replacement_map):
    """
    Construct a WhileInstr based on the given information.
    """
    guard_key = 'guard_' + str(len(replacement_map))
    if change_dir:
        replacement_map[guard_key] = sp.parse_expr(f"{var_str} > {threshold + period}")
        return parse_pgcl(f"while({guard_key}){{{var_str} := {var_str} - {period}}}").instructions[0]
    else:
        replacement_map[guard_key] = sp.parse_expr(f"{var_str} < {-threshold - period}")
        return parse_pgcl(f"while({guard_key}){{{var_str} := {var_str} + {period}}}").instructions[0]
        
                         
def convert_mono_AST(syntax_tree, var_trend_dict, info_dict, replacement_map):
    """
    Convert the syntax tree of a monotone k-d PCP to a bounded k-d PCP syntax tree.
    """
    if isinstance(syntax_tree, list):
        i = 0
        while i < len(syntax_tree):
            if isinstance(syntax_tree[i], AsgnInstr):  
                if var_trend_dict[syntax_tree[i].lhs] != 'free':
                    new_instr = create_WhileInstr(syntax_tree[i].lhs, 
                                                  var_trend_dict[syntax_tree[i].lhs], 
                                                  info_dict[syntax_tree[i].lhs]['threshold'],
                                                  info_dict[syntax_tree[i].lhs]['period'],
                                                  replacement_map)  
                    syntax_tree.insert(i+1, new_instr)
                    i += 2
                else:
                    i += 1
            else:
                convert_mono_AST(syntax_tree[i], var_trend_dict, info_dict, replacement_map)
                i += 1

    elif isinstance(syntax_tree, WhileInstr):
        convert_mono_AST(syntax_tree.body, var_trend_dict, info_dict, replacement_map)

    elif isinstance(syntax_tree, IfInstr):
        convert_mono_AST(syntax_tree.true, var_trend_dict, info_dict, replacement_map)
        convert_mono_AST(syntax_tree.false, var_trend_dict, info_dict, replacement_map)

    elif isinstance(syntax_tree, ChoiceInstr):
        convert_mono_AST(syntax_tree.lhs, var_trend_dict, info_dict, replacement_map)
        convert_mono_AST(syntax_tree.rhs, var_trend_dict, info_dict, replacement_map)
    
        
        
def check_mono_pcp(sd_pgcl_prog, replacement_map):
    """
    Check if the given k-d PCP belongs to the class of monotone k-d PCPs.
    """ 
    # Initialize the variable trend dictionary for all variables in the program
    var_trend_dict = {key: None for key in sd_pgcl_prog.variables}
    
    # Check the variable trends to determine if the program satisfies the conditions for a monotone k-d PCP
    result = check_mono(sd_pgcl_prog, var_trend_dict)
    
    # If the program does not satisfy the monotone conditions, return False and None for the trend and info dictionaries
    if not result:
        return False, None, None
    
    # Initialize the information dictionary, excluding 'free' variables and those with no change
    info_dict = {key: {'threshold': [], 'period': []} for key, value in var_trend_dict.items() if value is not None and value != 'free'}
    
    # Check each guard to determine if it is a Rectangular Guard (i.e., each atomic proposition contains no more than one variable)
    result = check_separability(replacement_map, var_trend_dict, info_dict)
    return result, var_trend_dict, info_dict
    
        
        
def convert_mono_pcp(sd_pgcl_prog, replacement_map, var_trend_dict, info_dict):
    """
    Convert a monotone k-d PCP to a 1-d PCP.

    This function follows a two-step process:
    1. It first converts a constant k-d PCP to a bounded k-d PCP using the `convert_mono_AST` function.
    2. It then calculates intermediate information necessary for further conversion, such as variable bounds 
       and coefficients, and transforms the program into a 1-d PCP using the `convert_bounded_pcp` function.
    """
    # Convert monotone k-d PCP to bounded k-d PCP
    convert_mono_AST(sd_pgcl_prog.instructions, var_trend_dict, info_dict, replacement_map)
    
    # Calculate intermediate information needed for the next convertion
    M_str = None
    var_comp_dict = {}
    var_bound_dict = {}
    for var, init_val in sd_pgcl_prog.variables.items():
        if var_trend_dict[var] == 'free':
            M_str = var
        elif var_trend_dict[var] is None:
            var_comp_dict[var] = max(-init_val, 0)
            var_bound_dict[var] = abs(init_val) + 1
        elif var_trend_dict[var]:
            var_comp_dict[var] = max(-init_val, 0)
            var_bound_dict[var] = max(init_val, var_comp_dict[var] + info_dict[var]['threshold'] + info_dict[var]['period']) + 1
        else:
            var_comp_dict[var] = max(-init_val, info_dict[var]['threshold'] + info_dict[var]['period'])
            var_bound_dict[var] = var_comp_dict[var] + 1
    
    # Convert the bounded k-d PCP to a 1-d PCP
    var_bound_dict = dict(sorted(var_bound_dict.items(), key=lambda x: x[1]))
    convert_bounded_pcp(sd_pgcl_prog, replacement_map, var_comp_dict, var_bound_dict, M_str)
        
    
