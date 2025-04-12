import networkx as nx
import numpy as np
import logging

logger = logging.getLogger("pastry")


class LabeledMarkovChain:
    def __init__(self, pts, threshold, forward_rmc, backward_rmc):
        
        logger.info("Starting creation of Labeled Markov Chain.")
        
        self.pts = pts
        self.threshold = threshold
        self.forward_rmc = forward_rmc
        self.backward_rmc = backward_rmc

        self.initial_state = (0, self.pts.init_val)
        self.terminal_state = (self.pts.states_num - 1, 0)
        self.transient_states, self.null_recurrent_states = set(), set()

        self.G = nx.DiGraph()

        self.G.add_node(self.initial_state)
        self.G.add_node(self.terminal_state)

        self._convert_irregular_part_to_graph()
        self._convert_regular_part_to_graph('forward')
        self._convert_regular_part_to_graph('backward')

        self.post_set = nx.descendants(self.G, self.initial_state)
        self.post_set.add(self.initial_state)
        
        logger.info("Labeled Markov Chain successfully created. Number of states: %s", self.G.number_of_nodes())

    def _convert_irregular_part_to_graph(self):
        for state_pair, transitions_list in self.pts.states_transitions_dict.items():
            for transition in transitions_list:
                if transition['update_value'] == 0:
                    for x in range(-self.threshold, self.threshold + 1):
                        if transition['guard'].evaluate(x):
                            self.G.add_edge((state_pair[0], x), (state_pair[1], x))

                elif transition['update_value'] == 1:
                    for x in range(-self.threshold, self.threshold):
                        if transition['guard'].evaluate(x):
                            self.G.add_edge((state_pair[0], x), (state_pair[1], x + 1))

                elif transition['update_value'] == -1:
                    for x in range(self.threshold, -self.threshold, -1):
                        if transition['guard'].evaluate(x):
                            self.G.add_edge((state_pair[0], x), (state_pair[1], x - 1))

                else:
                    raise ValueError("Invalid update value")

    def _convert_regular_part_to_graph(self, direction):
        if direction == 'forward':
            rmc = self.forward_rmc
            boundary_value = self.threshold
        elif direction == 'backward':
            rmc = self.backward_rmc
            boundary_value = -self.threshold
        else:
            raise ValueError("Invalid direction")

        connection_rmc_states = {(direction, (0, i)) for i in range(self.pts.states_num)}
        connection_irmc_states = {(i, boundary_value) for i in range(self.pts.states_num)}

        for connection_rmc_state in connection_rmc_states:
            rmc_state = rmc.get_global_state(connection_rmc_state[1])
            for connection_irmc_state in connection_irmc_states:
                if self.pts.get_mc_transition_prob(connection_irmc_state, rmc_state):
                    self.G.add_edge(connection_irmc_state, connection_rmc_state)
                if self.pts.get_mc_transition_prob(rmc_state, connection_irmc_state):
                    self.G.add_edge(connection_rmc_state, connection_irmc_state)

        for i, j in rmc.B_nonzero_locs:
            self.G.add_edge((direction, (0, i)), (direction, (0, j)))

        for i, j in rmc.C_nonzero_locs:
            self.G.add_edge((direction, (0, i)), (direction, (1, j)))

        transient_level1_states, nullrec_level1_states, reachability_matrix = rmc.get_level1_info()

        for i, j in np.ndindex(reachability_matrix.shape):
            if reachability_matrix[i, j]:
                self.G.add_edge((direction, (1, i)), (direction, (0, j)))

        self.transient_states |= transient_level1_states
        self.null_recurrent_states |= nullrec_level1_states
  

    def visualize(self, ifshow=False, file_path=None):

        try:
            import pygraphviz as pgv
        except ImportError:
            print("PyGraphviz is not installed. Please install it to use visualization features.")
            return None

        G = pgv.AGraph(strict=False, directed=True)

        nodes_info = dict()
        for node in self.post_set:
            if node == self.initial_state:
                nodes_info[node] = 'initial'
            elif node == self.terminal_state:
                nodes_info[node] = 'terminal'
            else:
                nodes_info[node] = 'normal'

        for node, info in nodes_info.items():
            if info == 'initial':
                G.add_node(node, color='green', style='filled')
            elif info == 'terminal':
                G.add_node(node, color='red', style='filled')
            else:
                G.add_node(node)

        for edge in self.G.edges:
            if edge[0] in self.post_set and edge[1] in self.post_set:
                G.add_edge(edge[0], edge[1])

        G.layout(prog='dot')

        if file_path is None:
            output_image_path = 'finite_chain_graph.png'
        else:
            output_image_path = file_path

        G.draw(output_image_path)

        if ifshow:
            from IPython.display import Image
            return Image(filename=output_image_path)

        return output_image_path

    def verify_post_set_reachability(self):
        ternimal_reachable_states = nx.ancestors(self.G, self.terminal_state)
        ternimal_reachable_states.add(self.terminal_state)
        terminal_unreachable_states = set(self.G.nodes).difference(ternimal_reachable_states)

        if self.post_set.intersection(terminal_unreachable_states | self.transient_states):
            return False

        return True

    def verify_reachability_to_null_recurrent_states(self):
        if self.post_set.intersection(self.null_recurrent_states):
            return True
        else:
            return False

    def is_ast_and_past(self):
        if self.verify_post_set_reachability():
            return {'ast': True, 'past': not self.verify_reachability_to_null_recurrent_states()}
        else:
            return {'ast': False, 'past': False}
