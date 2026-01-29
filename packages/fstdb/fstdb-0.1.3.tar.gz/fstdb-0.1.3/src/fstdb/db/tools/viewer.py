"""
TreeDBViewer - TreeDB 객체를 다양한 형태로 출력하는 클래스
"""

from typing import TYPE_CHECKING
import pandas as pd

if TYPE_CHECKING:
    from ..tree_db import TreeDB
    from ...tree import TreeNode


class TreeDBViewer:
    """
    TreeDB 객체를 텍스트나 DataFrame 형태로 변환하는 클래스
    """
    
    def __init__(self, tree_db: 'TreeDB'):
        """
        TreeDBViewer 초기화
        
        Args:
            tree_db: 변환할 TreeDB 객체
        """
        self.tree_db = tree_db
    
    def to_text(self) -> str:
        """
        트리 구조를 텍스트 문자열로 반환합니다.
        
        Returns:
            트리 구조를 나타내는 문자열
        """
        return self.tree_db.tree_context.tree_to_text(self.tree_db.tree)
    
    def to_df(self) -> pd.DataFrame:
        """
        트리 구조를 pandas DataFrame으로 반환합니다.
        
        Returns:
            id와 path 컬럼을 가진 DataFrame
        """
        data = []
        
        for record_id in sorted(self.tree_db.ids):
            record = self.tree_db.get_record(record_id)
            record_path = self.tree_db.tree_context.get_record_path(record)
            data.append({
                'id': record_id,
                'path': str(record_path)
            })
        
        return pd.DataFrame(data)
