import re
from itertools import product

def simplify_product_advanced(product_str):
    """
    Simplifies an operator product string with correct commutation rules.
    - Operators from different parties (A, B) commute.
    - Operators from the same party (A1, A2) DO NOT commute.
    """
    operators = [op for op in product_str.split() if op != "Id"]
    if not operators:
        return "Id"

    # 1. Group operators by party, maintaining original relative order.
    party_groups = {}
    for op in operators:
        party = op[0]
        if party not in party_groups:
            party_groups[party] = []
        party_groups[party].append(op)
    
    # 2. For each party, simplify adjacent O^2=I pairs iteratively.
    for party, op_list in party_groups.items():
        simplified = True
        while simplified:
            simplified = False
            if len(op_list) < 2:
                break
            next_op_list = []
            i = 0
            while i < len(op_list):
                if i + 1 < len(op_list) and op_list[i] == op_list[i+1]:
                    i += 2
                    simplified = True
                else:
                    next_op_list.append(op_list[i])
                    i += 1
            op_list = next_op_list
        party_groups[party] = op_list

    # 3. Recombine party groups in canonical order (A then B).
    final_ops = []
    for party in sorted(party_groups.keys()):
        final_ops.extend(party_groups[party])

    if not final_ops:
        return "Id"
    return " ".join(final_ops)


def generate_level_n_set(base_operators, level):
    """Generates the full operator set up to a given integer level 'n'."""
    identity = "Id"
    if level == 0:
        return {identity}

    operator_set = {identity}
    operator_set.update(base_operators)
    
    current_level_products = set(base_operators)
    for _ in range(1, level):
        next_level_products = set()
        for op1 in current_level_products:
            for op2 in base_operators:
                product_str = f"{op1} {op2}"
                simplified = simplify_product_advanced(product_str)
                next_level_products.add(simplified)
        operator_set.update(next_level_products)
        current_level_products = next_level_products
        
    return operator_set

def generate_string_term_set(base_operators_by_party, term_str):
    """Generates the operator set for a specific string term like 'AB' or 'AAB'."""
    operator_pools = []
    for party_char in term_str:
        if party_char in base_operators_by_party:
            operator_pools.append(base_operators_by_party[party_char])
        else:
            return set()
            
    term_set = set()
    for combo in product(*operator_pools):
        product_str = " ".join(combo)
        simplified = simplify_product_advanced(product_str)
        term_set.add(simplified)
        
    return term_set

def npa_hierarchy_intermediate(base_operators, level_str):
    """
    Generates and returns the symbolic structure of the NPA hierarchy.
    """
    final_operator_set = set()

    base_operators_by_party = {}
    for op in base_operators:
        party = op[0]
        if party not in base_operators_by_party:
            base_operators_by_party[party] = []
        base_operators_by_party[party].append(op)

    terms = [term.strip() for term in level_str.split('+')]
    
    for term in terms:
        if term.isdigit():
            level = int(term)
            level_set = generate_level_n_set(base_operators, level)
            final_operator_set.update(level_set)
        else:
            term_set = generate_string_term_set(base_operators_by_party, term)
            final_operator_set.add("Id")
            final_operator_set.update(term_set)

    sorted_operator_set = sorted(list(final_operator_set), key=lambda s: (s.count(' ') + (1 if s != "Id" else 0), s))
    
    n = len(sorted_operator_set)
    moment_matrix_symbolic = [["" for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(n):
            op_i_str = sorted_operator_set[i]
            op_j_str = sorted_operator_set[j]
            
            op_i_dag_parts = list(reversed(op_i_str.split()))
            op_j_parts = op_j_str.split()

            full_product_str = " ".join(op_i_dag_parts + op_j_parts)
            
            simplified = simplify_product_advanced(full_product_str)
            moment_matrix_symbolic[i][j] = simplified
    
    return sorted_operator_set, moment_matrix_symbolic
