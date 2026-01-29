"""
regexapp.config
===============
Core attributes and metadata for the regexapp package.

This module defines application-level constants, metadata, and helper
utilities for managing references, dependencies, and configuration
files used by regexapp. It centralizes versioning, edition information,
company details, and file paths for system and user reference data.
"""

from os import path

from pathlib import Path
from pathlib import PurePath

import yaml

from regexapp.deps import genericlib_version as gtlib_version
from regexapp.deps import genericlib_File as File

import regexapp.utils as utils

__version__ = '0.6.1a1'
version = __version__
__edition__ = 'Community'
edition = __edition__

__all__ = [
    'version',
    'edition',
    'Data'
]


class Data:
    """
    Centralized application metadata and reference management for regexapp.

    The `Data` class encapsulates constants, metadata, and helper methods
    used throughout the regexapp application. It provides access to
    versioning information, company details, repository URLs, license
    text, and file paths for system and user reference data. It also
    includes utilities for retrieving dependency information and loading
    keyword or symbol definitions from YAML files.
    """

    # app yaml files
    system_reference_filename = str(
        PurePath(Path(__file__).parent, 'system_references.yaml')
    )
    symbol_reference_filename = str(
        PurePath(Path(__file__).parent, 'symbols.yaml')
    )
    sample_user_keywords_filename = str(
        PurePath(Path(__file__).parent,'sample_user_keywords.yaml')
    )
    user_reference_filename = str(
        PurePath(Path.home(), '.regexapp', 'user_references.yaml')
    )

    app_version = version

    # main app
    main_app_text = f'RegexApp v{version}'

    # packages
    pyyaml_text = f'pyyaml v{yaml.__version__}'
    pyyaml_link = 'https://pypi.org/project/PyYAML/'

    genericlib_text = f"genericlib v{gtlib_version}"
    genericlib_link = "https://pypi.org/project/genericlib/"

    # company
    company = 'Geeks Trident LLC'
    company_full_name = company
    company_name = "Geeks Trident"
    company_url = 'https://www.geekstrident.com/'

    # URL
    repo_url = 'https://github.com/Geeks-Trident-LLC/regexapp'
    documentation_url = path.join(repo_url, 'blob/develop/README.md')
    license_url = path.join(repo_url, 'blob/develop/LICENSE')

    # License
    years = '2022'
    license_name = f'RegexApp License'
    copyright_text = f'Copyright \xa9 {years}'
    license = utils.File.read('LICENSE')

    @classmethod
    def get_dependency(cls):
        dependencies = dict(
            pyyaml=dict(
                package=cls.pyyaml_text,
                url=cls.pyyaml_link
            ),
            genericlib=dict(
                package=cls.genericlib_text,
                url=cls.genericlib_link
            )
        )
        return dependencies

    @classmethod
    def get_app_keywords(cls):
        """Return system reference keywords from YAML file."""
        content = utils.File.read(Data.system_reference_filename)
        return content

    @classmethod
    def get_defined_symbols(cls):
        """Return defined symbols from YAML file."""
        content = utils.File.read(Data.symbol_reference_filename)
        return content

    @classmethod
    def get_user_custom_keywords(cls):
        """Return user custom keywords, creating file if missing."""
        filename = cls.user_reference_filename
        sample_file = cls.sample_user_keywords_filename
        if not File.is_exist(filename):
            File.create(filename)
            File.copy_file(sample_file, filename)

        content = utils.File.read(filename)
        return content
