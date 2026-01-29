"""
Path Manager Module
레코드 경로 관리를 위한 모듈
"""

from pathlib import Path
from typing import Union, List

from .tokenizer import Tokenizer
from .name_checker import RecordNameChecker, String___ID_Int_Checker
from .path_manager import RecordPathManager

# RecordPath 타입 정의
RecordPath = Union[str, List[str], Path]

__all__ = ["Tokenizer", "RecordNameChecker", "String___ID_Int_Checker", "RecordPathManager", "RecordPath"]
