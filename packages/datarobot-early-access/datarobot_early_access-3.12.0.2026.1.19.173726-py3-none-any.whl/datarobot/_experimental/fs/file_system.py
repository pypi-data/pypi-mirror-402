#
# Copyright 2026 DataRobot, Inc. and its affiliates.
#
# All rights reserved.
#
# DataRobot, Inc.
#
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
#
# Released under the terms of DataRobot Tool and Utility Agreement.
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Tuple

from fsspec import AbstractFileSystem


class DataRobotFileSystem(AbstractFileSystem):  # type: ignore[misc]
    """
    fsspec implementation for DataRobot's file system.

    File paths are of the form:
        dr://<catalog_id>/path/to/file.txt
    """

    protocol = "dr"

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def _split_path(self, path: str) -> Tuple[str, str]:
        """
        Split the given path into catalog ID and internal file path.
        Internal paths can be empty.

        Parameters
        ----------
        path:
            File path in the DataRobot file system.

        Returns
        -------
        Tuple[str, str]:
            A tuple of catalog ID and the internal file path.

        Raises
        ------
        ValueError:
            If the path format is invalid.

        Examples
        --------
        .. code-block:: python

            >>> fs = DataRobotFileSystem()
            >>> fs._split_path("dr://12345/path/to/file.txt")
            ('12345', 'path/to/file.txt')

            >>> fs._split_path("dr:///12345/")
            ('12345', '')
        """
        path_without_protocol = self._strip_protocol(path).lstrip("/")
        if not path_without_protocol:
            raise ValueError(
                f"Invalid path '{path}'. Expected format: '{self.protocol}://<catalog_id>/path/to/file.txt'"
            )
        parts = path_without_protocol.split("/", 1)
        catalog_id = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        return catalog_id, internal_path

    def mkdir(self, *args: Iterable[Any], **kwargs: Dict[str, Any]) -> None:
        """Not supported as DataRobotFileSystem does not support empty directories."""
        raise NotImplementedError("mkdir is not supported for DataRobotFileSystem.")

    def makedirs(self, *args: Iterable[Any], **kwargs: Dict[str, Any]) -> None:
        """Not supported as DataRobotFileSystem does not support empty directories."""
        raise NotImplementedError("makedirs is not supported for DataRobotFileSystem.")

    def rmdir(self, *args: Iterable[Any], **kwargs: Dict[str, Any]) -> None:
        """Not supported as DataRobotFileSystem does not support empty directories."""
        raise NotImplementedError("rmdir is not supported for DataRobotFileSystem.")

    def created(self, *args: Iterable[Any], **kwargs: Dict[str, Any]) -> datetime:
        """DataRobotFileSystem does not currently expose file creation timestamp."""
        raise NotImplementedError("created is not supported for DataRobotFileSystem.")

    def modified(self, *args: Iterable[Any], **kwargs: Dict[str, Any]) -> datetime:
        """DataRobotFileSystem does not currently expose file modification timestamp."""
        raise NotImplementedError("modified is not supported for DataRobotFileSystem.")
