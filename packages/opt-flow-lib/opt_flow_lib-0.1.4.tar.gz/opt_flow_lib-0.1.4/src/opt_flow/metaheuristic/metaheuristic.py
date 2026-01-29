from collections import deque
from typing import Dict, Set, Optional, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from opt_flow.metaheuristic.algorithm import Algorithm
from opt_flow.structure.base_individual import BaseIndividual
from opt_flow.metaheuristic.algorithm_type import AlgorithmType
from opt_flow.acceptance import BaseAcceptance 
from opt_flow.stats import ImprovementHistory, StatsRecord, StatsTracker
from opt_flow.stopping import BaseStopping, NoStopping
from opt_flow.callback import CallbackArgs
from opt_flow.stats.improvement_history_view import ImprovementHistoryView
from os import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
from opt_flow.config.config import config
from pickle import PicklingError, dumps
from logging import error
from opt_flow.stats import StatsTracker
from opt_flow.utils import RandomClass
from functools import wraps
from pathlib import Path
from opt_flow.core import BasePopulation
from opt_flow.reproducibility.iterations_registry import _init_registry, _register_execution

def _init_worker(config_dict):
    from opt_flow.utils.logger import _configure_log
    from opt_flow.config.config import configure

    _configure_log()

    configure(config_dict)


def _execute_node(
    node: "Algorithm", inputs: List[Optional[BaseIndividual]], visited_individuals: Optional[List[Optional[BaseIndividual]]]=None
) -> BaseIndividual:
    """
    Dispatch execution based on node type.
    """
    algo = node.alg
    ntype = node.alg_type
    if not visited_individuals:
        visited_individuals = []

    if ntype == AlgorithmType.population:
        sol = algo.create()
        return sol, algo
    elif ntype == AlgorithmType.trajectory:
        algo.iterate(inputs[0])
        return inputs[0], algo
    elif ntype == AlgorithmType.recombination:
        return algo.recombine(inputs[0], inputs[1]), algo
    elif ntype == AlgorithmType.acceptance:
        return Metaheuristic._find_best(algo, inputs, visited_individuals), algo
    else:
        raise NotImplementedError(f"Unknown algorithm type {ntype}")

