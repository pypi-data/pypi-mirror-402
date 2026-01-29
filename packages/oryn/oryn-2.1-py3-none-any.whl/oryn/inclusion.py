from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Literal, Optional

from .matching import MatchRule, match_rules, parse_gitignore


DEFAULT_IGNORE_RULES = [
  MatchRule.parse(r) for r in [
    '__pycache__/',
    '.DS_Store',
    '.git/',
    '.gitignore',
    '.venv/',
    '*.egg-info/',
  ]
]


@dataclass(slots=True)
class Ancestor:
  ignore_rules: list[MatchRule]

@dataclass(kw_only=True, slots=True)
class Item:
  has_children: bool
  ignored: bool
  inclusion_path: Optional[PurePath]
  inclusion_relation: Literal['ancestor', 'descendant', 'target', None]
  is_directory: bool
  path: Path


def lookup_file_tree(
  root_path: Path,
  *,
  ignore: list[str],
  include: list[str],
  overrides: dict[str, str],
  use_gitignore: bool,
):
  global_ignore_rules = DEFAULT_IGNORE_RULES + [MatchRule.parse(r) for r in ignore]
  include_rules = [MatchRule.parse(r, allow_negated=False, ensure_absolute=True) for r in include]

  ancestors = list[Ancestor]()
  queue: list[Optional[tuple[str, Path]]] = [('', root_path)]

  parent_relative_path = PurePath('.')
  inclusion_path: Optional[PurePath] = None

  override_map: dict[PurePath, Path] = {
    PurePath(key): root_path / value for key, value in overrides.items()
  }

  while queue:
    queue_item = queue.pop()

    if queue_item is None:
      if inclusion_path is not None:
        if inclusion_path == PurePath('.'):
          inclusion_path = None
        else:
          inclusion_path = inclusion_path.parent

      parent_relative_path = parent_relative_path.parent
      ancestors.pop()

      yield None
      continue

    # overriden_path = overrides.get(relative_path)
    # path = (root_path / (overriden_path if overriden_path is not None else relative_path)).resolve()

    name, path = queue_item

    if path == root_path:
      test_path = PurePath('/')
    else:
      test_path = PurePath('/') / parent_relative_path / name

    if path.is_dir():
      is_directory = True
    elif path.is_file():
      is_directory = False
    else:
      raise FileNotFoundError(f'Invalid path: {path}')

    if path == root_path:
      inclusion_relation = 'ancestor'
    elif inclusion_path is not None:
      inclusion_relation = 'descendant'
    else:
      inclusion_relation = match_rules(
        test_path,
        include_rules,
        directory=is_directory,
      )

    if inclusion_relation == 'target':
      inclusion_path = PurePath('.')

    if inclusion_path is not None:
      inclusion_path = inclusion_path / name

    if inclusion_relation in ('descendant', 'target'):
      ignored = match_rules(test_path, global_ignore_rules, directory=is_directory) == 'target'

      if not ignored:
        for ancestor_index, ancestor in enumerate(ancestors, start=1):
          if match_rules(
            PurePath('/') / PurePath(*test_path.parts[ancestor_index:]),
            ancestor.ignore_rules,
            directory=is_directory,
          ) == 'target':
            ignored = True
            break
    else:
      ignored = False

    has_children = is_directory and (inclusion_relation is not None) and (not ignored)

    yield Item(
      has_children=has_children,
      ignored=ignored,
      inclusion_path=inclusion_path,
      inclusion_relation=inclusion_relation,
      is_directory=is_directory,
      path=path,
    )

    if has_children:
      if use_gitignore:
        gitignore_path = path / '.gitignore'

        if gitignore_path.exists():
          with gitignore_path.open() as file:
            ignore_rules = parse_gitignore(file)
        else:
          ignore_rules = []
      else:
        ignore_rules = []

      ancestors.append(
        Ancestor(ignore_rules),
      )

      if path != root_path:
        parent_relative_path /= name

      children = {
        child_path.name: child_path for child_path in path.iterdir()
      } | {
        override_source.name: override_dest for override_source, override_dest in override_map.items() if override_source.parent == parent_relative_path
      }

      queue.append(None)

      for child_name, child_path in reversed(sorted(children.items(), key=(lambda child: (child[1].is_dir(), child[1].name)))):
        queue.append((child_name, child_path))
    else:
      if inclusion_path is not None:
        if inclusion_relation == 'target':
          inclusion_path = None
        else:
          inclusion_path = inclusion_path.parent
