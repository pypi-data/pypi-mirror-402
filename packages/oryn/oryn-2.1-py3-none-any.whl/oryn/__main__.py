import os
from dataclasses import KW_ONLY, dataclass, field
from pathlib import Path

from .inclusion import lookup_file_tree
from .metadata import ToolMetadata, read_metadata


ENABLE_COLOR = 'NO_COLOR' not in os.environ

@dataclass(slots=True)
class HierarchyNode:
  value: str
  _: KW_ONLY
  children: 'list[HierarchyNode]' = field(default_factory=list)
  is_target: bool

  def format(self, *, prefix: str = str()):
    if not self.is_target:
      if ENABLE_COLOR:
        value_prefix = '\033[90m'
        value_suffix = '\033[0m'
      else:
        value_prefix = ''
        value_suffix = ' (ignored)'
    else:
      value_prefix = ''
      value_suffix = ''

    return value_prefix + self.value + value_suffix + ''.join([
      '\n' + prefix
        + ('└── ' if (last := (index == (len(self.children) - 1))) else '├── ')
        + child.format(prefix=(prefix + ('    ' if last else '│   ')))
        for index, child in enumerate(self.children)
    ])


def compute_tree(root_path: Path, tool_metadata: ToolMetadata):
  node_ancestors = list[HierarchyNode]()

  for item in lookup_file_tree(
    root_path,
    ignore=tool_metadata.get('ignore', []),
    include=tool_metadata.get('include', []),
    overrides=tool_metadata.get('overrides', {}),
    use_gitignore=tool_metadata.get('use-gitignore', False),
  ):
    if item is None:
      if len(node_ancestors) > 1:
        node_ancestors.pop()
    else:
      if item.inclusion_path is not None:
        name = item.inclusion_path.name
      else:
        name = item.path.name or '.'

      if item.is_directory:
        name += '/'

      if item.inclusion_relation == 'target':
        name += ' [inclusion root]'

      node = HierarchyNode(
        is_target=((item.inclusion_relation is not None) and (not item.ignored)),
        value=name,
      )

      if node_ancestors:
        node_ancestors[-1].children.append(node)

      if item.has_children:
        node_ancestors.append(node)

  return node_ancestors[0]


if __name__ == '__main__':
  current_path = Path.cwd()

  _, tool_metadata = read_metadata(current_path)

  print('Files included in the build:')
  root_node = compute_tree(current_path, tool_metadata)
  print(root_node.format())

  # for item in lookup_file_tree(
  #   current_path,
  #   ignore=tool_metadata.get('ignore', []),
  #   include=tool_metadata.get('include', []),
  #   overrides=tool_metadata.get('overrides', {}),
  #   use_gitignore=tool_metadata.get('use-gitignore', False),
  # ):
  #   if item is not None:
  #     print(item.path)
  #     print("  ", repr(item.inclusion_path), item.inclusion_relation)
