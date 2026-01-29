"""
FileSystemContext - 파일 시스템 작업을 담당하는 컨텍스트 클래스
"""

from pathlib import Path
import shutil


class FileSystemContext:
    """파일 시스템 작업을 담당하는 컨텍스트 클래스"""
    
    @staticmethod
    def _has_extension(name: str) -> bool:
        """이름에 확장자가 있는지 확인합니다."""
        # 마지막 점 이후에 문자가 있으면 확장자로 간주
        # 예: "test.py" -> True, "test" -> False, ".hidden" -> False
        if '.' not in name:
            return False
        parts = name.rsplit('.', 1)
        return len(parts) == 2 and len(parts[1]) > 0 and not name.startswith('.')
    
    @staticmethod
    def create(record_path: Path) -> None:
        """
        레코드에 해당하는 파일/폴더를 생성합니다.
        
        Args:
            record_path: 생성할 파일/폴더의 경로
        """
        # 부모 디렉토리 생성
        record_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 확장자가 있으면 파일, 없으면 폴더 생성
        if FileSystemContext._has_extension(record_path.name):
            # 파일 생성 (빈 파일)
            record_path.touch(exist_ok=True)
        else:
            # 폴더 생성
            record_path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def remove(record_path: Path) -> None:
        """
        레코드에 해당하는 파일/폴더를 삭제합니다.
        
        Args:
            record_path: 삭제할 파일/폴더의 경로
        """
        if not record_path.exists():
            return
        
        if record_path.is_file():
            record_path.unlink()
        elif record_path.is_dir():
            # 디렉토리는 비어있어야 함 (레코드는 자식이 없어야 함)
            try:
                record_path.rmdir()
            except OSError:
                # 디렉토리가 비어있지 않은 경우
                shutil.rmtree(record_path)
