# This is a diy file system only for enthusiasts
# You can create an entire file system out of it.
# Use doubly LinkedList to move forward and backward through the file system

class FileSystemNode:
    def __init__(self, name: str, path, is_dir: bool = True):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.is_file = not self.is_dir
        self.parent = None
        self.children = []
        self.content = None  # Store file content here

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def set_content(self, content: str):
        """Set content for file nodes"""
        if self.is_dir:
            raise ValueError(f"Cannot set content on directory '{self.name}'")
        self.content = content
        self.path.write(content)

    def get_content(self):
        """Get content for file nodes"""
        if self.is_dir:
            raise ValueError(f"Cannot get content from directory '{self.name}'")
        return self.content


class TempFileBuilder:
    def __init__(self, tmpdir_factory, root_dir: str = "static"):
        self._factory = tmpdir_factory
        self._root_node = FileSystemNode(
            name=root_dir,
            path=tmpdir_factory.mktemp(root_dir),
            is_dir=True
        )
        self._curr_node = self._root_node
        self._last_file_node = None  # Track last created file for convenience

    def create_child_dir(self, dir_name: str):
        new_path = self._curr_node.path.mkdir(dir_name)
        new_node = FileSystemNode(dir_name, new_path, is_dir=True)
        self._curr_node.add_child(new_node)
        self._curr_node = new_node
        return self

    def go_to_parent(self):
        if not self._curr_node.parent:
            raise ValueError("Already at root directory")
        self._curr_node = self._curr_node.parent
        return self

    def go_to_root(self):
        self._curr_node = self._root_node
        return self

    def go_to_child(self, dir_name: str):
        for child in self._curr_node.children:
            if child.is_dir and child.name == dir_name:
                self._curr_node = child
                return self
        raise ValueError(f"Child directory '{dir_name}' not found")

    def create_file(self, file_name: str):
        file_path = self._curr_node.path.join(file_name)
        file_node = FileSystemNode(file_name, file_path, is_dir=False)
        self._curr_node.add_child(file_node)
        self._last_file_node = file_node  # Track for chaining
        return self

    def set_file_content(self, content: str):
        if not self._last_file_node:
            raise ValueError("No file created to set content on")
        self._last_file_node.set_content(content)
        return self

    def get_file_node(self, file_name: str):
        """Get a specific file node from current directory"""
        for child in self._curr_node.children:
            if not child.is_dir and child.name == file_name:
                return child
        raise ValueError(f"File '{file_name}' not found in current directory")

    def find_node(self, name: str, node=None):
        """Recursively find a node by name in the tree"""
        if node is None:
            node = self._root_node

        if node.name == name:
            return node

        for child in node.children:
            result = self.find_node(name, child)
            if result:
                return result

        return None

    def get_tree_structure(self, node=None, prefix="", is_last=True):
        """Visual representation of the file tree using recursion"""
        if node is None:
            node = self._root_node

        lines = []

        # using box drawing Unicode characters for stdout
        # https://www.compart.com/en/unicode/block/U+2500
        connector = "└── " if is_last else "├── "
        node_display = node.name + ("/" if node.is_dir else "")

        # Add content indicator for files
        if not node.is_dir and node.content:
            node_display += f" ({len(node.content)} bytes)"

        lines.append(prefix + connector + node_display)

        if node.children:
            extension = "\t\t" if is_last else "│\t"
            for i, child in enumerate(node.children):
                is_last_child = (i == len(node.children) - 1)
                lines.extend(self.get_tree_structure(
                    child,
                    prefix + extension,
                    is_last_child
                ))

        return lines

    def print_tree(self):
        """Print the file system tree"""
        print("\n".join(self.get_tree_structure()))

    @property
    def root_node(self):
        return self._root_node

    @property
    def root(self):
        return self._root_node.path

    @property
    def current(self):
        return self._curr_node.path

    @property
    def current_node(self):
        return self._curr_node

    @property
    def parent(self):
        return self._curr_node.parent.path if self._curr_node.parent else None

    @property
    def parent_node(self):
        return self._curr_node.parent

    @property
    def last_file_node(self):
        """Get the last created file node"""
        return self._last_file_node
