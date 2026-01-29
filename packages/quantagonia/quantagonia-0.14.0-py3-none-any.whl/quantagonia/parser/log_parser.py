"""Class to parse solver log."""

from __future__ import annotations

import re


def get_regex_result(regex_string: str, search_string: str, group_name: str | None = None) -> str | None:
    m = re.compile(regex_string).search(search_string)
    if m is not None:
        return m.group(group_name) if group_name is not None else m.group()
    return None


class SolverLogParser:
    """Class for parsing the solver log."""

    def __init__(self, log: str):
        self.log = log
        self._base_regex = r"(?<=(Solver\sResults))[-\s\S]+"

    def get_solver_version(self) -> str:
        """Get the version number of the solver image."""
        regex = r"(?<=(Quantagonia\sHybridSolver\sversion))\s(?P<version>.*)"
        return str(get_regex_result(regex, self.log, "version")).strip()

    def get_sol_status(self) -> str:
        regex = self._base_regex + r"Solution\sStatus[:\s](?P<solution_status>[A-z\s]+)(\r\n?|\n)"
        return str(get_regex_result(regex, self.log, "solution_status")).strip()

    def get_timing(self) -> float:
        regex = self._base_regex + r"Wall\sTime[:\s](?P<wall_time>.*)\sseconds"
        timing = str(get_regex_result(regex, self.log, "wall_time")).strip()
        if (timing is None) or (timing == "None"):
            return float("nan")
        return float(timing)

    def get_objective(self) -> float:
        regex = self._base_regex + r"Objective[:\s]+(?P<objective>.*)"
        objective = str(get_regex_result(regex, self.log, "objective")).strip()
        if (objective is None) or (objective == "None"):
            return float("nan")
        return float(objective)

    def get_bound(self) -> float:
        regex = self._base_regex + r"Bound[:\s]+(?P<bound>.*)"
        bound = str(get_regex_result(regex, self.log, "bound")).strip()
        if (bound is None) or (bound == "None"):
            return float("nan")
        return float(bound)

    def get_absolute_gap(self) -> float:
        regex = self._base_regex + r"Absolute\sGap[:\s]+(?P<absolute_gap>.*)"
        absolute_gap = str(get_regex_result(regex, self.log, "absolute_gap")).strip()
        absolute_gap = absolute_gap.split()[0]
        if (absolute_gap is None) or (absolute_gap == "None"):
            return float("nan")
        return float(absolute_gap)

    def get_relative_gap(self) -> float:
        regex = self._base_regex + r"Relative\sGap[:\s]+(?P<relative_gap>\d+\.\d+)"
        relative_gap = str(get_regex_result(regex, self.log, "relative_gap")).strip()
        if (relative_gap is None) or (relative_gap == "None"):
            return float("nan")
        return float(relative_gap)

    def get_nodes(self) -> int | float:
        regex = self._base_regex + r"Nodes[:\s]+[\s]+(?P<nodes>(.)*)"
        nodes = str(get_regex_result(regex, self.log, "nodes")).strip()
        if (nodes is None) or (nodes == "None"):
            return float("nan")
        return int(nodes)

    def get_iterations(self) -> int | float:
        """Get LP iterations."""
        regex = self._base_regex + r"(LP|Simplex|IPM)\sIterations[:\s]+(?P<iterations>.*)"
        iterations = str(get_regex_result(regex, self.log, "iterations")).strip()
        if (iterations is None) or (iterations == "None"):
            return float("nan")
        return int(iterations)

    def get_best_node(self) -> int | float:
        """Get the node count of the best solution."""
        regex = self._base_regex + r"Best\sSolution[:\s]+after\s(?P<best_time>.*) seconds and (?P<best_node>.*) nodes"
        best_node = str(get_regex_result(regex, self.log, "best_node")).strip()
        if (best_node is None) or (best_node == "None"):
            return float("nan")
        return int(best_node)

    def get_best_time(self) -> float:
        """Get the timing of the best solution."""
        regex = self._base_regex + r"Best\sSolution[:\s]+after\s(?P<best_time>.*) seconds and (?P<best_node>.*) nodes"
        best_time = str(get_regex_result(regex, self.log, "best_time")).strip()
        if (best_time is None) or (best_time == "None"):
            return float("nan")
        return float(best_time)

    def get_nodes_over_time(self) -> list:
        """Get the number of open and closed nodes over time."""
        nodes_over_time = []
        log = self.log.split("\n")
        in_table = False
        nodes_pos = -1
        for orig_line in log:
            line = [s.strip() for s in orig_line.split("|") if s.strip() != ""]
            if len(line) <= 1:
                continue
            if line[-1] == "Time (s)":
                nodes_pos = line.index("Incumbent")
                in_table = True
            elif in_table and line[-1] != "Time (s)" and "-------" not in line[0]:  # skip line separator
                nodes = float(line[nodes_pos])
                nodes_over_time.append(nodes)

        return nodes_over_time

    def get_incumbents_over_time(self) -> list:
        """Get the incumbents over time."""
        incumbents_over_time = set()
        log = self.log.split("\n")
        in_table = False
        incumbents_pos = -1
        for orig_line in log:
            line = [s.strip() for s in orig_line.split("|") if s.strip() != ""]
            if len(line) <= 1:
                continue
            if line[-1] == "Time (s)":
                incumbents_pos = line.index("Incumbent")
                in_table = True
            elif in_table and line[-1] != "Time (s)" and "-------" not in line[0]:  # skip line separator
                incumbent = float(line[incumbents_pos])
                incumbents_over_time.add(incumbent)

        return incumbents_over_time

    def get_number_of_quantum_solutions(self) -> int:
        """Get the number of quantum solutions."""
        regex = r"(?<=(Solver\sResults))[\s\S]*\s-\sNumber\sof\sgenerated\squantum\ssolutions:\s(?P<sols>.*)"
        solutions = str(get_regex_result(regex, self.log, "sols")).strip()
        if (solutions is None) or (solutions == "None"):
            return float("nan")
        return int(solutions)

    def get_solver_summary(self) -> dict:
        data = {}
        data["solver_version"] = self.get_solver_version()
        data["sol_status"] = self.get_sol_status()
        data["timing"] = self.get_timing()
        data["objective"] = self.get_objective()
        data["bound"] = self.get_bound()
        data["absolute_gap"] = self.get_absolute_gap()
        data["relative_gap"] = self.get_relative_gap()
        data["iterations"] = self.get_iterations()
        data["nodes"] = self.get_nodes()
        data["best_node"] = self.get_best_node()
        data["best_time"] = self.get_best_time()
        data["num_quantum_solutions"] = self.get_number_of_quantum_solutions()

        return data
