import numpy as np
import networkx as nx
import scipy.sparse as scip
import sympy as sp
import logging

logger = logging.getLogger("pastry")

class RegularMarkovChain:
    """
    Represents the regular markov chain corresponding to a 1-d PCP.
    """
    def __init__(self, pts, direction, threshold, period):
        logger.info("Starting creation of Regular Markov Chain with '%s' direction", direction)
        
        # Initialize class variables
        if direction not in ["forward", "backward"]:
            logger.error("Invalid direction: '%s'. Expected 'forward' or 'backward'", direction)
            raise ValueError("Unknown direction type")
        self.pts = pts
        self.direction = direction
        self.threshold = threshold
        self.period = period
        self.pts_states_num = self.pts.states_num
        self.rmc_width = self.period * self.pts.states_num
        
        # Create transition probability matrices A, B, and C
        level0_rmc_list = [self.get_global_state((0, i)) for i in range(self.rmc_width)]
        level1_rmc_list = [self.get_global_state((1, i)) for i in range(self.rmc_width)]
        self.A, self.A_nonzero_locs = self._create_prob_matrix(level1_rmc_list, level0_rmc_list)
        self.B, self.B_nonzero_locs = self._create_prob_matrix(level1_rmc_list, level1_rmc_list)
        self.C, self.C_nonzero_locs = self._create_prob_matrix(level0_rmc_list, level1_rmc_list)
        
        logger.info("Regular Markov Chain with direction '%s' successfully created, each level contains %d states", direction, self.rmc_width)

    def get_global_state(self, rmc_state):
        """
        Converts the regular Markov chain state to a global state.
        """
        num = rmc_state[0] * (self.rmc_width) + rmc_state[1]
        multiple, remainder = divmod(num, self.pts_states_num)
        if self.direction == 'forward':
            variable_value = self.threshold + 1 + multiple
        else:
            variable_value = -1 * (self.threshold + 1 + multiple)
        return remainder, variable_value

    def _create_prob_matrix(self, from_global_state_list, to_global_state_list):
        """
        Creates a transition probability matrix.
        """
        nonzero_locs = set()
        re_matrix = np.zeros((self.rmc_width, self.rmc_width), dtype=object)
        for i in range(self.rmc_width):
            for j in range(self.rmc_width):
                prob = self.pts.get_mc_transition_prob(from_global_state_list[i], to_global_state_list[j])
                if prob:
                    nonzero_locs.add((i, j))
                    re_matrix[i, j] = prob
        return re_matrix, nonzero_locs
        
    def get_boolean_reachability_matrix(self):
        """
        Calculates boolean reachability matrix using sparse matrix operations.
        Returns dense boolean matrix for compatibility.
        """
        # Convert to sparse CSR format with binary values
        A = scip.csr_matrix(self.A != 0, dtype=bool)
        B = scip.csr_matrix(self.B != 0, dtype=bool)
        C = scip.csr_matrix(self.C != 0, dtype=bool)

        # Initialize reachability matrices
        shape = (self.rmc_width, self.rmc_width)
        re_old = scip.csr_matrix(shape, dtype=bool)
        re_new = scip.csr_matrix(shape, dtype=bool)

        while True:
            # Compute terms using sparse matrix multiplication
            B_term = B @ re_new
            C_term = C @ (re_new @ re_new)
            
            # Sparse element-wise OR using max() operation
            new_re = A.maximum(B_term).maximum(C_term)

            # Check for convergence using sparse matrix comparison
            if (new_re != re_old).nnz == 0:
                return new_re.toarray()  # Return dense array for compatibility

            # Update for next iteration
            re_old, re_new = re_new, new_re

    def get_approximate_reachability_matrix(self, tol=1e-8, max_iter=50000):
        """
        Computes approximate reachability matrix.
        """
        # Convert to numpy matrix with float values
        A_float = self.hybrid_to_float_matrix(self.A)
        B_float = self.hybrid_to_float_matrix(self.B)
        C_float = self.hybrid_to_float_matrix(self.C)

        re_new = np.zeros_like(A_float)
        for iteration in range(max_iter):
            re_next = A_float + B_float @ re_new + C_float @ (re_new @ re_new)
            if np.linalg.norm(re_next - re_new) < tol:
                print(f"Converged after {iteration + 1} iterations.")
                return re_next
            re_new = re_next
        logger.warning("Maximum number of iterations (%d) reached without convergence.", max_iter)
        print("Warning: Maximum number of iterations reached without convergence.")
        return re_new

    def hybrid_to_float_matrix(self, hybrid_matrix):
        """
        Convert a hybrid component numpy matrix to a float numpy matrix.
        """
        float_matrix = np.zeros(hybrid_matrix.shape, dtype=float)
        for i in range(hybrid_matrix.shape[0]):
            for j in range(hybrid_matrix.shape[1]):
                element = hybrid_matrix[i, j]
                if element == 0:
                    float_matrix[i, j] = 0.0
                else:
                    numerator, denominator = element
                    float_matrix[i, j] = numerator / denominator
        return float_matrix

    def hybrid_to_sympy_rational(self, hybrid_matrix):
        """
        Convert a hybrid component numpy matrix to a rational sympy matrix.
        """
        rows, cols = hybrid_matrix.shape
        sympy_matrix = []
        
        for i in range(rows):
            row = []
            for j in range(cols):
                element = hybrid_matrix[i, j]
                if element == 0:
                    row.append(sp.Rational(0))
                else:
                    numerator, denominator = element
                    row.append(sp.Rational(numerator, denominator))
            sympy_matrix.append(row)
        return sp.Matrix(sympy_matrix)

    def _get_bscc_category(self, bscc, ac_matrix):
        """
        Determines the category of the bottom strongly connected component by calculating its steady-state distribution.
        """
        size = len(bscc)

        # Directly return the result for a BSCC with only one state
        if size == 1:
            return bscc[0] // self.rmc_width

        # Extract the submatrix of the adjacency matrix corresponding to the BSCC
        hybrid_matrix = ac_matrix[np.ix_(bscc, bscc)]

        # Convert hybrid matrix to a rational transition matrix
        transition_matrix = self.hybrid_to_sympy_rational(hybrid_matrix)

        # Set up the system of equations for the steady-state distribution
        pi_symbols = sp.symbols(f'pi0:{size}')
        pi_vector = sp.Matrix(pi_symbols)
        equations = [sp.Eq(sum(pi_vector[j] * transition_matrix[j, i] for j in range(size)), pi_vector[i]) for i in
                     range(size)]
        equations.append(sp.Eq(sum(pi_vector), 1))
        solution = sp.solve(equations, pi_symbols, dict=True)

        if len(solution) > 1:
            logger.error("Multiple solutions found for steady-state distribution. Expected a unique solution.")
            raise ValueError("Multiple solutions found, expected a unique solution.")

        if solution:
            stationary_distribution = [solution[0][pi_symbols[i]] for i in range(size)]

            # Calculate left and right transition trends
            left_transition_trend = 0
            right_transition_trend = 0
            for i, state in enumerate(bscc):
                ac_level = state // self.rmc_width
                if ac_level == 0:
                    left_transition_trend += stationary_distribution[i]
                if ac_level == 2:
                    right_transition_trend += stationary_distribution[i]
            if left_transition_trend < right_transition_trend:
                return 2
            elif left_transition_trend > right_transition_trend:
                return 0
            else:
                return 1
        else:
            logger.error("No solution found for the stationary distribution.")
            raise ValueError("No solution found for the stationary distribution.")

    def _analyze_runway(self, max_level):
        """
        Constructs and analyzes the runway to identify trap states and exit states.
        """
        runway = nx.DiGraph()
        level1_nodes = {(1, i) for i in range(self.rmc_width)}
        left_barrier = {(0, i) for i in range(self.rmc_width)}
        right_barrier = {(max_level, i) for i in range(self.rmc_width)}
        runway.add_nodes_from(level1_nodes)
        runway.add_nodes_from(left_barrier)
        runway.add_nodes_from(right_barrier)

        #construct runway
        for i, j in self.A_nonzero_locs:
            for k in range(0, max_level):
                runway.add_edge((k + 1, i), (k, j))
                
        for i, j in self.B_nonzero_locs:
            for k in range(0, max_level + 1):
                runway.add_edge((k, i), (k, j))
                
        for i, j in self.C_nonzero_locs:
            for k in range(1, max_level):
                runway.add_edge((k, i), (k + 1, j))
        
        boolean_reachability_matrix = self.get_boolean_reachability_matrix()
        source_nodes = [(max_level, i) for i in range(self.rmc_width)]
        target_nodes = [(max_level - 1, j) for j in range(self.rmc_width)]
        edges = {(source_nodes[i], target_nodes[j]) for i in range(self.rmc_width) for j in range(self.rmc_width) if
                 boolean_reachability_matrix[i, j]}
        runway.add_edges_from(edges)
        
        trap_nodes = set(runway.nodes)
        for node in left_barrier:
            runway.add_edge(node, 'left_fake')
        for node in right_barrier:
            runway.add_edge(node, 'right_fake')
        left_barrier_ancestors = nx.ancestors(runway, 'left_fake')
        right_barrier_ancestors = nx.ancestors(runway, 'right_fake')
        trap_nodes = trap_nodes - left_barrier_ancestors - right_barrier_ancestors
        runway.remove_nodes_from(['left_fake', 'right_fake'])

        trapped_level1_states, exit_level1_states = set(), set()
        for node in level1_nodes:
            reachable_nodes = nx.descendants(runway, node) | {node}
            if reachable_nodes & trap_nodes:
                trapped_level1_states.add((self.direction, node))
            elif not (reachable_nodes & right_barrier):
                exit_level1_states.add((self.direction, node))
        return trapped_level1_states, exit_level1_states, boolean_reachability_matrix

    def get_level1_info(self):
        """
        Determines level1 states info based on the coupled markov chain and runway analysis.
        """
        logger.info("Starting the analysis of Regular Markov Chain with direction: %s.", self.direction)

        ac_matrix = np.block([[self.A, self.B, self.C], [self.A, self.B, self.C], [self.A, self.B, self.C]])
        abstract_chain = nx.from_numpy_array(ac_matrix != 0, create_using=nx.DiGraph())
        sccs = [list(scc) for scc in nx.strongly_connected_components(abstract_chain)]

        condensed_graph = nx.DiGraph()
        condensed_graph.add_nodes_from(range(len(sccs)))
        node_to_scc = {}
        for idx, scc in enumerate(sccs):
            for node in scc:
                node_to_scc[node] = idx
                
        # Process each edge to determine SCC connections
        for u, v in abstract_chain.edges():
            i = node_to_scc[u]
            j = node_to_scc[v]
            if i != j:
                condensed_graph.add_edge(i, j)

        bottom_sccs_nodes_categories = dict()
        for node in condensed_graph.nodes:
            if condensed_graph.out_degree(node) == 0:
                bottom_sccs_nodes_categories[node] = self._get_bscc_category(sccs[node], ac_matrix)

        axis_acstates_categories = {key: 0 for key in range(self.rmc_width)}
        for i in range(len(sccs)):
            if i in bottom_sccs_nodes_categories:
                bottom_category = bottom_sccs_nodes_categories[i]
                for acstate in sccs[i]:
                    if acstate < self.rmc_width:
                        axis_acstates_categories[acstate] = max(axis_acstates_categories[acstate], bottom_category)
            else:
                for bottom_node, bottom_category in bottom_sccs_nodes_categories.items():
                    if nx.has_path(condensed_graph, i, bottom_node):
                        for acstate in sccs[i]:
                            if acstate < self.rmc_width:
                                axis_acstates_categories[acstate] = max(axis_acstates_categories[acstate],
                                                                        bottom_category)
                                
        logger.info("Starting runway analysis. Total runway states to be analyzed: %d.", 3 * self.rmc_width * self.rmc_width)
        
        max_level = 3 * self.rmc_width
        trapped_level1_states, exit_level1_states, boolean_reachability_matrix = self._analyze_runway(max_level)
        
        logger.info("Runway analysis completed. Trapped states: %d, Exit states: %d", len(trapped_level1_states), len(exit_level1_states))
        
        excluded_states = trapped_level1_states | exit_level1_states
        transient_level1_states, nullrec_level1_states = set(), set()
        transient_level1_states |= trapped_level1_states
        for state, category in axis_acstates_categories.items():
            rmc_state = (self.direction, (1, state))
            if rmc_state not in excluded_states:
                if category == 2:
                    transient_level1_states.add(rmc_state)
                elif category == 1:
                    nullrec_level1_states.add(rmc_state)
                    
        logger.info("Completed the analysis of Regular Markov Chain with direction: %s.", self.direction)
        return transient_level1_states, nullrec_level1_states, boolean_reachability_matrix
