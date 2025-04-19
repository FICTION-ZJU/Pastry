from probably.pgcl import *
from src.analysis.guard_analysis import *
from fractions import Fraction
import logging

logger = logging.getLogger("pastry")

class ProbabilisticTransitionSystem:
    """
    Represents the probabilistic transition system for a 1-d probabilistic counter program.
    """
    def __init__(self, program):
        logger.info("Starting creation of Probabilistic Transition System.")

        # Initialize class variables
        self.init_val = int(list(program.variables.values())[0])
        self.var_name = list(program.variables.keys())[0]
        self.states_num = 0
        self.non_trivial_guards = []
        self.states_types_dict = dict()
        self.states_transitions_dict = dict()
        
        # Recursively build the PTS block from the program's instructions
        exit_info_list, _ = self._build_block_from_subast(program.instructions)
        
        # Add a terminal state and corresponding zeroing transitions at the end of the PTS
        terminal_state = self._add_state('terminal')
        for exit_info in exit_info_list:
            self._add_transition_from_info(exit_info, (terminal_state,))
        self._add_transition(terminal_state, terminal_state, GuardExpr(self.var_name + '>0'), 1, 1, -1)
        self._add_transition(terminal_state, terminal_state, GuardExpr(self.var_name + '<0'), 1, 1, 1)
        self._add_transition(terminal_state, terminal_state, GuardExpr('Eq(' + self.var_name + ',0)'), 1, 1, 0)
        
        logger.info("Probabilistic Transition System successfully created with %d states and %d transitions.", len(self.states_types_dict), len(self.states_transitions_dict))
    
    def get_mc_transition_prob(self, mc_state_from, mc_state_to):
        """
        Computes the transition probability between two Markov Chain states.
        """
        pts_states_pair = (mc_state_from[0], mc_state_to[0])
        if pts_states_pair not in self.states_transitions_dict:
            return 0
        else:
            pts_transitions_list = self.states_transitions_dict[pts_states_pair]
            for pts_transition in pts_transitions_list:
                if pts_transition["guard"].evaluate(mc_state_from[1]):
                    update_value = pts_transition["update_value"]
                    if mc_state_from[1] + update_value == mc_state_to[1]:
                        return (pts_transition["prob_num"], pts_transition["prob_den"])
            else:
                return 0

    def _add_state(self, state_type):
        """
        Adds a new PTS state with the given type to the internal PTS state dictionary.

        :param state_type: The label of the new state, e.g., 'assign' or 'while'. (str)
        :return: The unique integer ID assigned to the newly added state. (int)
        """
        self.states_types_dict[self.states_num] = state_type
        self.states_num += 1
        return self.states_num - 1

    def _add_transition(self, state_from, state_to, guard, prob_num, prob_den, update_value):
        """
        Creates a transition between two PTS states and updates the internal PTS transition dictionary.
        """
        if guard.sp_expr.free_symbols:
            self.non_trivial_guards.append(guard)
            
        if (state_from, state_to) in self.states_transitions_dict:
            self.states_transitions_dict[(state_from, state_to)].append({'guard': guard, 'prob_num': prob_num,
                                                                         'prob_den': prob_den,
                                                                         'update_value': update_value})
        else:
            self.states_transitions_dict[(state_from, state_to)] = [{'guard': guard, 'prob_num': prob_num,
                                                                     'prob_den': prob_den,
                                                                     'update_value': update_value}]

    def _add_transition_from_info(self, exit_info, entry_info):
        """
        Adds a transition by unpacking information from structured exit and entry tuples.
        """
        self._add_transition(exit_info[0], entry_info[0], exit_info[1], exit_info[2], exit_info[3], exit_info[4])

    def _parse_prob(self, prob_Expr):
        """
        Parses a probability expression into fractional form and computes its complement.
        """
        frprob = prob_Expr.to_fraction()
        nfrprob = Fraction(1, 1) - frprob
        return frprob.numerator, frprob.denominator, nfrprob.numerator, nfrprob.denominator
    
    def _parse_assign(self, Assign_Expr):
        """
        Parses an assignment instruction and extracts the integer update value
        """
        return (-1 if Assign_Expr.rhs.operator == Binop.MINUS else 1)*Assign_Expr.rhs.rhs.value
    
    def _build_block_from_assign_group(self, update_value):
        """
        Builds a PTS block for a group of assignments.
        """
        exists = []
        entries = []
        sign = int(update_value > 0) - int(update_value < 0)
        for index in range(abs(update_value)):
            state_up = self._add_state('assign')
            exists.append([(state_up, GuardExpr('true'), 1, 1, sign)])
            entries.append((state_up,))
            
        self._build_edges(exists, entries)
        return exists[-1], entries[0]
    
    def _build_edges(self, exits, entries):
        len_list = len(entries)
        if len_list > 1:
            for index in range(len_list):
                current_exit_info_list = exits[index]
                if index > 0:
                    current_entry_info = entries[index]
                    for exit_info in previous_exit_info_list:
                            self._add_transition_from_info(exit_info, current_entry_info)
                previous_exit_info_list = current_exit_info_list   

    def _build_block_from_subast(self, subast):
        """
        Recursively builds a PTS block
        """
        if isinstance(subast, list):
            if len(subast) == 0:
                state_empty = self._add_state('empty')
                entry_info = (state_empty,)
                exit_info_list = [(state_empty, GuardExpr('true'), 1, 1, 0)]
                return exit_info_list, entry_info

            else:
                i = 0
                len_subset = len(subast)
                merged_exits = []
                merged_entries = []
                while i < len_subset:
                    if isinstance(subast[i], AsgnInstr):
                        assign_num_list = [self._parse_assign(subast[i])]
                        i += 1
                        while i < len_subset and isinstance(subast[i], AsgnInstr):
                            assign_num_list.append(self._parse_assign(subast[i]))
                            i += 1
                        assign_value = sum(assign_num_list)
                        
                        if assign_value == 0:
                            continue
                            
                        current_exit_info_list, current_entry_info = self._build_block_from_assign_group(assign_value)
                    else:
                        current_exit_info_list, current_entry_info = self._build_block_from_subast(subast[i])
                        i += 1
                    merged_exits.append(current_exit_info_list)
                    merged_entries.append(current_entry_info)
                
                if merged_entries:
                    self._build_edges(merged_exits, merged_entries)
                    return merged_exits[-1], merged_entries[0]
                else:
                    return self._build_block_from_subast([])

        elif isinstance(subast, WhileInstr):
            state_while = self._add_state('while')
            guard = subast.cond
            negated_guard = guard.negate()
            exit_info_list = [(state_while, negated_guard, 1, 1, 0)]
            entry_info = (state_while,)

            if len(subast.body) == 0 or (len(subast.body) == 1 and isinstance(subast.body[0], SkipInstr)):
                self._add_transition_from_info((state_while, guard, 1, 1, 0), entry_info)
            else:
                body_exit_info_list, body_entry_info = self._build_block_from_subast(subast.body)
                self._add_transition_from_info((state_while, guard, 1, 1, 0), body_entry_info)
                for item in body_exit_info_list:
                    self._add_transition_from_info(item, entry_info)
            return exit_info_list, entry_info

        elif isinstance(subast, IfInstr):
            state_if = self._add_state('if')
            guard = subast.cond
            negated_guard = guard.negate()
            entry_info = (state_if,)

            if len(subast.true) == 0 or (len(subast.true) == 1 and isinstance(subast.true[0], SkipInstr)):
                true_exit_info_list = [(state_if, guard, 1, 1, 0)]
            else:
                true_exit_info_list, true_entry_info = self._build_block_from_subast(subast.true)
                self._add_transition_from_info((state_if, guard, 1, 1, 0), true_entry_info)

            if len(subast.false) == 0 or (len(subast.false) == 1 and isinstance(subast.false[0], SkipInstr)):
                false_exit_info_list = [(state_if, negated_guard, 1, 1, 0)]
            else:
                false_exit_info_list, false_entry_info = self._build_block_from_subast(subast.false)
                self._add_transition_from_info((state_if, negated_guard, 1, 1, 0), false_entry_info)
            exit_info_list = true_exit_info_list + false_exit_info_list
            return exit_info_list, entry_info

        elif isinstance(subast, ChoiceInstr):
            state_choice = self._add_state('choice')
            entry_info = (state_choice,)
            f1, m1, nf1, nm1 = self._parse_prob(subast.prob)

            if len(subast.lhs) == 0 or (len(subast.lhs) == 1 and isinstance(subast.lhs[0], SkipInstr)):
                lhs_exit_info_list = [(state_choice, GuardExpr('true'), f1, m1, 0)]
            else:
                lhs_exit_info_list, lhs_entry_info = self._build_block_from_subast(subast.lhs)
                self._add_transition_from_info((state_choice, GuardExpr('true'), f1, m1, 0), lhs_entry_info)

            if len(subast.rhs) == 0 or (len(subast.rhs) == 1 and isinstance(subast.rhs[0], SkipInstr)):
                rhs_exit_info_list = [(state_choice, GuardExpr('true'), nf1, nm1, 0)]
            else:
                rhs_exit_info_list, rhs_entry_info = self._build_block_from_subast(subast.rhs)
                self._add_transition_from_info((state_choice, GuardExpr('true'), nf1, nm1, 0), rhs_entry_info)
            exit_info_list = lhs_exit_info_list + rhs_exit_info_list
            return exit_info_list, entry_info
            
    def visualize(self, ifshow=False, file_path=None):
        """
        Visualizes the probabilistic transition system using PyGraphviz.
        """
        try:
            import pygraphviz as pgv
        except ImportError:
            print("PyGraphviz is not installed. Please install it to use visualization features.")
            return None

        G = pgv.AGraph(strict=False, directed=True)

        nodes_info = dict()
        nodes_info[0] = {'type': self.states_types_dict[0], 'state': 'initial'}
        nodes_info[self.states_num - 1] = {'type': self.states_types_dict[self.states_num - 1], 'state': 'terminal'}
        for state in range(1, self.states_num - 1):
            nodes_info[state] = {'type': self.states_types_dict[state], 'state': 'normal'}

        for node, info in nodes_info.items():
            label = f"{node}\n{info['type']}"
            if info['state'] == 'initial':
                G.add_node(node, label=label, color='green', style='filled')
            elif info['state'] == 'terminal':
                G.add_node(node, label=label, color='red', style='filled')
            else:
                G.add_node(node, label=label)

        for (state_from, state_to), transitions_list in self.states_transitions_dict.items():
            for transition in transitions_list:
                if transition['prob_num'] % transition['prob_den'] == 0:
                    prob = str(transition['prob_num'] // transition['prob_den'])
                else:
                    prob = f"{transition['prob_num']}/{transition['prob_den']}"
                edge_label = f"Prob: {prob}\nGuard: {str(transition['guard'])}\nUpdate: {transition['update_value']}"
                G.add_edge(state_from, state_to, label=edge_label)

        G.layout(prog='dot')
        if file_path is None:
            output_image_path = 'probabilistic_transition_system.png'
        else:
            output_image_path = file_path
        G.draw(output_image_path)

        if ifshow:
            from IPython.display import Image
            return Image(filename=output_image_path)
        return output_image_path
