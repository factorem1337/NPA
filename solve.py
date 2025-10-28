import numpy as np
import cvxpy as cp

# Import the blueprint generator from the npa.py file you provided
from npa import npa_hierarchy_intermediate

def solve_npa_from_symbolic(symbolic_basis, symbolic_matrix, objective_coeffs):
    """
    Builds and solves a dimension-independent Semidefinite Program (SDP) 
    from the symbolic NPA matrix structure.

    This function takes the abstract "blueprint" of the moment matrix and
    translates it into a concrete optimization problem that CVXPY can solve.

    Args:
        symbolic_basis (list): The list of unique monomial strings that label the rows 
                               and columns of the moment matrix (e.g., ['Id', 'A1', 'A1 B1']).
        symbolic_matrix (list of lists): The 2D list where each entry is a string 
                                         representing the simplified operator product.
        objective_coeffs (dict): A dictionary mapping monomial strings to their 
                                 coefficients in the Bell inequality to be maximized.

    Returns:
        float: The optimal value found by the SDP solver, representing the upper bound
               on the Bell inequality's quantum value.
    """
    n = len(symbolic_basis)
    
    # --- Step 1: Identify all unique monomials and create a CVXPY variable for each ---
    # Scan the entire symbolic matrix blueprint to find every unique operator product
    # (monomial) that appears as an entry.
    unique_monomials = sorted(list(set(item for row in symbolic_matrix for item in row)))
    # Create a dictionary where each unique monomial string is a key, and its value
    # is a CVXPY variable. By default, these represent complex-valued moments <S>.
    monomial_vars = {mon: cp.Variable(complex=True) for mon in unique_monomials}
    
    # --- Step 2: Enforce reality conditions based on physical principles ---
    # Certain expectation values are guaranteed to be real numbers. We must
    # enforce this in the SDP for correctness.
    real_valued_keys = {"Id"}
    # Single operator expectation values like <A1> or <B2> are real.
    for op in symbolic_basis:
        if " " not in op: real_valued_keys.add(op)
    # Correlation terms between parties like <A1 B1> are also real.
    for op1 in symbolic_basis:
        if op1.startswith('A'):
            for op2 in symbolic_basis:
                if op2.startswith('B'):
                    # The key must match the canonical form from npa.py's simplify function
                    real_valued_keys.add(" ".join(sorted([op1, op2])))
    
    # Re-declare the variables for real-valued moments without the complex=True flag.
    for key in real_valued_keys:
        if key in monomial_vars:
            monomial_vars[key] = cp.Variable()

    # The expectation value of the identity operator is always 1, not a variable.
    monomial_vars['Id'] = 1.0

    # --- Step 3: Build the moment matrix Gamma as a CVXPY expression ---
    # This programmatically assembles the individual monomial variables into the full
    # moment matrix variable according to the symbolic blueprint.
    gamma = cp.bmat([[monomial_vars[symbolic_matrix[i][j]] for j in range(n)] for i in range(n)])

    # --- Step 4: Define the objective function to be maximized ---
    # The objective is the Bell inequality, constructed as a linear combination of the
    # monomial variables using the provided coefficients.
    objective = cp.sum([coeff * monomial_vars[op] for op, coeff in objective_coeffs.items() if op in monomial_vars])
    
    # --- Step 5: Define the core NPA constraint ---
    # The single most important constraint is that the moment matrix must be
    # positive semidefinite. This is the mathematical condition for a set of
    # correlations to be compatible with quantum mechanics.
    constraints = [gamma >> 0]
    
    # --- Step 6: Solve the optimization problem ---
    problem = cp.Problem(cp.Maximize(cp.real(objective)), constraints)
    # The problem is passed to an external solver (SCS is a good default).
    problem.solve(solver=cp.SCS, verbose=True)

    print("\n--- Solver Results ---")
    if problem.status in ["infeasible", "unbounded"]:
        print(f"Solver failed with status: {problem.status}")
        return None
    
    print(f"Status: {problem.status}")
    print(f"Optimal Value: {problem.value:.8f}")
    return problem.value

if __name__ == '__main__':
    # --- NON-INTERACTIVE CONFIGURATION ---
    # Define the Bell scenario to be tested.
    num_a_settings = 2
    num_b_settings = 2
    base_operators = [f"A{i+1}" for i in range(num_a_settings)] + \
                     [f"B{i+1}" for i in range(num_b_settings)]

    # Define the Bell functional's coefficients as a dictionary.
    # This example is for the CHSH inequality: + A1*B1 + A1*B2 + A2*B1 - A2*B2
    objective_coeffs = {
        "A1 B1": 1,
        "A1 B2": 1,
        "A2 B1": 1,
        "A2 B2": -1
    }
    
    # Define the NPA hierarchy level to solve for.
    # '1+AB' is a common level that is sufficient for the CHSH inequality.
    level_to_solve = "2+AAB"

    print("="*60)
    print(f"      Running Dimension-Independent Optimizer for CHSH")
    print("="*60)
    
    # --- Main Execution ---
    # 1. Get the symbolic structure (blueprint) from the npa.py library.
    try:
        basis, sym_matrix = npa_hierarchy_intermediate(base_operators, level_to_solve)
        print(f"Generated symbolic structure for level '{level_to_solve}'. Matrix size: {len(basis)}x{len(basis)}.")
    except Exception as e:
        print(f"\nError from npa.py: {e}"); exit()
        
    # 2. Call the main solver function with the blueprint and the objective.
    max_bound = solve_npa_from_symbolic(basis, sym_matrix, objective_coeffs)

    # 3. Display the final result and compare it to the known theoretical value.
    tsirelson_bound = 2 * np.sqrt(2)
    print("\n" + "="*50)
    print(f"      FINAL RESULT FOR LEVEL '{level_to_solve}'")
    print("="*50)
    if max_bound is not None:
        print(f"Maximum Quantum Value <= {max_bound:.8f}")
        print(f"Known Tsirelson Bound:   {tsirelson_bound:.8f}")
    else:
        print("Could not determine the maximum value.")
    print("="*50)
