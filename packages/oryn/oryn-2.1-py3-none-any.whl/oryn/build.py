import csv
import re
import shutil
import stat
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Optional
from zipfile import ZipFile, ZipInfo

from packaging.licenses import canonicalize_license_expression
from packaging.tags import Tag, sys_tags
from packaging.version import InvalidVersion, Version

from .inclusion import Item, lookup_file_tree
from .metadata import read_metadata


# See: https://packaging.python.org/en/latest/specifications/name-normalization/#name-normalization
def is_name_valid(unnormalized_name: str, /):
  return re.match(r'^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$', unnormalized_name, re.IGNORECASE) is not None

def normalize_name(name: str, /):
  return re.sub(r'[-_.]+', '-', name).lower()

def normalize_path(path: Path, /):
  part_index = 0
  new_parts = list[str]()

  while part_index < len(path.parts):
    match path.parts[part_index]:
      case '.':
        pass
      case '..':
        if new_parts:
          new_parts.pop()
      case part:
        new_parts.append(part)

    part_index += 1

  return Path(*new_parts)

def process_person_list(person_list: list[str | dict], /):
  names = list[str]()
  emails = list[str]()

  for person in person_list:
    if isinstance(person, str):
      names.append(person)
    elif isinstance(person, dict):
      name = person.get('name', '')
      email = person.get('email', '')

      if email and name:
        emails.append(f'{name} <{email}>')
      elif email:
        emails.append(email)
      elif name:
        names.append(name)

  return names, emails