def _ensure_on_start(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self._on_start()
        return method(self, *args, **kwargs)
    return wrapper

def _backtrack_best_path(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        sinks = self._get_sinks()
        if self.nodes[sinks[0]].final_individual:
            best = self.nodes[sinks[0]].get_individual()
            self._backtrack_best_path()
            return best
        return result
    return wrapper

def _increment_population_iterations(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self._tracker.increment_iteration()
        return method(self, *args, **kwargs)
    return wrapper


class Metaheuristic(RandomClass):
    """
    Base class for metaheuristics composed of interconnected algorithm nodes.
    """
    
    decorators = [_register_execution, _ensure_on_start, _backtrack_best_path]
    
    pop_decorators = [_increment_population_iterations]
    
    def __init__(self, *args, default_acceptance: Optional[BaseAcceptance] = None, seed: Optional[int] = None, stopping: Optional[BaseStopping] = None, callbacks = None, **kwargs):
        super().__init__(*args, seed=seed, **kwargs)
        self.nodes: Dict[str, "Algorithm"] = {}
        self.out_edges: Dict[str, Set["Algorithm"]] = {}
        self.in_edges: Dict[str, Set["Algorithm"]] = {}
        self.default_acceptance = default_acceptance or config.default_acceptance
        self._best_paths = []
        if not hasattr(self, "_callbacks") or not self._callbacks:
            self._callbacks = callbacks or []
        self._reset_nodes()
        self._tracker = StatsTracker()
        if not hasattr(self, "_stopping_criterion") or isinstance(self._stopping_criterion, NoStopping):
            self._stopping_criterion = stopping or NoStopping()
        self._execution_id = 0
        config._increment_alg_id()
        _init_registry()
        
    @property
    def alg_id(self):
        return int(config.alg_id)
    
    @classmethod
    def pipeline(cls, *algs) -> "Metaheuristic":
        mh = cls(data=None)
        last_alg = None
        for alg in algs:
            mh.add_algorithm(alg)
            if last_alg is not None:
                mh.connect(last_alg, alg)
            last_alg = alg
        return mh
            
    
    @property
    def id(self):
        return 'ALG' + str(self.alg_id) + '_' + str(self._execution_id)
    
    def _increment_execution_id(self):
        self._execution_id += 1
        
    def __init_subclass__(cls):
        super().__init_subclass__()
        for name in ("iterate", "create"):
            method = getattr(cls, name, None)
            if callable(method):
                # Apply decorators
                for dec in reversed(cls.decorators):
                    method = dec(method)
                if name == "create" and hasattr(cls, 'pop_decorators'):
                    for dec in reversed(cls.pop_decorators):
                        method = dec(method)
                setattr(cls, name, method)


    def _run_callbacks(self, args: CallbackArgs):
        for cb in self._callbacks:
            try:
                cb(args)
            except Exception as e:
                error(f'Error invoking callback {cb.__class__.__name__}: {e}')
                raise
        
    def _on_start(self):
        dependencies = {dep for x in self._callbacks for dep in x.__dependencies__}.union(set(self._stopping_criterion.__dependencies__))
        dependencies.add("individual")
        self._tracker = StatsTracker(dependencies)
        self._stopping_criterion._start()

        
    def should_continue(self, alg: "Algorithm") -> bool:
        """
        Determines whether the metaheuristic should continue based on the
        stopping criterion and acceptance.

        Args:
            alg (Algorithm): Algorithm node whose individual is being evaluated.

        Returns:
            bool: True if the algorithm can continue, False if it should stop.
        """
        individual = alg.get_individual()
        if self._stopping_criterion._is_null(individual):
            return False
        improved = self.default_acceptance.compare_individuals(self._tracker.get_best_individual(), individual)
        record = StatsRecord(individual.get_objective(), improved, individual, alg.name)
        args = CallbackArgs.from_stats(record, self._tracker)
        should_continue = not self._stopping_criterion._stop(args)
        self._tracker._record(record)
        self._run_callbacks(args) 
        return should_continue
    

    def get_best_paths(self) -> List["Algorithm"]:
        """
        Returns the best individual paths through the algorithm graph.

        Returns:
            List[List[Algorithm]]: A list of paths, each path being a list of
                                   Algorithm nodes representing the best sequence.
        """
        
        paths = [
            [self.nodes[nid] for nid in reversed(path)] for path in self._best_paths
        ]

        unique_paths = []
        for p in paths:
            if not any(
                len(p) < len(q) and all(node in q for node in p)
                for q in paths
            ):
                unique_paths.append(p)
        return unique_paths

    def get_improvement_history(self) -> ImprovementHistory:
        """
        Returns the improvement history for the metaheuristic execution.

        The history is constructed by aggregating the improvement histories
        of nodes in the best path.

        Returns:
            ImprovementHistory: Object containing the recorded improvements.
        """
        improvement_history = ImprovementHistory()
        best_paths = self.get_best_paths()
        if len(best_paths) == 1:
            best_path = best_paths[0]
            for node in best_path:
                improvement_history.extend(node.get_improvement_history())
        return improvement_history
    
    def get_improvement_history_view(self) -> ImprovementHistoryView:
        """
        Returns the improvement history view for the metaheuristic execution.

        The history is constructed by aggregating the improvement histories
        of nodes in the best path.

        Returns:
            ImprovementHistoryView: Object containing a view of the recorded 
            improvements.
        """
        return self.get_improvement_history().view()

    def _reset_nodes(self):
        for node in self.nodes.values():
            node._reset()
        self._best_paths.clear()


    def _validate_pickle(self) -> bool:
        valid = True
        for node in self.nodes.values():
            try:
                dumps(node.alg)
            except Exception as e:
                error(f"Error pickling the algorithm {node.id}: {e}")
                valid = False
        return valid

    def add_algorithm(self, alg: "Algorithm"):
        """
        Adds an algorithm node to the metaheuristic graph.

        Args:
            alg (Algorithm): Algorithm node to add.
        """
        if alg.id not in self.nodes:
            self.nodes[alg.id] = alg
        self.out_edges.setdefault(alg.id, set())
        self.in_edges.setdefault(alg.id, set())

    def connect(self, src_node: "Algorithm", tgt_node: "Algorithm"):
        """
        Connects two algorithm nodes in the metaheuristic graph.

        Args:
            src_node (Algorithm): Source algorithm node.
            tgt_node (Algorithm): Target algorithm node.

        Raises:
            KeyError: If either node does not exist in the metaheuristic.
        """
        src_id = src_node.id
        tgt_id = tgt_node.id
        if src_id not in self.nodes or tgt_id not in self.nodes:
            raise KeyError(f"Cannot connect {src_id} -> {tgt_id}, node not found")
        self.out_edges[src_id].add(tgt_node)
        self.in_edges[tgt_id].add(src_node)

    def _sequential_execute(self):
        indegree = self._calculate_indegree()
        depth = self._calculate_depth(indegree)
        while True:
            queue = deque([nid for nid, depth_val in depth.items() if depth_val == 0])
            if not queue:
                break
            nid = queue.popleft()
            node = self.nodes[nid]
            if node.alg_type == AlgorithmType.acceptance:
                inputs = [pred.get_individual() for pred in sorted(self.in_edges[nid], key=lambda x: x.id) if pred.alg_type != AlgorithmType.acceptance]
                self.rng.shuffle(inputs)
                visited_individuals = [pred.get_individual() for pred in sorted(self.in_edges[nid], key=lambda x: x.id) if pred.alg_type == AlgorithmType.acceptance]
            else:
                inputs = [pred.get_individual() for pred in sorted(self.in_edges[nid], key=lambda x: x.id)]
                visited_individuals = []

            if node.final_individual is None:
                next_solution, _ = _execute_node(node, inputs, visited_individuals)
                node.set_individual(next_solution)

            for succ in self.out_edges[nid]:
                indegree[succ.id] -= 1
            del indegree[nid]
            depth = self._calculate_depth(indegree)

    def _validate_inputs(self, inputs: List[Any], node_id):
        valid = True
        for input in inputs:
            try:
                dumps(input)
            except Exception as e:
                error(f"Error pickling the inputs of node {node_id}: {e}")
                valid = False
        return valid

    def _parallel_execute(self, max_workers: int):
        if not config.parallel:
            raise RuntimeError("Cannot execute a parallel algorithm without setting parallel to True.")
        if not self._validate_pickle():
            return
        indegree = self._calculate_indegree()
        depth = self._calculate_depth(indegree)
        result_nodes = {}
        try:
            with ProcessPoolExecutor(
                max_workers=max_workers,
                initializer=_init_worker,
                initargs=(config.to_dict(),),
            ) as executor:
                while True:
                    ready_nodes = [
                        nid
                        for nid, depth_val in depth.items()
                        if depth_val == 0 and nid not in result_nodes
                    ]
                    if not ready_nodes:
                        break

                    futures = {}
                    for nid in ready_nodes:
                        node = self.nodes[nid]
                        if node.alg_type == AlgorithmType.acceptance:
                            inputs = [result_nodes[pred.id] for pred in self.in_edges[nid] if pred.alg_type != AlgorithmType.acceptance]
                            visited_solutions = [result_nodes[pred.id]for pred in self.in_edges[nid] if pred.alg_type == AlgorithmType.acceptance]
                        else:
                            inputs = [result_nodes[pred.id] for pred in self.in_edges[nid]]
                            visited_solutions = []
                        if self._validate_inputs(inputs, nid):
                            futures[executor.submit(_execute_node, node, inputs, visited_solutions)] = node

                    for future in as_completed(futures):
                        node = futures[future]
                        try:
                            result, algo = future.result()
                            node.alg = algo
                            node.set_individual(result)
                            result_nodes[node.id] = result
                        except Exception as e:
                            error(
                                f"Error processing result of algorithm {node.id}: {e}"
                            )

                    for nid in ready_nodes:
                        for succ in self.out_edges[nid]:
                            indegree[succ.id] -= 1
                        del indegree[nid]
                    depth = self._calculate_depth(indegree)
        except PicklingError as e:
            error(f"Error ocurred picking the algorithm: {e}")
            raise
        except Exception as e:
            error(f"Unexpected error while executing in parallel: {e}")
            raise
        for nid, sol in result_nodes.items():
            self.nodes[nid].set_individual(sol)

    def _calculate_depth(self, indegree: dict[str, int]) -> dict[str, int]:
        """
        Calculate the depth (longest path length from any root)
        for every node in the directed graph.

        Returns:
            dict[node_id, depth]
        """
        temp_indegree = indegree.copy()
        depth: dict[str, int] = dict.fromkeys(temp_indegree.keys(), 0)

        queue = deque([nid for nid, deg in temp_indegree.items() if deg == 0])

        while queue:
            nid = queue.popleft()
            for succ in self.out_edges[nid]:
                depth[succ.id] = max(depth[succ.id], depth[nid] + 1)
                temp_indegree[succ.id] -= 1
                if temp_indegree[succ.id] == 0:
                    queue.append(succ.id)

        return depth

    def _calculate_indegree(self) -> Dict[str, int]:
        return {nid: len(self.in_edges[nid]) for nid in self.nodes.keys()}

    def _get_starts(self) -> List[str]:
        return [nid for nid, ins in self.in_edges.items() if not ins]

    def _validate_ins_and_outs(self):
        sinks = self._get_sinks()
        if not sinks:
            raise RuntimeError("No final algorithms in metaheuristic")
        starts = self._get_starts()
        if not starts:
            raise RuntimeError("No starting algorithms in metaheuristic")

    def create(self, parallel=False, max_workers=None) -> BaseIndividual:
        """
        Executes the metaheuristic to create an individual.

        Args:
            parallel (bool, optional): If True, executes nodes in parallel.
            max_workers (int, optional): Number of parallel workers.

        Returns:
            BaseIndividual: The individual created by the metaheuristic.
        """
        if parallel and not max_workers:
            max_workers = cpu_count()
        return self._run_create(parallel, max_workers)
        
    def _run_create(self, parallel=False, max_workers=None) -> BaseIndividual:
        self._validate_ins_and_outs()
        sinks = self._get_sinks()
        if len(sinks) != 1:
            final_node = Algorithm(
                self.default_acceptance, "final acceptance", AlgorithmType.acceptance
            )
            self.add_algorithm(final_node)
            self.connect_all(final_node)

        if not parallel:
            self._sequential_execute()
        else:
            max_workers = max_workers or cpu_count()
            self._parallel_execute(max_workers)
        return self.nodes[self._get_sinks()[0]].get_individual()
        

    def partial_create(self, parallel=False, max_workers=None):
        """
        Executes a partial construction of the metaheuristic graph.

        Useful for incremental execution or debugging.

        Args:
            parallel (bool, optional): If True, executes nodes in parallel.
            max_workers (int, optional): Number of parallel workers.
        """
        self._validate_ins_and_outs()
        if not parallel:
            self._sequential_execute()
        else:
            max_workers = max_workers or cpu_count()
            self._parallel_execute(max_workers)

    def partial_iterate(
        self, individual: BaseIndividual, parallel=False, max_workers=None
    ):
        """
        Performs a partial improvement on a given individual.

        Args:
            individual (BaseIndividual): Individual to be partially modified.
            parallel (bool, optional): If True, executes nodes in parallel.
            max_workers (int, optional): Number of parallel workers.
        """
        self._create_mock_population(individual)
        if parallel:
            max_workers = max_workers or cpu_count()
        self.partial_construct(parallel, max_workers)

    def iterate(
        self, individual: BaseIndividual, parallel=False, max_workers=None
    ):
        """
        Iterates over a given individual using the metaheuristic's trajectory nodes.

        Args:
            individual (BaseIndividual): Individual to be modified.
            parallel (bool, optional): If True, executes nodes in parallel.
            max_workers (int, optional): Number of parallel workers.
        """
        if parallel:
            max_workers = max_workers or cpu_count()
        self._run_iterate(individual, parallel, max_workers)
        
        
    def _run_iterate(self, individual: BaseIndividual, parallel=False, max_workers=None):
        self._create_mock_population(individual)
        if parallel:
            max_workers = max_workers or cpu_count()
        new_individual = self._run_create(parallel, max_workers)
        individual.overwrite_with(new_individual)

    def _create_mock_population(self, individual: BaseIndividual):
        from opt_flow.metaheuristic.algorithm import Algorithm
        class MockPopulation(BasePopulation):
            def create(this) -> BaseIndividual:
                return individual.copy()

        starts = self._get_starts()
        for start_id in starts:
            tgt_node = self.nodes[start_id]
            if tgt_node.alg_type == AlgorithmType.population:
                continue
            mock_algorithm = Algorithm(
                MockPopulation(None, 0), "input", AlgorithmType.population
            )
            self.add_algorithm(mock_algorithm)
            self.connect(mock_algorithm, tgt_node)

    @staticmethod
    def _find_best(
        acceptance: BaseAcceptance, individuals: List[BaseIndividual], visited_individuals: Optional[List[BaseIndividual]] = None,
    ) -> Optional[BaseIndividual]:
        if not visited_individuals:
            visited_individuals = []
        best_individual = None
        for individual in individuals:
            if individual is None:
                continue
            if individual in visited_individuals:
                continue
            if acceptance.compare_individuals(best_individual, individual): 
                best_individual = individual
        if best_individual is None:
            for individual in individuals:
                if individual is None:
                    continue
                if acceptance.compare_individuals(best_individual, individual):
                    best_individual = individual
        return best_individual

    def connect_all(self, alg: "Algorithm"):
        """
        Connects the given algorithm node to all nodes at the maximum depth 
        in the metaheuristic graph.

        This is typically used to ensure that a new node (e.g., a final acceptance 
        node) is connected to all terminal nodes in the current execution graph.

        Args:
            alg (Algorithm): The algorithm node to connect to all deepest nodes.
    """
        depth = self._calculate_depth(self._calculate_indegree())
        max_depth_nodes = [
            self.nodes[nid]
            for nid, depth_val in depth.items()
            if depth_val == max(depth.values())
        ]
        for mhnode in max_depth_nodes:
            if mhnode == alg:
                continue
            self.connect(mhnode, alg)

    def _backtrack_best_path(self):
        sinks = self._get_sinks()
        final_node = self.nodes[sinks[0]]
        final_node._set_best()
        self._best_paths.append([final_node.id])
        self._backtrack_from_node(final_node)

    def _add_node_to_best_path(self, origin: "Algorithm", node: "Algorithm"):
        for path in self._best_paths:
            if path[-1] == origin.id:
                path.append(node.id)

    def _add_new_best_path(self, origin: "Algorithm", node: "Algorithm"):
        new_best_paths = []
        for path in self._best_paths:
            if path[-1] == origin.id:
                new_best_paths.append(path + [node.id])
                new_best_paths.append(path)
            else:
                new_best_paths.append(path)
        self._best_paths = new_best_paths

    def _remove_remaining_best_paths(self, node: "Algorithm"):
        new_best_paths = []
        for path in self._best_paths:
            if path[-1] != node.id:
                new_best_paths.append(path)
        self._best_paths = new_best_paths

    def _backtrack_from_node(self, node: "Algorithm"):
        depth = self._calculate_depth(self._calculate_indegree())
        node_individual = node.get_individual()
        last_layer = self.in_edges[node.id]
        if node.alg_type == AlgorithmType.acceptance:
            best_nodes = [
                last_node
                for last_node in last_layer
                if last_node.get_individual() == node_individual
            ]
            best_nodes_in_last_layer = [last_node for last_node in best_nodes if depth[last_node.id] == max([depth[n.id] for n in best_nodes])]
            for mh_node in best_nodes_in_last_layer:
                mh_node._set_best()
                self._add_new_best_path(node, mh_node)
                self._backtrack_from_node(mh_node)
            self._remove_remaining_best_paths(node)
        elif node.alg_type == AlgorithmType.trajectory:
            original_node = next(iter(last_layer))
            original_node._set_best()
            self._add_node_to_best_path(node, original_node)
            self._backtrack_from_node(original_node)
        elif node.alg_type == AlgorithmType.recombination:
            for mh_node in last_layer:
                mh_node._set_best()
                self._add_new_best_path(node, mh_node)
                self._backtrack_from_node(mh_node)
            self._remove_remaining_best_paths(node)

    def _get_sinks(self) -> List[str]:
        return [nid for nid, outs in self.out_edges.items() if not outs]

    def plot_algorithm_graph(
        self,
        filename: str = "metaheuristic",
        view: bool = True,
        only_best_path: bool = True,
        folder: Path | None = None,
    ):
        """
        Plots the metaheuristic algorithm graph using Graphviz and saves it
        to a run folder, creating it if necessary.

        Args:
            filename (str, optional): Output file name without extension.
            view (bool, optional): If True, opens the plot after rendering.
            only_best_path (bool, optional): If True, plots only the best solution paths.
            folder (Path | None, optional): Folder where the graph is saved.
                If None, a default run folder is created.
        """
        from graphviz import Digraph
        from pathlib import Path

        # --- Determine run folder (same logic as save_metrics) ---
        if folder is None:
            folder = Path("runs") / f"{config.start_time}_{config.name}"
        folder.mkdir(parents=True, exist_ok=True)

        # Full output path (Graphviz adds extension automatically)
        output_path = folder / filename

        dot = Digraph(comment="MH Algorithm Graph", format="png")

        # --- Global Graph Style ---
        dot.attr(
            label="Metaheuristic Algorithm Graph",
            labelloc="t",
            labeljust="c",
            fontsize="24",
            fontname="Trebuchet MS",
            rankdir="LR",
            splines="true",
            overlap="false",
            nodesep="0.6",
            ranksep="0.7",
            bgcolor="white",
        )

        # --- Default Node & Edge Style ---
        dot.attr(
            "node",
            fontname="Trebuchet MS Bold",
            fontsize="16",
            margin="0.45,0.25",
            style="filled,rounded",
            color="#2C3E50",
        )
        dot.attr("edge", fontname="Trebuchet MS", fontsize="13", color="#7F8C8D")

        # --- Colors for node types ---
        type_colors = {
            AlgorithmType.population: "#A3E4D7",
            AlgorithmType.trajectory: "#F7DC6F",
            AlgorithmType.recombination: "#F5B7B1",
            AlgorithmType.acceptance: "#D7DBDD",
        }

        # --- Add Nodes ---
        for node_id, node in self.nodes.items():
            if not node.is_best and only_best_path:
                continue

            label = node.id
            if node.get_individual() is not None: 
                obj_value = node.get_individual().get_objective()
                label += "\n" + str(obj_value)

            fillcolor = type_colors.get(node.alg_type, "#FFFFFF")

            if node.is_best:
                dot.node(
                    node_id,
                    label,
                    fillcolor=fillcolor,
                    color="#E74C3C",
                    penwidth="3",
                    fontcolor="black",
                )
            else:
                dot.node(
                    node_id,
                    label,
                    fillcolor=fillcolor,
                    color="#2C3E50",
                    penwidth="1.8",
                    fontcolor="black",
                )

        # --- Add Edges ---
        for src_id, targets in self.out_edges.items():
            for tgt_node in targets:
                is_best_edge = any(
                    src_id in path
                    and tgt_node.id in path
                    and path.index(tgt_node.id) - path.index(src_id) == -1
                    for path in self._best_paths
                )

                if is_best_edge:
                    dot.edge(src_id, tgt_node.id, color="#E74C3C", penwidth="2.5")
                elif not only_best_path:
                    dot.edge(src_id, tgt_node.id, color="#7F8C8D", penwidth="1.3")

        # --- Render into run folder ---
        dot.render(str(output_path), view=view, cleanup=True)
