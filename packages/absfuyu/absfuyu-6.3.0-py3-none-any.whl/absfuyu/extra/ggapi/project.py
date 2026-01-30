"""
Absfuyu: Google related
-----------------------
Project with these gg

Version: 6.3.0
Date updated: 17/01/2026 (dd/mm/yyyy)
"""

# Library
# ---------------------------------------------------------------------------
import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from absfuyu.core.dummy_func import tqdm
from absfuyu.extra.ggapi.gdrive import GoogleDriveClient, GoogleDriveFile
from absfuyu.util.path import ProjectDirInit


# ---------------------------------------------------------------------------
@dataclass
class GDriveFile:
    file: GoogleDriveFile
    path: Path | str = ""

    def download(self, directory: str | Path = ".") -> None:
        new_path = self.file.download(directory=directory)
        self.path = new_path


class ProjectWithGGAccount(ProjectDirInit):
    """W.I.P"""

    def __init__(
        self,
        source_path: str | Path,
        create_if_not_exist: bool = False,
        *,
        auto_generate: bool = False,
        manual: bool = False,
        strict_service_account: bool = True,
    ) -> None:
        """
        Project directory with Google service account

        Parameters
        ----------
        source_path : str | Path
            Root directory of the project.

        create_if_not_exist : bool
            Create the root directory if it does not exist, by default ``False``

        auto_generate : bool, optional
            Automatically create folders/files when calling add methods, by default ``False``

        manual : bool, optional
            Create folder structure manually, by default ``False``

        strict_service_account : bool, optional
            Force use encrypted service account, by default ``True``
        """

        super().__init__(source_path, create_if_not_exist, auto_generate=auto_generate)

        # Add folder
        self.add_folder("data_source")
        self.add_folder("service")

        if not manual:
            self._make_folder()
            self._make_file()

        # Var
        self.gdfile: GoogleDriveFile | None = None
        self.strict_service_account = strict_service_account
        self._gdfiles: dict[str, GDriveFile] = {}