def write_wheel(wheel_directory: str, /, *, editable: bool = False, distribution_names: Optional[str]):
  # Load metadata

  root_path = Path.cwd()

  metadata, tool_metadata = read_metadata(root_path)
  project_metadata = metadata.get('project', {})


  # Normalize name

  unnormalized_name = project_metadata['name']

  if not is_name_valid(unnormalized_name):
    raise ValueError(f'Invalid project name: {unnormalized_name}')

  project_name = normalize_name(unnormalized_name)


  # Normalize version

  raw_version = project_metadata['version']

  try:
    version = Version(raw_version)
  except InvalidVersion:
    raise ValueError(f'Invalid version: {raw_version}')


  # List distributions

  @dataclass(slots=True)
  class Distribution:
    interpreter: str
    abi: str
    platform: str

    name: Optional[str]
    overrides: dict[str, str]

    @property
    def tag(self):
      return Tag(self.interpreter, self.abi, self.platform)

    @property
    def tag_str(self):
      return f'{self.interpreter}-{self.abi}-{self.platform}'

  default_interpreter = tool_metadata.get('interpreter', 'py3')
  default_abi = tool_metadata.get('abi', 'none')
  default_platform = tool_metadata.get('platform', 'any')

  default_overrides = tool_metadata.get('overrides', {})

  if 'distributions' in tool_metadata:
    distribution_tags = set[str]()

    def map_distribution_dict(distribution_dict: dict, /):
      name = distribution_dict.get('name')

      if name in {'all'}:
        raise ValueError(f'Reserved distribution name: {name}')

      distribution = Distribution(
        interpreter=distribution_dict.get('interpreter', default_interpreter),
        abi=distribution_dict.get('abi', default_abi),
        platform=distribution_dict.get('platform', default_platform),

        name=name,
        overrides=(default_overrides | distribution_dict.get('overrides', {})),
      )

      if distribution.tag_str in distribution_tags:
        raise ValueError(f'Conflicting distribution tag: {distribution.tag_str}')

      distribution_tags.add(distribution.tag_str)
      return distribution

    distributions = [map_distribution_dict(distribution_dict) for distribution_dict in tool_metadata['distributions']]
  else:
    distributions = [Distribution(
      interpreter=default_interpreter,
      abi=default_abi,
      platform=default_platform,

      name=None,
      overrides=default_overrides,
    )]


  # Filter distributions

  if distribution_names == 'all':
    filtered_distributions = distributions
  elif distribution_names is not None:
    target_names = set(name.strip() for name in distribution_names.split(','))
    distributions_by_name = { distribution.name: distribution for distribution in distributions if distribution.name is not None }

    filtered_distributions = [
      distributions_by_name[name] for name in target_names if name in distributions_by_name
    ]
  elif editable:
    supported_tags = set(sys_tags())

    distribution = next(
      (distribution for distribution in distributions if distribution.tag in supported_tags),
      None,
    )

    if distribution is None:
      raise RuntimeError('No compatible distribution found')

    filtered_distributions = [distribution]
  else:
    filtered_distributions = distributions


  # Write wheel

  keep_internal_symlinks = True

  first_wheel_base_name: Optional[str] = None
  snake_name = project_name.replace('-', '_')

  for distribution in filtered_distributions:
    wheel_base_name = f'{snake_name}-{version}-{distribution.tag}'
    wheel_file_name = wheel_base_name + '.whl'

    if first_wheel_base_name is None:
      first_wheel_base_name = wheel_file_name

    with ZipFile(Path(wheel_directory) / wheel_file_name, 'w') as archive:
      # Initialize

      # See: https://packaging.python.org/en/latest/specifications/recording-installed-packages/
      dist_info_path = Path(f'{snake_name}-{version}.dist-info')

      record_output = StringIO()
      record_writer = csv.writer(record_output, delimiter=',', lineterminator='\n')

      for record_path in [
        dist_info_path / 'METADATA',
        dist_info_path / 'WHEEL',
        dist_info_path / 'RECORD',
      ]:
        record_writer.writerow([str(record_path), '', ''])

      # Copy targets

      lookup = lookup_file_tree(
        root_path,
        ignore=tool_metadata.get('ignore', []),
        include=tool_metadata.get('include', []),
        overrides=distribution.overrides,
        use_gitignore=tool_metadata.get('use-gitignore', False),
      )

      if editable:
        target_parent_paths = set[Path]()

        for item in lookup:
          if (item is not None) and (item.inclusion_relation == 'target') and (not item.ignored):
            assert item.inclusion_path is not None
            target_parent_paths.add(item.path.parent)

        with archive.open(f'_{snake_name}.pth', 'w') as file:
          for path in target_parent_paths:
            file.write(f'{path.as_posix()}\n'.encode())

      else:
        copied_items_by_path = dict[Path, Item]()
        inclusion_root_names = set[str]()

        for item in lookup:
          if (item is not None) and (item.inclusion_path is not None) and (not item.ignored) and (not item.is_directory):
            if item.inclusion_relation == 'target':
              assert len(item.inclusion_path.parts) == 1
              name = item.inclusion_path.name

              if name in inclusion_root_names:
                raise ValueError(f'Conflicting inclusion root name: {name}')

              inclusion_root_names.add(name)

            copied_items_by_path[item.path] = item

        for item in copied_items_by_path.values():
          assert item.inclusion_path is not None

          target_path_str = str(item.inclusion_path)
          target_info = ZipInfo(target_path_str)

          record_writer.writerow([target_path_str, '', ''])

          if keep_internal_symlinks and item.path.is_symlink():
            target_path = item.path.readlink()

            if not target_path.is_absolute():
              target_absolute_path = normalize_path(item.path.parent / target_path)
              pointed_item = copied_items_by_path.get(target_absolute_path, None)

              if pointed_item is not None:
                assert pointed_item.inclusion_path is not None

                archive.writestr(
                  target_info,
                  (pointed_item.inclusion_path).relative_to(item.inclusion_path.parent, walk_up=True).as_posix(),
                )

                target_info.external_attr |= stat.S_IFLNK << 16

                continue

          # Using this instead of archive.write() to erase the timestamp
          with (
            item.path.open('rb') as source_file,
            archive.open(target_info, 'w') as target_file,
          ):
            shutil.copyfileobj(source_file, target_file)

      # Write metadata, record and wheel files

      with archive.open(str(dist_info_path / 'METADATA'), 'w') as metadata_file:
        # Metadata version

        metadata_file.write('Metadata-Version: 2.4\n'.encode())

        # Name and version

        metadata_file.write(f'Name: {project_name}\n'.encode())
        metadata_file.write(f'Version: {version}\n'.encode())

        # Python version

        if 'requires-python' in project_metadata:
          metadata_file.write(f'Requires-Python: {project_metadata["requires-python"]}\n'.encode())

        # Description

        if 'description' in project_metadata:
          metadata_file.write(f'Summary: {project_metadata["description"]}\n'.encode())

        # Dependencies

        for dependency in project_metadata.get('dependencies', []):
          metadata_file.write(f'Requires-Dist: {dependency}\n'.encode())

        # Authors

        if 'authors' in project_metadata:
          names, emails = process_person_list(project_metadata['authors'])

          if names:
            metadata_file.write(f'Author: {", ".join(names)}\n'.encode())

          if emails:
            metadata_file.write(f'Author-Email: {", ".join(emails)}\n'.encode())

        # Maintainers

        if 'maintainers' in project_metadata:
          names, emails = process_person_list(project_metadata['maintainers'])

          if names:
            metadata_file.write(f'Maintainer: {", ".join(names)}\n'.encode())

          if emails:
            metadata_file.write(f'Maintainer-Email: {", ".join(emails)}\n'.encode())

        # License

        if 'license' in project_metadata:
          metadata_file.write(f'License-Expression: {canonicalize_license_expression(project_metadata["license"])}\n'.encode())

        # Classifiers

        for classifier in project_metadata.get('classifiers', []):
            metadata_file.write(f'Classifier: {classifier}\n'.encode())

        # Keywords

        keywords = project_metadata.get('keywords', [])

        if keywords:
          metadata_file.write(f'Keywords: {",".join(keywords)}\n'.encode())

        # URLs

        for label, url in project_metadata.get('urls', {}).items():
          metadata_file.write(f'Project-URL: {label}, {url}\n'.encode())

        # Readme

        if 'readme' in project_metadata:
          if isinstance(project_metadata['readme'], str):
            readme_path = Path(project_metadata['readme'])
            readme_type = None
          else:
            readme_path = Path(project_metadata['readme']['file'])
            readme_type = project_metadata['readme'].get('content-type')

          if not readme_path.is_absolute():
            readme_path = root_path / readme_path

          if readme_type is None:
            match readme_path.suffix.lower():
              case '.md':
                readme_type = 'text/markdown'
              case '.rst':
                readme_type = 'text/x-rst'
              case _:
                readme_type = 'text/plain'

          metadata_file.write(f'Description-Content-Type: {readme_type}\n\n'.encode())

          # Write metadata file

          with readme_path.open('rb') as readme_file:
            shutil.copyfileobj(readme_file, metadata_file)

      # with archive.open(str(dist_info_path / 'METADATA'), 'r') as metadata_file:
      #   print(metadata_file.read().decode())

      with archive.open(str(dist_info_path / 'RECORD'), 'w') as record_file:
        record_file.write(record_output.getvalue().encode())

      with archive.open(str(dist_info_path / 'WHEEL'), 'w') as wheel_file:
        wheel_file.write('Wheel-Version: 1.0\n'.encode())


      print(f'-- Wheel contents: {wheel_base_name} --------')
      archive.printdir()
      print()


  if first_wheel_base_name is None:
    raise RuntimeError('No wheels were built')

  return first_wheel_base_name


def build_wheel(wheel_directory: str, config_settings = None, metadata_directory = None):
  return write_wheel(
    wheel_directory,
    editable=False,
    distribution_names=(config_settings.get('distributions') if config_settings is not None else None),
  )


def build_sdist(sdist_directory, config_settings = None):
  raise NotImplementedError('Sdist building is not implemented yet')


def build_editable(wheel_directory: str, config_settings = None, metadata_directory = None):
  return write_wheel(
    wheel_directory,
    editable=True,
    distribution_names=(config_settings.get('distributions') if config_settings is not None else None),
  )


__all__ = [
  'build_editable',
  'build_sdist',
  'build_wheel',
]
