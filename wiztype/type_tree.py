from memobj import WindowsProcess

from .memory import HashNode

HASH_CALL_PATTERN = rb"\xE8....\x48\x3B\x18\x74\x12"


def _get_root_node(process: WindowsProcess) -> HashNode:
    # assume it's the first one, need module filtering
    hash_call_addr = process.scan_memory(HASH_CALL_PATTERN)[0]

    # E8 [B2 43 00 00]
    call_offset = process.read_formatted(hash_call_addr + 1, "i")

    # 5 is the length of the call instruction
    call_addr = hash_call_addr + call_offset + 5

    # 48 8B 05 [BF 0A F7 01]
    hash_tree_offset = process.read_formatted(call_addr + 53, "i")

    # 50 is start of the lea instruction and 7 is the length of it
    hash_tree_addr = call_addr + 50 + hash_tree_offset + 7

    pointer = process.read_formatted(hash_tree_addr, "Q")
    address = process.read_formatted(pointer, "Q")

    return HashNode(address=address, process=process)


def _get_children_nodes(node: HashNode, nodes: set):
    nodes.add(node)

    if node.is_leaf is False:
        if left_node := node.left:
            if left_node not in nodes:
                _get_children_nodes(left_node, nodes)
        if right_node := node.right:
            if right_node not in nodes:
                _get_children_nodes(right_node, nodes)

    return nodes


def _read_all_nodes(root_node: HashNode):
    nodes = set()

    first_node = root_node.parent
    return _get_children_nodes(first_node, nodes)


def get_hash_nodes(process: WindowsProcess) -> set[HashNode]:
    root_node = _get_root_node(process)
    return _read_all_nodes(root_node)


def get_type_tree() -> dict[str, HashNode]:
    process = WindowsProcess.from_name("WizardGraphicalClient.exe")

    nodes = get_hash_nodes(process)

    hash_map = {}

    for node in nodes:
        if node.is_leaf:
            continue

        hash_map[node.node_data.name] = node

    return hash_map
