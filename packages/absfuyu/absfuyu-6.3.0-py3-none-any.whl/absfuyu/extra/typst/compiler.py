"""
Absfuyu: Typst
--------------
Typst multithread compiler

Version: 6.3.0
Date updated: 20/01/2026 (dd/mm/yyyy)
"""

# Module level
# ---------------------------------------------------------------------------
__all__ = ["TypstCompiler"]


# Library
# ---------------------------------------------------------------------------
import subprocess
from pathlib import Path
from typing import override

HAS_TYPST = False
try:
    import typst
except ImportError:
    from subprocess import run

    from absfuyu.config import ABSFUYU_CONFIG

    if ABSFUYU_CONFIG._get_setting("auto-install-extra").value:  # type: ignore
        cmd = "python -m pip install -U absfuyu[typst]".split()
        run(cmd)
        HAS_TYPST = True
    else:

        class DummyTypst:
            def compile(*args, **kwargs) -> None:
                pass

        typst = DummyTypst()


from absfuyu.util import is_command_available
from absfuyu.util.multithread_runner import MultiThreadRunner
from absfuyu.util.path import DirectorySelectMixin


# Class
# ---------------------------------------------------------------------------
class TypstCompiler(DirectorySelectMixin, MultiThreadRunner):
    """
    Compile all ``.typ`` files into PDFs using Typst (logger included)

    Usage:
    ------
    >>> e = TypstCompiler(<path>)
    >>> e.run()
    """

    def __init__(
        self,
        source_path: str | Path,
        create_if_not_exist: bool = False,
    ) -> None:
        super().__init__(source_path, create_if_not_exist)

        self.typst_path = "typst"

        try:
            is_command_available([self.typst_path, "compile"])
            self.has_typst = True
            self.logger.info("Using typst in PATH")
        except ValueError:
            self.logger.info("Using typst python mode")
            self.has_typst = False

    def add_typst_path(self, path: str | Path) -> None:
        if Path(path).exists():
            self.typst_path = path
            self.logger.info(f"Typst path set to {path}")

    @override
    def get_tasks(self) -> list[Path]:
        return self.select_all(".typ", recursive=True)

    @override
    def run_one(self, x: Path) -> None:
        output_file = x.with_suffix(".pdf")

        if output_file.exists():
            return

        try:
            if self.has_typst:
                subprocess.run(
                    [self.typst_path, "compile", str(x), str(output_file)],
                    check=True,
                    capture_output=True,
                )
            else:
                if not HAS_TYPST:
                    self.logger.info("No typst complier available")
                typst.compile(str(x), output=str(output_file))
        except Exception:
            self.logger.error(f"ERROR: skip {x}")
