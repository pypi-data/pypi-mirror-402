import inspect
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from loguru import logger


class ProjectRootFinder:
    """
    ProjectRootFinder
    TODO git, svn, hg查找均未考虑需要向上查找的情况
    """

    _cache = None

    def __init__(self, start_path: str = None):
        if start_path is None:
            self.start_path = self._get_caller_project_path()
        else:
            self.start_path = Path(start_path).resolve()

    def _get_caller_project_path(self):
        """智能获取调用者项目路径"""
        # 方法1：尝试从调用栈获取
        caller_path = self._get_caller_from_stack()
        if caller_path:
            return caller_path

        # 方法2：从sys.argv[0]获取（主脚本路径）
        main_script = self._get_main_script_path()
        if main_script:
            return main_script

        # 方法3：使用当前工作目录
        return Path.cwd()

    def _get_caller_from_stack(self):
        """从调用栈获取调用者路径"""
        try:
            stack = inspect.stack()
            library_file = Path(__file__).resolve()

            # 查找第一个不在库中的调用者
            for frame_info in stack[1:]:
                frame_file = Path(frame_info.filename).resolve()

                # 增加逻辑：如果是 Jupyter 的临时文件，直接跳过
                if "ipykernel_" in frame_info.filename:
                    continue

                # 跳过库文件和标准库文件
                if frame_file != library_file and not self._is_stdlib_or_site_packages(
                    frame_file
                ):
                    return frame_file.parent

        except Exception as _:
            pass

        return None

    def _is_stdlib_or_site_packages(self, file_path):
        """检查是否是标准库或第三方库文件"""
        path_str = str(file_path).lower()

        # 1. 获取 Python 的安装路径和虚拟环境路径
        # sys.prefix 是当前环境路径，sys.base_prefix 是基础安装路径
        prefixes = [
            sys.prefix.lower(),
            sys.base_prefix.lower(),
        ]

        # 2. 如果文件在这些路径下，直接判定为库文件
        if any(path_str.startswith(p) for p in prefixes):
            return True

        # 3. 兜底逻辑：检查常见的库标识（防止某些特殊环境）
        library_indicators = [
            "site-packages",
            "dist-packages",
            "lib/python",
            "lib64/python",
            # 针对 Jupyter 内核
            "ipykernel",
            # 部分 IDE 插件
            "apple_ignite",
            # 针对 Windows 下 Jupyter 的临时执行文件
            "appdata\\local\\temp",
        ]

        return any(indicator in path_str for indicator in library_indicators)

    def _get_main_script_path(self):
        """获取主脚本路径"""
        try:
            if sys.argv and sys.argv[0]:
                main_script = Path(sys.argv[0]).resolve()
                if main_script.exists() and main_script.is_file():
                    return main_script.parent
        except Exception:
            pass

        return None

    def _find_by_git(self) -> Optional[Path]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=self.start_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except Exception as e:
            ...
        return None

    def _find_by_svn(self) -> Optional[Path]:
        try:
            result = subprocess.run(
                ["svn", "info", "--show-item", "wcroot-abspath", str(self.start_path)],
                cwd=self.start_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except Exception as _:
            ...
        return None

    def _find_by_hg(self) -> Optional[Path]:
        try:
            result = subprocess.run(
                ["hg", "root"],
                cwd=self.start_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except Exception as _:
            ...
        return None

    def _find_by_markers(self, markers: List[str] = None) -> Optional[Path]:
        if self.start_path is None:
            return None

        if markers is None or len(markers) <= 0:
            markers = [
                "setup.py",
                "pyproject.toml",
                "setup.cfg",
                "poetry.lock",
                "uk.lock",
                "requirements.txt",
                ".git",
                ".gitignore",
                ".hg",
                "Pipfile",
                "Makefile",
                ".idea",
                ".vscode",
                ".venv",
            ]

        non_root_dir_names = {".venv", ".idea", ".git", ".vscode", ".hg"}

        candidates = {}
        max_depth = 50
        depth = 0
        current = self.start_path
        try:
            while current != current.parent and depth < max_depth:
                depth += 1

                if not current.exists() or not current.is_dir():
                    current = current.parent
                    continue

                if current.name in non_root_dir_names:
                    current = current.parent
                    continue

                marker_count = sum(
                    1 for marker in markers if (current / marker).exists()
                )
                if marker_count > 0:
                    candidates[current] = marker_count

                current = current.parent
        except Exception as _:
            pass

        if not candidates:
            return None

        best_path = max(candidates.items(), key=lambda x: x[1])[0]
        return best_path

    def _find_by_structure(self) -> Optional[Path]:
        current = self.start_path
        while current != current.parent:
            src_dir = current / "src"
            lib_dir = current / "lib"
            if (src_dir.exists() and src_dir.is_dir()) or (
                lib_dir.exists() and lib_dir.is_dir()
            ):
                py_files = list(current.glob("*.py"))
                if len(py_files) > 0 or (current / "__init__.py").exists():
                    return current
            current = current.parent
        return None

    def find_root(self, search_methods: List[str] = None) -> Path:

        if self._cache:
            return self._cache

        if search_methods is None:
            search_methods = ["git", "svn", "hg", "markers", "structure"]

        for search_method in search_methods:
            try:
                if search_method == "git":
                    result = self._find_by_git()
                elif search_method == "svn":
                    result = self._find_by_svn()
                elif search_method == "hg":
                    result = self._find_by_hg()
                elif search_method == "markers":
                    result = self._find_by_markers()
                elif search_method == "structure":
                    result = self._find_by_structure()
                else:
                    continue
            except Exception as e:
                logger.warning(
                    f"Failed: {e} to find project root by search method: {search_method}"
                )
                continue

            if result:
                self._cache = result
                return result

        raise FileNotFoundError("Unable to locate project root directory.")


def get_root_path(start_path: str = None, search_methods: List[str] = None) -> Path:
    """
    Get project root path
    :param start_path: start path
    :param search_methods: search methods
    :return: project root path
    """
    finder = ProjectRootFinder(start_path)
    return finder.find_root(search_methods)


def ensure_search_path() -> None:
    root_path = str(get_root_path())
    logger.debug(
        f"Root path: {root_path}, please make sure it's satisfied the project structure, if not, please add it to PYTHONPATH manually"
    )
    if root_path not in sys.path:
        sys.path.append(root_path)
