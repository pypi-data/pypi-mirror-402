"""
FileFinder module - 파일 시스템을 순회하여 조건을 만족하는 경로를 찾는 클래스
"""

from pathlib import Path
from typing import List, Callable


class FileFinder:
    """
    파일 시스템을 순회하여 조건을 만족하는 경로를 찾는 클래스
    """

    @staticmethod
    def find_paths(root_path: Path, condition: Callable[[Path], bool]) -> List[Path]:
        """
        경로의 하위 디렉터리와 파일을 순회하여 조건을 만족하는 경로를 모두 찾습니다.
        특정 경로가 조건을 만족하면 그 아래 폴더나 파일은 더 이상 순회하지 않습니다.

        Args:
            root_path: 순회를 시작할 루트 경로 (Path)
            condition: 경로가 조건을 만족하는지 확인하는 callback 함수 (Path) -> bool

        Returns:
            조건을 만족하는 경로들의 리스트 (List[Path])

        Example:
            >>> from pathlib import Path
            >>> def is_json_file(path: Path) -> bool:
            ...     return path.suffix == '.json'
            >>> results = FileFinder.find_paths(Path("/home/user"), is_json_file)
            >>> # .json 파일들만 반환
        """
        if not root_path.exists():

            return []

        results: List[Path] = []

        def traverse(current_path: Path) -> None:
            """
            재귀적으로 경로를 순회하는 내부 함수
            """
            # 현재 경로가 조건을 만족하는지 확인
            if condition(current_path):
                results.append(current_path)
                # 조건을 만족하면 하위는 더 이상 탐색하지 않음
                return

            # 디렉터리인 경우 하위 항목 순회
            if current_path.is_dir():
                try:
                    for item in current_path.iterdir():
                        traverse(item)
                except (PermissionError, OSError):
                    # 권한 오류나 기타 시스템 오류는 무시하고 계속 진행
                    pass

        # 루트 경로부터 순회 시작
        traverse(root_path)

        return results