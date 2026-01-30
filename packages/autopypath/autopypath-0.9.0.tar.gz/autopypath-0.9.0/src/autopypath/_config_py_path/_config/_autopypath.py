"""autopypath.toml configuration module for autopypath."""

from pathlib import Path
from typing import Union

from ._toml import _TomlConfig

__all__ = ['_AutopypathConfig']


class _AutopypathConfig(_TomlConfig):
    """Configuration for autopypath using autopypath.toml files."""

    def __init__(self, repo_root_path: Union[Path, None]) -> None:
        """Configuration for autopypath using autopypath.toml files.

        If a ``autopypath.toml`` file is not found in the provided repository root path,
        the configuration will have all attributes set to ``None``.

        If the ``autopypath.toml`` file is found, it will parse the relevant
        autopypath configuration under the ``[tool.autopypath]`` section.

        :param Path | None repo_root_path: The root path of the repository containing the toml file.
            If ``None``, a special empty configuration is created with the :attr:`toml_filepath` property
            set to a :class:`NoPath` instance (a custom Path subclass representing the absence of a path).
            The configuration attributes (:attr:`repo_markers`, :attr:`paths`, :attr:`load_strategy`, and
            :attr:`path_resolution_order`) will all be set to ``None`` in this case.
        :param bool strict: (default: ``False``) Indicates whether strict mode is enabled for error handling.
        :raises AutopypathError: If the provided repo_root_path is not a valid directory.
        """
        super().__init__(repo_root_path=repo_root_path, toml_filename='autopypath.toml', toml_section='tool.autopypath')

    def __repr__(self) -> str:
        """String representation of the AutopypathConfig object.

        :return str: A string representation of the AutopypathConfig instance.
        """
        return f'{self.__class__.__name__}(repo_root_path={self._repo_root_path!r})'

    def __str__(self) -> str:
        """String conversion of the AutopypathConfig object.

        :return str: A string representation of the AutopypathConfig instance.
        """
        return self.__repr__()
