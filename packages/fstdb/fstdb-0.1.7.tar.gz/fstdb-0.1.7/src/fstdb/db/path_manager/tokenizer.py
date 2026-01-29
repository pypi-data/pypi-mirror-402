from pathlib import Path
from typing import Optional, List, Union

class Tokenizer:
    """
    경로를 토큰 리스트로 변환하는 클래스
    Path, str, list 등의 형태로 받아서 List[str]로 반환
    """

    @staticmethod
    def tokenize(path: Union[str, Path, List[str]]) -> List[str]:
        """
        경로를 토큰 리스트로 변환합니다.

        Args:
            path: 변환할 경로 (str, Path, 또는 List[str])

        Returns:
            경로를 분할한 토큰 리스트

        Example:
            >>> Tokenizer.tokenize("/home/user/file.txt")
            ['home', 'user', 'file.txt']
            >>> Tokenizer.tokenize("folder/subfolder")
            ['folder', 'subfolder']
            >>> Tokenizer.tokenize(["a", "b", "c"])
            ['a', 'b', 'c']
        """
        # 모든 입력 타입을 Path로 통일
        if isinstance(path, list):
            # List[str]인 경우 Path로 변환
            # 빈 문자열과 구분자 제거 후 Path 생성
            filtered_tokens = [token for token in path if token and token not in ('/', '\\')]
            if not filtered_tokens:
                return []
            # Path 객체 생성 (리스트의 각 요소를 경로 부분으로 사용)
            path_obj = Path(*filtered_tokens)
        elif isinstance(path, Path):
            # 이미 Path 객체인 경우 그대로 사용
            path_obj = path
        else:
            # str인 경우 Path로 변환
            path_obj = Path(path)
        
        # Path의 parts를 사용하여 토큰 리스트 생성
        # 빈 부분과 구분자 제거
        tokens = [token for token in path_obj.parts if token and token not in ('/', '\\')]
        
        return tokens
