import traceback


class PipelineVisualizer:
    """
    A helper class to visualize directed graphs (pipelines) in CLI,
    including loops.

    Edge format:
        dict[str, list[tuple[str, str]]]
        FromNode -> [(condition, ToNode), ...]
    """

    @staticmethod
    def _targets(edges: dict[str, list[tuple[str, str]]], node: str) -> list[str]:
        """
        Extract target nodes, ignoring conditions.
        """
        return [to_node for _, to_node in edges.get(node, [])]

    @staticmethod
    def visualize(
        edges: dict[str, list[tuple[str, str]]],
        start_node: str
    ) -> None:
        """
        Visualize a directed graph in CLI, including loops.
        """
        try:
            main_path, visited, loop_edges = PipelineVisualizer._walk_main_path(edges, start_node)
            side_branches = PipelineVisualizer._find_side_branches(edges, main_path)
            main_line = PipelineVisualizer._render_main_line(main_path)
            print(main_line)
            PipelineVisualizer._print_side_branches(edges, side_branches, main_line, visited)
            PipelineVisualizer._print_main_loops(loop_edges, main_line)
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            print("Unable to visualize the pipeline due to unexpected error")



    @staticmethod
    def _render_branch_with_loops(
        start: str,
        edges: dict[str, list[tuple[str, str]]],
        global_visited: set,
    ) -> tuple[str, list[str]]:
        """
        Render a branch and explicitly mark loops.
        """

        path = []
        stack = []
        loops = []

        current = start

        while current:
            if current in stack:
                loops.append(current)
                break

            if current in global_visited:
                loops.append(current)
                break

            stack.append(current)
            path.append(current)

            next_nodes = PipelineVisualizer._targets(edges, current)
            current = next_nodes[0] if next_nodes else None

        return " -> ".join(path), loops

    @staticmethod
    def _walk_main_path(
        edges: dict[str, list[tuple[str, str]]],
        start_node: str,
    ) -> tuple[list[str], set[str], list[tuple[str, str]]]:
        """
        Follow the first outgoing edge from the start to build the main path.
        Detect a single loop edge if encountered.
        Returns (main_path, visited, loop_edges).
        """

        visited: set[str] = set()
        stack: list[str] = []
        main_path: list[str] = []
        loop_edges: list[tuple[str, str]] = []

        current = start_node

        while current:
            if current in stack:
                loop_edges.append((stack[-1], current))
                break

            if current in visited:
                break

            visited.add(current)
            stack.append(current)
            main_path.append(current)

            next_nodes = PipelineVisualizer._targets(edges, current)
            current = next_nodes[0] if next_nodes else None

        return main_path, visited, loop_edges

    @staticmethod
    def _find_side_branches(
        edges: dict[str, list[tuple[str, str]]],
        main_path: list[str],
    ) -> dict[str, list[str]]:
        """
        For each node in main path, collect additional children beyond the first.
        """
        side_branches: dict[str, list[str]] = {}
        for node in main_path:
            children = PipelineVisualizer._targets(edges, node)
            if len(children) > 1:
                side_branches[node] = children[1:]
        return side_branches

    @staticmethod
    def _render_main_line(main_path: list[str]) -> str:
        """
        Render the main path as a single CLI line.
        """
        return " -> ".join(main_path)

    @staticmethod
    def _print_side_branches(
        edges: dict[str, list[tuple[str, str]]],
        side_branches: dict[str, list[str]],
        main_line: str,
        visited: set[str],
    ) -> None:
        """
        Print side branches and their loop annotations.
        """
        for node, branches in side_branches.items():
            base_offset = main_line.index(node) + len(node)
            indent = " " * base_offset

            for branch in branches:
                print(f"{indent} |")
                branch_line, branch_loops = PipelineVisualizer._render_branch_with_loops(
                    branch, edges, visited
                )
                print(f"{indent} ----> {branch_line}")

                for loop in branch_loops:
                    print(f"{indent}        ↺ loop to {loop}")

    @staticmethod
    def _print_main_loops(
        loop_edges: list[tuple[str, str]],
        main_line: str,
    ) -> None:
        """
        Print loop edges detected on the main path.
        """
        for src, target in loop_edges:
            offset = main_line.index(src) + len(src)
            indent = " " * offset
            print(f"{indent} ↺ loop to {target}")



def main() -> None:
    test_cases = [
        (
            "Test 1: Simple linear pipeline",
            {
                "Start": [("c1", "A")],
                "A": [("c2", "B")],
                "B": [("c3", "C")],
                "C": [],
            },
            "Start",
        ),
        (
            "Test 2: Conditional branching without loops",
            {
                "Start": [("c1", "A")],
                "A": [("c2", "B"), ("c3", "X")],
                "B": [("c4", "C")],
                "C": [],
                "X": [("c5", "Y")],
                "Y": [],
            },
            "Start",
        ),
        (
            "Test 3: Loop on the main path",
            {
                "Start": [("c1", "A")],
                "A": [("c2", "B")],
                "B": [("c3", "C")],
                "C": [("c4", "A")],
            },
            "Start",
        ),
        (
            "Test 4: Loop inside a side branch",
            {
                "Start": [("c1", "A")],
                "A": [("c2", "B"), ("c3", "X")],
                "B": [],
                "X": [("c4", "Y")],
                "Y": [("c5", "X")],
            },
            "Start",
        ),
        (
            "Test 5: Cross-loop from branch back to main path",
            {
                "Start": [("c1", "A")],
                "A": [("c2", "B"), ("c3", "X")],
                "B": [("c4", "C")],
                "C": [],
                "X": [("c5", "A")],
            },
            "Start",
        ),
    ]

    for title, edges, start_node in test_cases:
        print("\n" + "=" * len(title))
        print(title)
        print("=" * len(title))
        PipelineVisualizer.visualize(edges, start_node)


if __name__ == "__main__":
    main()
