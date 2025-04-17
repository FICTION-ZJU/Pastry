from src.utils.project_utils import create_AsgnInstr
from src.analysis.guard_analysis import MOD, DIV
from src.transformers.bounded import convert_bounded_pcp
from probably.pgcl.ast import *
import sympy as sp


def convert_condbounded_AST(syntax_tree, var_abc_info, central_var):
    if isinstance(syntax_tree, list):
        i = 0
        while i < len(syntax_tree):
            if isinstance(syntax_tree[i], AsgnInstr):
                if syntax_tree[i].lhs == central_var:
                    central_value = (-1 if syntax_tree[i].rhs.operator == Binop.MINUS else 1)*syntax_tree[i].rhs.rhs.value
                    for var, abc_info in var_abc_info.items():
                        asgn_value = -central_value*abc_info[1]
                        syntax_tree.insert(i+1, create_AsgnInstr(var, asgn_value))
                        i += 2
                else:
                    or_value = (-1 if syntax_tree[i].rhs.operator == Binop.MINUS else 1)*syntax_tree[i].rhs.rhs.value
                    abc_info = var_abc_info[syntax_tree[i].lhs]
                    syntax_tree[i] = create_AsgnInstr(syntax_tree[i].lhs, or_value*abc_info[0])
                    i += 1
                    
            else:
                convert_condbounded_AST(syntax_tree[i], var_abc_info, central_var)
                i += 1

    elif isinstance(syntax_tree, WhileInstr):
        convert_condbounded_AST(syntax_tree.body, var_abc_info, central_var)

    elif isinstance(syntax_tree, IfInstr):
        convert_condbounded_AST(syntax_tree.true, var_abc_info, central_var)
        convert_condbounded_AST(syntax_tree.false, var_abc_info, central_var)

    elif isinstance(syntax_tree, ChoiceInstr):
        convert_condbounded_AST(syntax_tree.lhs, var_abc_info, central_var)
        convert_condbounded_AST(syntax_tree.rhs, var_abc_info, central_var)
    
    
        
def convert_condbounded_guards(replacement_map, var_abc_info, central_var):
    cvar_symbol = sp.Symbol(central_var)
    var_sub_dict = {}
    for var, abc_info in var_abc_info.items():
        var_symbol = sp.Symbol(var)
        var_sub_dict[var_symbol] = DIV(var_symbol + abc_info[1]*cvar_symbol + abc_info[2], abc_info[0])
        
    for guard_label, spguard in replacement_map.items():
        replacement_map[guard_label] = spguard.subs(var_sub_dict)
    
        
def convert_condbounded_pcp(sd_pgcl_prog, replacement_map, var_abc_info, central_var, filtering=False):
    if filtering:
        # Filter and retain only meaningful annotation data for analysis
        var_abc_info = {k: v for k, v in var_abc_info.items() if k in sd_pgcl_prog.variables}
        
    central_init = sd_pgcl_prog.variables[central_var]
    for var, abc_info in var_abc_info.items():
        sd_pgcl_prog.variables[var] = abc_info[0]*sd_pgcl_prog.variables[var] - abc_info[1]*central_init - abc_info[2]
    
    convert_condbounded_AST(sd_pgcl_prog.instructions, var_abc_info, central_var)
    convert_condbounded_guards(replacement_map, var_abc_info, central_var)
    
    M_str = central_var
    var_comp_dict = {}
    var_bound_dict = {}
    for var, abc_info in var_abc_info.items():
        var_comp_dict[var] = abc_info[3]
        var_bound_dict[var] = 2*abc_info[3] + 1
        
    convert_bounded_pcp(sd_pgcl_prog, replacement_map, var_comp_dict, var_bound_dict, M_str)
