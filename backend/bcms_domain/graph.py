"""Validated depends-on graph. PROCESS:A -> ASSET:B means A depends on B."""
import networkx as nx


def build_graph(process_ids, asset_ids, dependencies):
    valid = {*(f'PROCESS:{i}' for i in process_ids), *(f'ASSET:{i}' for i in asset_ids)}
    graph = nx.DiGraph()
    graph.add_nodes_from(sorted(valid))
    invalid = 0
    for d in dependencies:
        u, v = f"{d['from_type']}:{d['from_id']}", f"{d['to_type']}:{d['to_id']}"
        if u not in valid or v not in valid:
            invalid += 1
            continue
        graph.add_edge(u, v)
    warnings = []
    if invalid:
        warnings.append('UNAVAILABLE_DEPENDENCY_ENDPOINTS: excluded references outside the active tenant graph')
    if not graph.number_of_edges():
        warnings.append('EMPTY_DEPENDENCY_GRAPH: zero confirmed impacts does not establish safety')
    if any(graph.degree(f'PROCESS:{p}') == 0 for p in process_ids):
        warnings.append('INCOMPLETE_PROCESS_COVERAGE: some active processes have no registered dependencies')
    graph.graph['warnings'] = warnings
    return graph


def dependency_norm(graph, process_id, total_processes):
    node = f'PROCESS:{process_id}'
    if total_processes <= 1 or node not in graph:
        return 0.0
    count = sum(n.startswith('PROCESS:') for n in nx.ancestors(graph, node))
    return round(count / (total_processes - 1), 4)


def cascade(graph, disrupted_ids):
    if not isinstance(disrupted_ids, list) or any(type(i) is not int or i <= 0 or f'ASSET:{i}' not in graph for i in disrupted_ids):
        raise ValueError('Disrupted assets must reference active assets in the current organization')
    affected = set()
    for i in disrupted_ids:
        affected.update(n for n in nx.ancestors(graph, f'ASSET:{i}') if n.startswith('PROCESS:'))
    warnings = list(graph.graph.get('warnings', []))
    if not disrupted_ids:
        warnings.append('NO_DISRUPTED_ASSETS: no failure input provided')
    elif not affected:
        warnings.append('NO_REGISTERED_DEPENDENTS: no confirmed process impact; unregistered dependencies remain unknown')
    return sorted(int(n.split(':')[1]) for n in affected), warnings
