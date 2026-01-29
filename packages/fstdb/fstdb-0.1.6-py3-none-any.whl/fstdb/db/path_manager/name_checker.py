import re
from typing import Optional

from abc import ABC, abstractmethod


class RecordNameChecker(ABC):
    """
    레코드 이름을 검증하는 클래스
    
    생성 시 정규표현식 문자열을 인자로 받아서, str 값이 특정 조건을 만족하는지 확인합니다.
    """

    @abstractmethod
    def is_match(self, text: str) -> bool:        
        ...
    
    @abstractmethod
    def get_id(self, text: str) -> int:
        ...

class String___ID_Int_Checker(RecordNameChecker):

    def __init__(self):
        # 확장자 선택적: 이름___id_숫자 또는 이름___id_숫자.확장자
        self.name_pattern = re.compile(r'^[a-zA-Z가-힣0-9_]+___id_\d+(\.\w+)?$')
        self.id_pattern = re.compile(r'___id_(\d+)')


    def is_match(self, text: str) -> bool:        
        return bool(self.name_pattern.match(text))
    
    def get_id(self, text: str) -> int:
        match = self.id_pattern.search(text)
        if match:
            return int(match.group(1))
        raise ValueError(f"Invalid name: {text}")

    def compose(self, name: str, id: int) -> str:
        """
        이름과 ID를 조합하여 레코드 이름을 생성합니다.
        확장자가 있는 경우 확장자를 유지합니다.
        
        Args:
            name: 기본 이름 (예: "test.py", "test")
            id: 레코드 ID
            
        Returns:
            조합된 레코드 이름 (예: "test___id_1.py", "test___id_1")
        """
        # 확장자 분리
        if '.' in name and not name.startswith('.'):
            # 마지막 점을 기준으로 이름과 확장자 분리
            name_parts = name.rsplit('.', 1)
            base_name = name_parts[0]
            extension = '.' + name_parts[1]
            return f"{base_name}___id_{id}{extension}"
        else:
            # 확장자가 없는 경우
            return f"{name}___id_{id}"
