"""
PathManager - 레코드 경로 관리를 통합하는 클래스
Tokenizer와 RecordNameChecker를 통합하여 레코드 경로 관련 작업을 수행합니다.
"""

from pathlib import Path
from typing import Union, List, Optional
from .tokenizer import Tokenizer
from .name_checker import RecordNameChecker

RecordPath = Union[str, List[str], Path]


class RecordPathManager:
    """
    레코드 경로 관리를 통합하는 클래스
    
    Tokenizer와 RecordNameChecker를 조합하여 레코드 경로 관련 작업을 수행합니다.
    """
    
    def __init__(self, tokenizer: Tokenizer, name_checker: RecordNameChecker):
        """
        RecordPathManager 초기화
        
        Args:
            tokenizer: 경로를 토큰으로 분해하는 Tokenizer 인스턴스
            name_checker: 레코드 이름을 검증하고 ID를 추출하는 RecordNameChecker 인스턴스
        """
        self.tokenizer = tokenizer
        self.name_checker = name_checker
    
    def tokenize(self, path: RecordPath) -> List[str]:
        """
        경로를 토큰 리스트로 변환합니다.
        
        Args:
            path: 변환할 경로 (str, Path, 또는 List[str])
            
        Returns:
            경로를 분할한 토큰 리스트
        """
        return self.tokenizer.tokenize(path)
    
    def get_id(self, name: str) -> int:
        """
        레코드 이름에서 ID를 추출합니다.
        
        Args:
            name: 레코드 이름
            
        Returns:
            추출된 ID
            
        Raises:
            ValueError: 유효하지 않은 이름인 경우
        """
        return self.name_checker.get_id(name)
    
    def is_match(self, name: str) -> bool:
        """
        이름이 레코드 이름 형식과 일치하는지 확인합니다.
        
        Args:
            name: 확인할 이름
            
        Returns:
            일치 여부
        """
        return self.name_checker.is_match(name)
    
    def compose(self, name: str, id: int) -> str:
        """
        이름과 ID를 조합하여 레코드 이름을 생성합니다.
        
        Args:
            name: 기본 이름 (예: "test.py", "test")
            id: 레코드 ID
            
        Returns:
            조합된 레코드 이름 (예: "test___id_1.py", "test___id_1")
        """
        return self.name_checker.compose(name, id)
    
    def is_record_path(self, path: RecordPath) -> bool:
        """
        경로가 레코드 경로인지 확인합니다.
        경로의 마지막 토큰이 레코드 이름 형식과 일치하는지 확인합니다.
        
        Args:
            path: 확인할 경로
            
        Returns:
            레코드 경로 여부
        """
        tokens = self.tokenize(path)
        if not tokens:
            return False
        last_token = tokens[-1]
        return self.is_match(last_token)
    
    def get_id_from_path(self, path: RecordPath) -> int:
        """
        경로에서 레코드 ID를 추출합니다.
        
        Args:
            path: 레코드 경로
            
        Returns:
            추출된 ID
            
        Raises:
            ValueError: 유효하지 않은 경로인 경우
        """
        tokens = self.tokenize(path)
        if not tokens:
            raise ValueError(f"Empty path: {path}")
        return self.get_id(tokens[-1])
    
    def compose_path(self, name: RecordPath, id: Optional[int] = None) -> List[str]:
        """
        이름과 ID를 조합하여 레코드 경로를 생성합니다.
        
        Args:
            name: 기본 이름 또는 경로
            id: 레코드 ID (None이면 ID 없이 반환)
            
        Returns:
            토큰 리스트로 변환된 경로
        """
        tokens = self.tokenize(name)
        if id is not None and tokens:
            tokens[-1] = self.compose(tokens[-1], id)
        return tokens
