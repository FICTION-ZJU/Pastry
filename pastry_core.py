from src.parsers.parser import parse_pcp
from src.models.pts import ProbabilisticTransitionSystem
from src.models.rmc import RegularMarkovChain
from src.models.lmc import LabeledMarkovChain
from src.utils.project_utils import analyze_threshold_and_period_from_pts
import logging

logger = logging.getLogger("pastry")

def run_core_analysis(prog_str):
    """
    Perform termination analysis on a probabilistic counter program.

    :param prog_str: A string representing a probabilistic counter program.
    :return: A dictionary with Boolean termination results, of the form:
             {
                 "AST": True or False,
                 "PAST": True or False
             }
    """
    logger.info("Starting core analysis")

    # Parse the program into an internal representation
    pcp_prog = parse_pcp(prog_str)

    # Build the probabilistic transition system
    pts = ProbabilisticTransitionSystem(pcp_prog)

    # Analyze threshold and periods (used to construct regular Markov chains)
    threshold, period_po, period_ne = analyze_threshold_and_period_from_pts(pts)

    # Build forward-directed regular Markov chain
    rmc_forward = RegularMarkovChain(pts, 'forward', threshold, period_po)

    # Build backward-directed regular Markov chain
    rmc_backward = RegularMarkovChain(pts, 'backward', threshold, period_ne)

    # Construct the finite labeled Markov chain that simulates the program's termination behavior
    lmc = LabeledMarkovChain(pts, threshold, rmc_forward, rmc_backward)
    return lmc.is_ast_and_past()

