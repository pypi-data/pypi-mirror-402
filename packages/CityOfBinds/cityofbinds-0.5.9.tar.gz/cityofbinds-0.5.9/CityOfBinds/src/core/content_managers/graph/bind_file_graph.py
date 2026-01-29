import copy
import random

import networkx as nx

from .....utils.types.str_path import StrPath
from ...._configs.constants import BFGConstants
from ...game_content.bind_file.bind_file import BindFile


class BindFileGraph(nx.DiGraph):
    """
    A wrapper around NetworkX DiGraph for managing logical connections between BindFile objects.

    This class enables the creation of complex rotating bind patterns by establishing directed
    relationships between bind files with optional trigger conditions and delays.

    Terminology:
        - Link: A directed connection from a source bind file to a target bind file
        - Trigger Conditions: Optional metadata describing when/how bind files are connected
        - Node Index: Integer identifier for each bind file in the graph (auto-assigned)
        - Edge: The connection between two bind files with optional trigger conditions

    Common Patterns:
        - Chain: bf1 -> bf2 -> bf3 (linear sequence)
        - Loop: bf1 -> bf2 -> bf3 -> bf1 (circular sequence)
        - K-Regular: Each bind file connects to k other bind files
    """

    def add_bind_file(
        self, bind_file: BindFile, file_path_override: str = None
    ) -> "BindFileGraph":
        """
        Add BindFile as a new node in the graph.

        Args:
            bind_file: The BindFile to add to the graph

        Returns:
            Self for method chaining

        Example:
            >>> graph = BindFileGraph()
            >>> bf1 = BindFile([Bind("F1", ["say hello"])])
            >>> graph.add_bind_file(bf1)  # Node 0
            >>> len(graph.nodes)  # 1
        """

        super().add_node(
            self.number_of_nodes(),
            **{
                BFGConstants.NODE_DATA_KEY: bind_file,
                BFGConstants.FILE_PATH_OVERRIDE_KEY: file_path_override,
            },
        )
        return self

    def connect(
        self,
        source_bind_file_index: int,
        target_bind_file_index: int,
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Create a directed link from source to target bind file.

        Args:
            source_bind_file_index: Index of the source bind file
            target_bind_file_index: Index of the target bind file
            load_conditions: Optional conditions for what triggers this link
            delay: Number of copies of source node and intermediate links to insert as delay

        Returns:
            Self for method chaining

        Example:
            >>> graph.link(0, 1)  # bf0 -> bf1
            >>> graph.link(0, 2, {"on_triggers": "SPACE"})  # bf0 -> bf2 (on SPACE press only)
            >>> graph.link(1, 2, delay=2)  # bf1 -> copy(bf1) -> copy(bf1) -> bf2
        """
        # Add the edge with trigger conditions as metadata
        super().add_edge(
            source_bind_file_index,
            target_bind_file_index,
            **{BFGConstants.EDGE_DATA_KEY: load_conditions},
        )
        # Insert delay nodes if requested
        if delay > 0:
            self.add_delay(source_bind_file_index, target_bind_file_index, delay)
        return self

    def path(
        self,
        bind_file_indexes: list[int],
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Create a linear chain of bind files in sequence.

        Args:
            bind_file_indexes: List of node indexes to chain in list order
            load_conditions: Conditions applied to all links in the chain
            delay: Delay applied to all links in the chain

        Returns:
            Self for method chaining

        Example:
            >>> graph.chain([0, 1, 2])  # Creates: bf0 -> bf1 -> bf2
            >>> graph.chain([4, 3, 5], {"on_triggers": "F1"})  # bf4 -> bf3 -> bf5 (all on F1)
        """
        # Link each consecutive pair in the sequence
        for i in bind_file_indexes[:-1]:
            self.connect(i, i + 1, load_conditions=load_conditions, delay=delay)
        return self

    def path_random(
        self,
        bind_file_indexes: list[int],
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Create a linear chain of bind files in random order.

        Args:
            bind_file_indexes: List of node indexes to chain in random order
            load_conditions: Conditions applied to all links in the chain
            delay: Delay applied to all links in the chain

        Returns:
            Self for method chaining
        """
        randomized_indexes = random.sample(bind_file_indexes, len(bind_file_indexes))
        return self.path(
            randomized_indexes,
            load_conditions=load_conditions,
            delay=delay,
        )

    def path_with_return(
        self,
        bind_file_indexes: list[int],
        return_conditions: dict = None,
        return_delay: int = 0,
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Paths bind_file_indexes in sequence, and adds a reset condition to connect every node to the beginning of the path.

        Args:
            bind_file_indexes: List of node indexes to reset in the chain
            reset_conditions: Conditions applied to all reset links in the chain
            load_conditions: Conditions applied to all links in the chain
            delay: Delay applied to all links in the chain

        Returns:
            Self for method chaining
        """
        # Remove existing links
        self.path(bind_file_indexes, load_conditions=load_conditions, delay=delay)
        for i in bind_file_indexes:
            self.connect(
                i,
                bind_file_indexes[0],
                load_conditions=return_conditions,
                delay=return_delay,
            )
        return self

    def cycle(
        self,
        bind_file_indexes: list[int],
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Create a circular loop connecting bind files in list order, with last linking back to first.

        Args:
            bind_file_indexes: List of node indexes to connect in a loop
            load_conditions: Conditions applied to all links in the loop
            delay: Delay applied to all links in the loop

        Returns:
            Self for method chaining

        Example:
            >>> graph.loop([0, 1, 2])  # Creates: bf0 -> bf1 -> bf2 -> bf0 (circular)
            >>> graph.loop([6, 4, 5, 3])  # bf6 -> bf4 -> bf5 -> bf3 -> bf6 (circular)
        """
        # Handle empty list case
        if not bind_file_indexes:
            return self

        # Create the chain first
        self.path(bind_file_indexes, load_conditions=load_conditions, delay=delay)
        # Connect the last back to the first to complete the loop
        self.connect(
            bind_file_indexes[-1],
            bind_file_indexes[0],
            load_conditions=load_conditions,
            delay=delay,
        )
        return self

    def cycle_random(
        self,
        bind_file_indexes: list[int],
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Create a circular loop connecting bind files in random order, with last linking back to first.

        Args:
            bind_file_indexes: List of node indexes to connect in a random loop
            load_conditions: Conditions applied to all links in the loop
            delay: Delay applied to all links in the loop

        Returns:
            Self for method chaining
        """
        randomized_indexes = random.sample(bind_file_indexes, len(bind_file_indexes))
        return self.cycle(
            randomized_indexes,
            load_conditions=load_conditions,
            delay=delay,
        )

    def make_k_regular(
        self,
        bind_file_indexes: list[int],
        k: int,
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Create a k-regular graph where each bind file connects to exactly k other bind files.

        In a k-regular graph, every node has exactly k outgoing edges. Connections are made
        to the next k nodes in circular/list order.

        Args:
            bind_file_indexes: List of node indexes to make k-regular
            k: Number of outgoing connections each node should have
            load_conditions: Conditions applied to all links
            delay: Delay applied to all links

        Returns:
            Self for method chaining

        Raises:
            ValueError: If k >= number of bind files (impossible to create without self links)

        Example:
            >>> graph.make_k_regular([0, 1, 2, 3], k=2)
            # Creates: bf0 -> bf1, bf2
            #          bf1 -> bf2, bf3
            #          bf2 -> bf3, bf0
            #          bf3 -> bf0, bf1
        """
        if k >= len(bind_file_indexes):
            raise ValueError(
                "k must be less than the number of bind files to create a k-regular graph."
            )

        n = len(bind_file_indexes)
        # For each node, connect to the next k nodes in circular order
        for i in range(n):
            for j in range(1, k + 1):
                target_index = (i + j) % n  # Wrap around using modulo
                self.connect(
                    bind_file_indexes[i],
                    bind_file_indexes[target_index],
                    load_conditions=load_conditions,
                    delay=delay,
                )
        return self

    def make_k_random(
        self,
        bind_file_indexes: list[int],
        k: int,
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Create a strongly connected k-random graph where each node has exactly k outgoing edges.

        Creates a k-regular graph with randomized connections by shuffling node order
        then applying the k-regular pattern. This ensures strong connectivity, exact
        k-regularity (k in, k out), and even distribution of edges.

        Args:
            bind_file_indexes: List of node indexes to make k-random
            k: Number of outgoing connections each node should have
            load_conditions: Conditions applied to all links
            delay: Delay applied to all links

        Returns:
            Self for method chaining

        Raises:
            ValueError: If k >= number of bind files (impossible without self-loops)

        Example:
            >>> graph.make_k_random([0, 1, 2, 3], k=2)
            # Randomizes order, then creates k-regular pattern
            # Result: strongly connected, k in/out for each node
        """
        # Randomize order, then use k-regular pattern for guaranteed properties
        randomized = random.sample(bind_file_indexes, len(bind_file_indexes))
        return self.make_k_regular(randomized, k, load_conditions, delay)

    def weave(
        self,
        bind_file_index_lists: list[list[int]],
        cycle: bool = False,
        load_conditions: dict = None,
        delay: int = 0,
    ) -> "BindFileGraph":
        """
        Create interleaved paths from multiple lists of bind file indexes.

        Shorter lists are extended by adding new nodes (copies of their bind files,
        cycling through the original list) until all lists match the longest length.
        This avoids multiple incoming edges to the same node.

        Args:
            bind_file_index_lists: List of lists of node indexes to interleave
            load_conditions: Conditions applied to all links
            delay: Delay applied to all links
        Returns:
            Self for method chaining
        Example:
            >>> graph.weave([[0,1,2], [3,4,5]])
            # Creates: bf0 -> bf3 -> bf1 -> bf4 -> bf2 -> bf5
            >>> graph.weave([[0,1,2,3,4], [5,6]])
            # Extends [5,6] with new nodes 7,8,9 (copies of bf5,bf6,bf5)
            # Creates: bf0 -> bf5 -> bf1 -> bf6 -> bf2 -> bf7 -> bf3 -> bf8 -> bf4 -> bf9
        """
        max_len = max(len(lst) for lst in bind_file_index_lists)

        # Extend shorter lists by adding new nodes with copies of their bind files
        extended_lists = []
        for lst in bind_file_index_lists:
            extended = list(lst)
            for i in range(len(lst), max_len):
                original_index = lst[i % len(lst)]
                original_bind_file = self.get_bind_file(original_index)
                new_index = self.number_of_nodes()
                self.add_bind_file(copy.deepcopy(original_bind_file))
                extended.append(new_index)
            extended_lists.append(extended)

        # Interleave the now-equal-length lists
        interleaved = []
        for i in range(max_len):
            for lst in extended_lists:
                interleaved.append(lst[i])

        if cycle:
            return self.cycle(interleaved, load_conditions=load_conditions, delay=delay)
        return self.path(interleaved, load_conditions=load_conditions, delay=delay)

    def _subdivide_edge(
        self,
        source_bind_file_index: int,
        target_bind_file_index: int,
        new_bind_file: BindFile,
        first_condition=None,
        second_condition=None,
    ) -> "BindFileGraph":
        """
        Internal method to subdivide an existing edge by inserting a new node.

        Removes the direct edge between source and target, then creates:
        source -> new_node -> target

        Args:
            source_bind_file_index: Starting node
            target_bind_file_index: Ending node
            new_bind_file: BindFile to insert as intermediate node
            first_condition: Trigger conditions for source -> new_node
            second_condition: Trigger conditions for new_node -> target

        Returns:
            Self for method chaining

        Raises:
            ValueError: If no edge exists between source and target
        """
        # Remove the existing direct edge
        try:
            self.remove_edge(source_bind_file_index, target_bind_file_index)
        except nx.NetworkXError as e:
            raise ValueError(
                f"No link to subdivide between bind file '{self.get_bind_file(source_bind_file_index)}' and bind file '{self.get_bind_file(target_bind_file_index)}'."
            ) from e

        # Add the new intermediate node
        new_bind_file_index = self.number_of_nodes()
        self.add_bind_file(new_bind_file)

        # Create the two new edges: source -> new -> target
        super().add_edge(
            source_bind_file_index,
            new_bind_file_index,
            **({BFGConstants.EDGE_DATA_KEY: first_condition}),
        )
        super().add_edge(
            new_bind_file_index,
            target_bind_file_index,
            **({BFGConstants.EDGE_DATA_KEY: second_condition}),
        )

        return self

    def add_delay(
        self, source_bind_file_index: int, target_bind_file_index: int, steps: int = 1
    ) -> "BindFileGraph":
        """
        Insert copies of source node between two connected nodes. Maintains trigger conditions.

        This method subdivides an existing edge by inserting intermediate nodes,
        effectively creating a delay in the bind file sequence.

        Args:
            source_bind_file_index: Starting node index
            target_bind_file_index: Ending node index
            steps: Number of delay nodes to insert

        Returns:
            Self for method chaining

        Example:
            >>> graph.link(0, 1)  # bf0 -> bf1
            >>> graph.add_delay(0, 1, 2)  # bf0 -> copy(bf0) -> copy(bf0) -> bf1
        """
        # Preserve the original connection conditions
        original_load_conditions = self.get_load_conditions(
            source_bind_file_index, target_bind_file_index
        )
        original_bind_file = self.get_bind_file(source_bind_file_index)

        # Insert the specified number of delay nodes
        for _ in range(steps):
            new_delay_bind_file_index = self.number_of_nodes()
            self._subdivide_edge(
                source_bind_file_index,
                target_bind_file_index,
                copy.deepcopy(original_bind_file),
                first_condition=original_load_conditions,
                second_condition=original_load_conditions,
            )
            # Update source for next iteration (chaining delays)
            source_bind_file_index = new_delay_bind_file_index

        return self

    def get_load_conditions(
        self, source_bind_file_index: int, target_bind_file_index: int
    ) -> dict:
        """Get the trigger conditions for a specific edge.

        Args:
            source_bind_file_index: Source node index
            target_bind_file_index: Target node index

        Returns:
            Dictionary of trigger conditions, empty dict if none set
        """
        return (
            self.get_edge_data(source_bind_file_index, target_bind_file_index)[
                BFGConstants.EDGE_DATA_KEY
            ]
            or {}
        )

    def get_outgoing_connections(self, bind_file_index: int) -> list[int]:
        """Get all node indexes that this bind file links to.

        Args:
            bind_file_index: Node index to get outgoing connections for
        Returns:
            List of target node indexes
        """
        return list(self.successors(bind_file_index))

    def get_incoming_connections(self, bind_file_index: int) -> list[int]:
        """Get all node indexes that link to this bind file.

        Args:
            bind_file_index: Node index to get incoming connections for
        Returns:
            List of source node indexes
        """
        return list(self.predecessors(bind_file_index))

    def get_bind_file(self, bind_file_index: int) -> BindFile:
        """Retrieve the BindFile object stored at a specific node.

        Args:
            bind_file_index: Node index to retrieve BindFile from

        Returns:
            BindFile object stored at the specified node
        """
        return self.nodes[bind_file_index][BFGConstants.NODE_DATA_KEY]

    def extend(
        self, other_graph: "BindFileGraph", merge_on: list[tuple[int, int]] = None
    ) -> "BindFileGraph":
        """
        Extend this graph with nodes and edges from another graph.

        All nodes from other_graph are added with updated indexes (offset by current node count).
        Edges are preserved with updated node references. Optionally merge specific nodes.

        Args:
            other_graph: The BindFileGraph to merge into this one
            merge_on: List of (self_node_index, other_node_index) tuples specifying nodes to merge.
                     For merged nodes, self's BindFile is kept but all edges are combined.

        Returns:
            Self for method chaining

        Example:
            >>> bfg1 = BindFileGraph()
            >>> bfg1.add_bind_file(bf1).add_bind_file(bf2)  # nodes 0, 1
            >>> bfg2 = BindFileGraph()
            >>> bfg2.add_bind_file(bf3).add_bind_file(bf4)  # nodes 0, 1
            >>> bfg2.link(0, 1)
            >>>
            >>> # Extend without merging: bfg1 gets nodes 0,1,2,3 with edge 2->3
            >>> bfg1.extend(bfg2)
            >>>
            >>> # Extend with merging: node 1 from bfg1 merges with node 0 from bfg2
            >>> bfg1.extend(bfg2, merge_on=[(1, 0)])
        """
        if merge_on is None:
            merge_on = []

        # Create mapping for node ID translation
        # Format: {other_graph_node_id: self_graph_node_id}
        node_id_mapping = {}
        merge_dict = {
            other_node: self_node for self_node, other_node in merge_on
        }  # Swap tuple elements

        # Step 1: Add nodes and build ID mapping
        for node_id in other_graph.nodes():
            if node_id in merge_dict:
                # This node should be merged - map to existing node in self
                node_id_mapping[node_id] = merge_dict[node_id]
            else:
                # Add as new node - add_bind_file assigns ID based on current node count
                other_bind_file = other_graph.get_bind_file(node_id)
                actual_new_node_id = (
                    self.number_of_nodes()
                )  # This will be the assigned ID
                self.add_bind_file(other_bind_file)
                node_id_mapping[node_id] = actual_new_node_id

        # Step 2: Add edges with translated node IDs
        for source, target, edge_data in other_graph.edges(data=True):
            mapped_source = node_id_mapping[source]
            mapped_target = node_id_mapping[target]

            # Add edge with preserved edge data
            load_conditions = edge_data.get(BFGConstants.EDGE_DATA_KEY)
            self.add_edge(
                mapped_source,
                mapped_target,
                **(
                    {BFGConstants.EDGE_DATA_KEY: load_conditions}
                    if load_conditions
                    else {}
                ),
            )

        return self

    def add_backup_side_effect(
        self, node_index: int, backup_target: int | StrPath
    ) -> "BindFileGraph":
        """
        Add a side-effect to a bind file node that creates a backup of all binds when bind file is loaded.

        Args:
            node_index: Index of the bind file node to add the side-effect to
            backup_target: Path or index of the bind file to back up to

        Returns:
            Self for method chaining
        """
        return self._add_side_efftect(
            node_index,
            BFGConstants.BACKUP_SIDE_EFFECT_COMMAND,
            backup_target,
        )

    def add_restore_side_effect(
        self, node_index: int, restore_source: int | StrPath
    ) -> "BindFileGraph":
        """
        Add a side-effect to a bind file node that restores binds from a backup when bind file is loaded.

        Args:
            node_index: Index of the bind file node to add the side-effect to
            restore_source: Path or index of the bind file to restore from

        Returns:
            Self for method chaining
        """
        return self._add_side_efftect(
            node_index,
            BFGConstants.RESTORE_SIDE_EFFECT_COMMAND,
            restore_source,
        )

    def _add_side_efftect(self, node_index: int, file_command: str, target: StrPath):
        """Internal method to add a generic side-effect command to a bind file node."""
        if BFGConstants.SIDE_EFFECTS_KEY not in self.nodes[node_index]:
            self.nodes[node_index][BFGConstants.SIDE_EFFECTS_KEY] = []
        self.nodes[node_index][BFGConstants.SIDE_EFFECTS_KEY].append(
            (file_command, target)
        )
        return self
