"""
Absufyu: Checksum
-----------------
Check MD5, SHA256, ...

Version: 6.3.0
Date updated: 21/01/2026 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = [
    # Checksum
    "Checksum",
    "ChecksumAlgorithm",
    # Mixin
    "DirectoryChecksumMixin",
]


# Library
# ---------------------------------------------------------------------------
import hashlib
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import ClassVar, Literal, Protocol, overload, override

from absfuyu.core.baseclass import BaseClass
from absfuyu.core.docstring import deprecated, versionadded, versionchanged
from absfuyu.core.dummy_func import tqdm
from absfuyu.dxt import DictExt, ListExt
from absfuyu.util.multithread_runner import MultiThreadRunner
from absfuyu.util.path import DirectoryBase

# Setup
# ---------------------------------------------------------------------------
type ChecksumAlgorithm = Literal["md5", "sha1", "sha256", "sha512"]
type KeepMode = Literal["first", "last", "newest", "oldest"]

DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MB


class ChecksumAlgorithm(StrEnum):
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"


# Will be removed in version 7.0.0
ChecksumMode = ChecksumAlgorithm


class ChecksumVerfiyStatus(StrEnum):
    CHANGED = "changed"
    MISSING = "missing"


@dataclass
class ChecksumResult:
    path: Path
    checksum: str
    algorithm: ChecksumAlgorithm

    st_size: int | float = field(init=False)
    st_mtime: int | float = field(init=False)

    def __post_init__(self) -> None:
        st = self.path.stat()
        self.st_size = st.st_size
        self.st_mtime = st.st_mtime


@dataclass
class ChecksumVerifyResult:
    """
    Mismatch result when verify integrity

    Parameters
    ----------
    path : Path
        File path

    status : ChecksumVerfiyStatus
        Verify status

    old: str = ""
        Old hash

    new: str = ""
        New hash
    """

    path: Path
    status: ChecksumVerfiyStatus
    old: str = ""
    new: str = ""

    def to_dict(self, path_to_relative_to: Path | None = None) -> dict[str, str]:
        if path_to_relative_to is None:
            path = str(self.path.resolve())
        else:
            path = str(self.path.relative_to(path_to_relative_to))

        output = {
            "path": path,
            "status": self.status.value,
            "old": self.old,
            "new": self.new,
        }
        return output


class SupportChecksum(Protocol):
    """
    Support ``DirectoryChecksumMixin`` and its subclass
    """
    TABLE_NAME: ClassVar = "checksum"

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(
        self,
        source_path: str | Path,
        create_if_not_exist: bool = False,
        algorithm: ChecksumAlgorithm = "sha256",
        recursive: bool = True,
        *,
        using_relative_path: bool = True,
        tqdm_enabled: bool = True,
    ) -> None: ...

    def __init__(self, *args, **kwargs) -> None: ...

    # Checksum
    def _iter_files_to_checksum(self) -> Iterator[Path]: ...
    def _checksum_file(self, path: Path, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str: ...

    @overload
    def checksum(self) -> None: ...

    @overload
    def checksum(self, save_to_db: Literal[False] = ...) -> str: ...

    def checksum(self, save_to_db: bool = True) -> None | str: ...

    def verify_integrity(self) -> list[ChecksumVerifyResult]: ...


# Function
# ---------------------------------------------------------------------------
@deprecated("5.0.0")
def _checksum_operation(
    file: Path | str,
    hash_mode: ChecksumAlgorithm = "sha256",
) -> str:
    """
    This performs checksum
    """
    if hash_mode.lower() == "md5":
        hash_engine = hashlib.md5()
    elif hash_mode.lower() == "sha1":
        hash_engine = hashlib.sha1()
    elif hash_mode.lower() == "sha256":
        hash_engine = hashlib.sha256()
    elif hash_mode.lower() == "sha512":
        hash_engine = hashlib.sha512()
    else:
        hash_engine = hashlib.md5()

    with open(Path(file), "rb") as f:
        while True:
            data = f.read(4096)
            if len(data) == 0:
                break
            else:
                hash_engine.update(data)
    return hash_engine.hexdigest()


# Class
# ---------------------------------------------------------------------------
@deprecated("6.2.0")
class DuplicateSummary(DictExt[str, list[Path]]):
    """
    Duplicate file summary
    """

    def summary(self) -> int:
        """
        Show how many duplicates (include the original)

        Returns
        -------
        int
            How many duplicates
        """
        temp = self.__class__(self.copy())
        try:
            return sum(temp.apply(lambda x: len(x)).values())
        except Exception as err:
            print(f"Something wrong - {err}")

    def remove_duplicates(self, dry_run: bool = True, keep_first: bool = True, debug: bool = False) -> None:
        """
        Remove duplicates

        Parameters
        ----------
        dry_run : bool, optional
            Simulate only (no files deleted), by default ``True``

        keep_first : bool, optional
            Keep the first duplicate file, will keep the last duplicate file when ``False``, by default ``True``
        """
        temp = self.__class__(self.copy())
        removable_files = ListExt([x[1:] if keep_first else x[:-1] for x in temp.values()]).flatten()

        for x in removable_files:
            x: Path = x

            if debug or dry_run:
                print(f"Deleting {x}")
            if dry_run:
                continue

            x.unlink(missing_ok=True)


@deprecated("6.2.0")
@versionchanged("4.1.1", reason="Checksum for entire folder is possible")
@versionadded("4.1.0")
class Checksum(BaseClass):
    """
    Checksum engine

    Parameters
    ----------
    path : str | Path
        Path to file/directory to perform checksum

    hash_mode : ChecksumMode | Literal["md5", "sha1", "sha256", "sha512"], optional
        Hash mode, by default ``"sha256"``

    save_result_to_file : bool, optional
        Save checksum result(s) to file, by default ``False``
    """

    def __init__(
        self,
        path: str | Path,
        hash_mode: ChecksumAlgorithm | Literal["md5", "sha1", "sha256", "sha512"] = ChecksumAlgorithm.SHA256,
        save_result_to_file: bool = False,
    ) -> None:
        """
        Checksum engine

        Parameters
        ----------
        path : str | Path
            Path to file/directory to perform checksum

        hash_mode : ChecksumAlgorithm | Literal["md5", "sha1", "sha256", "sha512"], optional
            Hash mode, by default ``"sha256"``

        save_result_to_file : bool, optional
            Save checksum result(s) to file, by default ``False``
        """
        self.path = Path(path)
        self.hash_mode = hash_mode
        self.save_result_to_file = save_result_to_file
        self.checksum_result_file_name = "checksum_results.txt"

    def _get_hash_engine(self):
        hash_mode = self.hash_mode
        if hash_mode.lower() == "md5":
            hash_engine = hashlib.md5()
        elif hash_mode.lower() == "sha1":
            hash_engine = hashlib.sha1()
        elif hash_mode.lower() == "sha256":
            hash_engine = hashlib.sha256()
        elif hash_mode.lower() == "sha512":
            hash_engine = hashlib.sha512()
        else:
            hash_engine = hashlib.md5()
        return hash_engine

    def _checksum_operation(
        self,
        file: Path | str,
    ) -> str:
        """This performs checksum"""

        hash_engine = self._get_hash_engine().copy()
        # with open(Path(file), "rb") as f:
        with file.open("rb") as f:
            # Read and hash the file in 4K chunks. Reading the whole
            # file at once might consume a lot of memory if it is
            # large.
            while True:
                data = f.read(4096)
                if len(data) == 0:
                    break
                else:
                    hash_engine.update(data)
        return hash_engine.hexdigest()  # type: ignore

    def checksum(self, recursive: bool = True) -> str:
        """
        Perform checksum

        Parameters
        ----------
        recursive : bool, optional
            Do checksum for every file in the folder (including child folder),
            by default ``True``

        Returns
        -------
        str
            Checksum hash
        """
        if self.path.absolute().is_dir():  # Dir
            new_path = self.path.joinpath(self.checksum_result_file_name)
            # List of files
            if recursive:
                file_list: list[Path] = [x for x in self.path.glob("**/*") if x.is_file()]
            else:
                file_list = [x for x in self.path.glob("*") if x.is_file()]

            # Checksum
            res = []
            for x in tqdm(file_list, desc="Calculating hash", unit_scale=True):
                name = x.relative_to(self.path)
                res.append(f"{self._checksum_operation(x)} | {name}")
            output = "\n".join(res)
        else:  # File
            new_path = self.path.with_name(self.checksum_result_file_name)
            output = self._checksum_operation(self.path)

        # Save result
        if self.save_result_to_file:
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(output)

        return output


# Mixin
@deprecated("6.2.0")
class DirectoryRemoveDuplicateMixin(DirectoryBase):
    """
    Directory - Remove duplicate by SHA256

    - remove_duplicate
    """

    def __init__(self, source_path, create_if_not_exist: bool = False) -> None:
        super().__init__(source_path, create_if_not_exist)

        self._duplicate_cache: DuplicateSummary | None = None

    def _gather_duplicate_cache(self, recursive: bool = True) -> None:
        engine = Checksum(self.source_path, hash_mode=ChecksumAlgorithm.SHA256, save_result_to_file=False)
        valid = [x for x in engine.path.glob("**/*" if recursive else "*") if x.is_file()]
        checksum_cache = {}

        # Checksum
        for x in tqdm(valid, unit_scale=True, desc="Checking..."):
            try:
                cs_res = engine._checksum_operation(x)

                if checksum_cache.get(cs_res) is None:
                    checksum_cache[cs_res] = [x]
                else:
                    checksum_cache[cs_res] += [x]
            except Exception as err:
                print(f"ERROR: {x} - {err}")
                continue

        # Save to cache
        self._duplicate_cache = DuplicateSummary({k: v for k, v in checksum_cache.items() if len(v) > 1})

    def remove_duplicate(self, dry_run: bool = True, recursive: bool = True, debug: bool = True) -> None:
        """
        Remove duplicate files by SHA256 checksum

        Parameters
        ----------
        dry_run : bool, optional
            Simulate only (no files deleted), by default ``True``

        recursive : bool, optional
            Scan every file in the folder (including child folder), by default ``True``

        debug : bool, optional
            Print delete messages, by default ``True``
        """
        self._gather_duplicate_cache(recursive=recursive)

        # Remove
        try:
            summary = self._duplicate_cache
            print(f"Duplicate files: {summary.summary()}")
            summary.remove_duplicates(dry_run=dry_run, keep_first=False, debug=debug)
        except Exception as err:
            pass


class _MultithreadedRunnerBase[Result](MultiThreadRunner):
    def __init__(
        self,
        checksum_engine: SupportChecksum,
        algorithm: ChecksumAlgorithm = "sha256",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        super().__init__()

        self.checksum_engine = checksum_engine
        self.algorithm = algorithm
        self.chunk_size = chunk_size
        self._output: list[Result] = []

    def _checksum_file(
        self,
        path: Path,
    ) -> str:
        h = hashlib.new(self.algorithm)

        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(self.chunk_size), b""):
                h.update(chunk)

        return h.hexdigest()


class ChecksumMultithreadedRunner(_MultithreadedRunnerBase[ChecksumResult]):
    @override
    def get_tasks(self) -> list[Path]:
        return self.checksum_engine._iter_files_to_checksum()

    @override
    def run_one(self, task: Path) -> None:
        res = self._checksum_file(task)
        self._output.append(ChecksumResult(task, res, self.algorithm))


class VerifyMultithreadedRunner(_MultithreadedRunnerBase[ChecksumVerifyResult]):
    @override
    def get_tasks(self) -> list[tuple[str, str, str]]:
        with sqlite3.connect(self.checksum_engine._db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT path, path_rel, checksum FROM {self.checksum_engine.TABLE_NAME}")
            checksum_list: list[tuple[str, str, str]] = cur.fetchall()
        return checksum_list

    @override
    def run_one(self, task: tuple[str, str, str]) -> None:
        path, path_rel, old_checksum = task
        if self.checksum_engine.using_relative_path:
            file = self.checksum_engine.source_path / path_rel
        else:
            file = Path(path)

        if not file.exists():
            self._output.append(ChecksumVerifyResult(file, ChecksumVerfiyStatus.MISSING))
            return

        new_checksum = self._checksum_file(file)

        if new_checksum != old_checksum:
            self._output.append(
                ChecksumVerifyResult(
                    path=file,
                    status=ChecksumVerfiyStatus.CHANGED,
                    old=old_checksum,
                    new=new_checksum,
                )
            )


@versionadded("6.2.0")
class DirectoryChecksumMixin(DirectoryBase):
    """
    Checksum all files in a directory, storing results in SQLite Database is supported

    Atrributes
    ----------
    TABLE_NAME : str
        Name of result table in db

    Methods
    -------
    - checksum(...): Checksum files in directory
    - verify_integrity(...): Verify integrity of files
    - delete_duplicates(...): Delete duplicates
    """

    TABLE_NAME: ClassVar[str] = "checksum"

    def __init__(
        self,
        source_path: str | Path,
        create_if_not_exist: bool = False,
        algorithm: ChecksumAlgorithm = "sha256",
        recursive: bool = True,
        *,
        using_relative_path: bool = True,
        tqdm_enabled: bool = True,
    ) -> None:
        """
        Checksum all files in a directory.

        Parameters
        ----------
        source_path : str | Path
            Source directory

        create_if_not_exist : bool, optional
            Create directory when not exist, by default ``False``

        algorithm : ChecksumAlgorithm, optional
            Hash algorithm supported by ``hashlib``, by default ``"sha256"``

        recursive : bool, optional
            Include sub directories, by default ``True``

        using_relative_path : bool, optional
            Using relative path to ``source_path`` to perform checksum operations, by default ``True``

        tqdm_enabled : bool, optional
            Enable ``tqdm`` visual in terminal (if available), by default ``True``
        """
        super().__init__(source_path, create_if_not_exist)

        self.algorithm = algorithm
        self.recursive = recursive
        self.using_relative_path = using_relative_path
        self.tqdm_enabled = tqdm_enabled

        self._db_path = self.source_path.joinpath(f"{self.TABLE_NAME}.db")

    # Main
    # --------------------------------
    @overload
    def checksum_singlethread(self) -> None: ...

    @overload
    def checksum_singlethread(self, save_to_db: Literal[False] = ...) -> str: ...

    def checksum_singlethread(self, save_to_db: bool = True) -> None | str:
        """Scan directory and store checksums in database."""

        iter_list = (
            self._iter_files_to_checksum()
            if not self.tqdm_enabled
            else tqdm(list(self._iter_files_to_checksum()), desc="Generating hash", unit_scale=True)
        )

        if save_to_db:
            self._init_db()
            with sqlite3.connect(self._db_path) as conn:
                cur = conn.cursor()

                for file in iter_list:
                    checksum = self._checksum_file(file)

                    cur.execute(
                        f"""
                        INSERT OR REPLACE INTO {self.TABLE_NAME}
                        (path, path_rel, size, mtime, checksum)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            str(file),
                            str(file.relative_to(self.source_path)),
                            file.stat().st_size,
                            file.stat().st_mtime,
                            checksum,
                        ),
                    )

                conn.commit()
        else:
            output = []
            for file in iter_list:
                checksum = self._checksum_file(file)
                output.append(f"{checksum} | {file.relative_to(self.source_path)}")
            return "\n".join(output)

    @overload
    def checksum_multithreaded(self) -> None: ...

    @overload
    def checksum_multithreaded(self, save_to_db: Literal[False] = ...) -> str: ...

    def checksum_multithreaded(self, save_to_db: bool = True) -> None | str:
        cs_m = ChecksumMultithreadedRunner(checksum_engine=self, algorithm=self.algorithm)
        cs_m.run(desc="Generating hash", tqdm_enabled=self.tqdm_enabled)
        output = cs_m._output

        if save_to_db:
            self._init_db()
            with sqlite3.connect(self._db_path) as conn:
                cur = conn.cursor()

                for file in output:
                    cur.execute(
                        f"""
                        INSERT OR REPLACE INTO {self.TABLE_NAME}
                        (path, path_rel, size, mtime, checksum)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            str(file.path),
                            str(file.path.relative_to(self.source_path)),
                            file.st_size,
                            file.st_mtime,
                            file.checksum,
                        ),
                    )

                conn.commit()
        else:
            output = [f"{x.checksum} | {x.path.relative_to(self.source_path)}" for x in output]
            return "\n".join(output)

    @overload
    def checksum(self, multithreaded: bool = True) -> None: ...

    @overload
    def checksum(self, multithreaded: bool = True, save_to_db: Literal[False] = ...) -> str: ...

    def checksum(self, multithreaded: bool = True, save_to_db: bool = True) -> None | str:
        """Scan directory and store checksums in database."""
        if multithreaded:
            return self.checksum_multithreaded(save_to_db=save_to_db)
        return self.checksum_singlethread(save_to_db=save_to_db)

    def verify_integrity_singlethread(self) -> list[ChecksumVerifyResult]:
        """
        Verify current files against stored checksums.

        Returns
        -------
        list[ChecksumVerifyResult]
            Each element describes a mismatch.
        """
        mismatches: list[ChecksumVerifyResult] = []

        if not self._db_path.exists():
            raise FileNotFoundError("No checksum database found!")

        with sqlite3.connect(self._db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT path, path_rel, checksum FROM {self.TABLE_NAME}")
            checksum_list: list[tuple[str, str, str]] = (
                cur.fetchall()
                if not self.tqdm_enabled
                else tqdm(cur.fetchall(), desc="Verifying integrity", unit_scale=True)
            )

            for path, path_rel, old_checksum in checksum_list:

                if self.using_relative_path:
                    file = self.source_path / path_rel
                else:
                    file = Path(path)

                if not file.exists():
                    mismatches.append(ChecksumVerifyResult(file, ChecksumVerfiyStatus.MISSING))
                    continue

                new_checksum = self._checksum_file(file)

                if new_checksum != old_checksum:
                    mismatches.append(
                        ChecksumVerifyResult(
                            path=file,
                            status=ChecksumVerfiyStatus.CHANGED,
                            old=old_checksum,
                            new=new_checksum,
                        )
                    )

        return mismatches

    def verify_integrity_multithreaded(self) -> list[ChecksumVerifyResult]:
        """
        Verify current files against stored checksums (multithreaded).

        Returns
        -------
        list[ChecksumVerifyResult]
            Each element describes a mismatch.
        """

        if not self._db_path.exists():
            raise FileNotFoundError("No checksum database found!")

        v_m = VerifyMultithreadedRunner(checksum_engine=self, algorithm=self.algorithm)
        v_m.run(desc="Verifying integrity", tqdm_enabled=self.tqdm_enabled)
        # output = v_m._output
        mismatches: list[ChecksumVerifyResult] = v_m._output

        return mismatches

    def verify_integrity(self, multithreaded: bool = True) -> list[ChecksumVerifyResult]:
        """
        Verify current files against stored checksums.

        Returns
        -------
        list[ChecksumVerifyResult]
            Each element describes a mismatch.
        """
        if multithreaded:
            return self.verify_integrity_multithreaded()
        return self.verify_integrity_singlethread()

    # def delete_duplicates(
    #     self,
    #     *,
    #     dry_run: bool = True,
    #     keep: KeepMode = "first",
    #     ignore_database: bool = True,
    # ) -> list[Path]:
    #     """
    #     Delete duplicate files based on checksum.
    #     Works with or without a database.

    #     Parameters
    #     ----------
    #     dry_run : bool, optional
    #         If ``True``, only report files that would be deleted, by default ``True``

    #     keep : KeepMode, optional
    #         Which file to keep per checksum group, by default ``"first"``

    #     ignore_database : bool
    #         Delete duplicate files without relying on an existing database, by default ``True``

    #     Returns
    #     -------
    #     list[Path]
    #         List of deleted (or would-be deleted) files.
    #     """

    #     use_database = self._db_path.exists() and not ignore_database

    #     deleted: list[Path] = []

    #     if use_database:
    #         with sqlite3.connect(self._db_path) as conn:
    #             cur = conn.cursor()
    #             cur.execute(
    #                 f"""
    #                 SELECT checksum, path, mtime
    #                 FROM {self.TABLE_NAME}
    #                 ORDER BY checksum, mtime
    #                 """
    #             )

    #             rows = (
    #                 cur.fetchall()
    #                 if not self.tqdm_enabled
    #                 else tqdm(cur.fetchall(), desc="Analyzing duplicates", unit_scale=True)
    #             )
    #     else:
    #         _files = ((self._checksum_file(x), str(x), x.stat().st_mtime) for x in self._iter_files_to_checksum())
    #         rows = _files if not self.tqdm_enabled else tqdm(list(_files), desc="Analyzing duplicates", unit_scale=True)

    #     # Group by checksum
    #     groups: dict[str, list[tuple[Path, float]]] = {}
    #     for checksum, path, mtime in rows:
    #         groups.setdefault(checksum, []).append((Path(path), mtime))

    #     for checksum, files in groups.items():
    #         if len(files) <= 1:
    #             continue  # not duplicate

    #         # Decide which one to keep
    #         if keep == "first":
    #             keep_file = files[0][0]
    #         elif keep == "last":
    #             keep_file = files[-1][0]
    #         elif keep == "newest":
    #             keep_file = max(files, key=lambda x: x[1])[0]
    #         elif keep == "oldest":
    #             keep_file = min(files, key=lambda x: x[1])[0]
    #         else:
    #             raise ValueError(f"Invalid keep option: {keep}")

    #         for file, _ in files:
    #             if file == keep_file:
    #                 continue

    #             deleted.append(file)

    #             if not dry_run and file.exists():
    #                 file.unlink()

    #                 # Remove from DB
    #                 if use_database:
    #                     with sqlite3.connect(self._db_path) as conn:
    #                         conn.execute(
    #                             f"DELETE FROM {self.TABLE_NAME} WHERE path = ?",
    #                             (str(file),),
    #                         )
    #                         conn.commit()

    #     return deleted

    def delete_duplicates(
        self,
        *,
        dry_run: bool = True,
        keep: KeepMode = "first",
        ignore_database: bool = True,
    ) -> list[Path]:
        """
        Delete duplicate files based on checksum.
        Works with or without a database.

        Parameters
        ----------
        dry_run : bool, optional
            If ``True``, only report files that would be deleted, by default ``True``

        keep : KeepMode, optional
            Which file to keep per checksum group, by default ``"first"``

        ignore_database : bool
            Delete duplicate files without relying on an existing database, by default ``True``

        Returns
        -------
        list[Path]
            List of deleted (or would-be deleted) files.
        """
        rows, no_database = self._load_checksum_rows(ignore_database)

        groups = self._group_by_checksum(rows)

        return self._delete_from_groups(
            groups=groups,
            keep=keep,
            dry_run=dry_run,
            no_database=no_database,
        )

    # Support
    # --------------------------------
    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    path TEXT PRIMARY KEY,
                    path_rel TEXT,
                    size INTEGER,
                    mtime REAL,
                    checksum TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # Checksum
    def _iter_files_to_checksum(self) -> Iterator[Path]:
        pattern = "**/*" if self.recursive else "*"
        for path in self.source_path.glob(pattern):
            if path.is_file():
                yield path

    def _checksum_file(self, path: Path, *, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
        h = hashlib.new(self.algorithm)

        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                h.update(chunk)

        return h.hexdigest()

    # Delete
    def _load_checksum_rows(
        self,
        ignore_database: bool,
    ) -> tuple[list[tuple[str, str, str, float]], bool]:
        """
        Load (checksum, path, mtime) rows either from database or filesystem.

        Returns
        -------
        rows : list[tuple[str, str, float]]
        no_database : bool
            True if database is missing or ignored.
        """
        no_database = not self._db_path.exists()

        if not no_database and not ignore_database:
            with sqlite3.connect(self._db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    f"""
                    SELECT checksum, path, path_rel, mtime
                    FROM {self.TABLE_NAME}
                    ORDER BY checksum, mtime
                    """
                )
                rows: list[tuple[str, str, str, float]] = cur.fetchall()
        else:
            rows: list[tuple[str, str, str, float]] = [
                (self._checksum_file(p), str(p), str(p.relative_to(self.source_path)), p.stat().st_mtime)
                for p in self._iter_files_to_checksum()
            ]

        if self.tqdm_enabled:
            rows = tqdm(rows, desc="Analyzing duplicates", unit_scale=True)

        return list(rows), no_database

    def _group_by_checksum(
        self,
        rows: list[tuple[str, str, str, float]],
    ) -> dict[str, list[tuple[Path, float]]]:
        """Group rows by checksum."""
        groups: dict[str, list[tuple[Path, float]]] = {}

        for checksum, path, path_rel, mtime in rows:
            if self.using_relative_path:
                file = self.source_path / path_rel
            else:
                file = Path(path)
            groups.setdefault(checksum, []).append((file, mtime))

        return groups

    def _delete_from_groups(
        self,
        *,
        groups: dict[str, list[tuple[Path, float]]],
        keep: KeepMode,
        dry_run: bool,
        no_database: bool,
    ) -> list[Path]:
        """
        Decide which files to keep and delete duplicates.
        """
        deleted: list[Path] = []

        for files in groups.values():
            if len(files) <= 1:
                continue

            keep_file = self._select_keep_file(files, keep)

            for file, _ in files:
                if file == keep_file:
                    continue

                deleted.append(file)

                if not dry_run and file.exists():
                    file.unlink()

                    # Remove from DB
                    if not no_database:
                        with sqlite3.connect(self._db_path) as conn:
                            conn.execute(
                                f"DELETE FROM {self.TABLE_NAME} WHERE path = ?",
                                (str(file),),
                            )
                            conn.commit()

        return deleted

    def _select_keep_file(
        self,
        files: list[tuple[Path, float]],
        keep: KeepMode,
    ) -> Path:
        """Select which file to keep from a duplicate group."""
        if keep == "first":
            return files[0][0]
        if keep == "last":
            return files[-1][0]
        if keep == "newest":
            return max(files, key=lambda x: x[1])[0]
        if keep == "oldest":
            return min(files, key=lambda x: x[1])[0]

        raise ValueError(f"Invalid keep option: {keep}")
