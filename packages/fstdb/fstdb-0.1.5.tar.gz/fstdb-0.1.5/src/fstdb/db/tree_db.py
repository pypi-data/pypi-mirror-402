"""
TreeDB module - TreeNode를 확장하여 다양한 경로 입력을 받는 클래스
"""

from pathlib import Path
from typing import Optional, Generic, TypeVar, Dict, Set, Type, List, TYPE_CHECKING
from ..tree import TreeNode, NodeType
from .context import RecordContext, FileSystemContext
from ..tree.context import TreeContext
from .path_manager import RecordPath
from .record import Record, RecordType

# DBType은 TreeDB의 서브클래스를 나타내는 TypeVar
# 실제 bound는 런타임에 TreeDB 클래스가 정의된 후 설정됨
DBType = TypeVar('DBType', bound='TreeDB')


class _TreeDB(Generic[NodeType, RecordType]):
    
    def __init__(self, path:Optional[Path], tree:Optional[NodeType], tree_db_context: RecordContext[NodeType], 
    tree_context: TreeContext[NodeType], NodeClass: Type[NodeType], RecordClass: Type[RecordType]):

        assert any([path, tree])
        assert not all([path, tree])

        self.record_context: RecordContext[NodeType] = tree_db_context
        self.tree_context: TreeContext[NodeType] = tree_context
        self.NodeClass = NodeClass
        self.RecordClass = RecordClass

        if path is not None:
            self.tree: NodeType = self.record_context.create_tree(path)
        else:
            self.tree: NodeType = tree

        self.id_record_dict: Dict[int, NodeType] = self.record_context.get_id_record_dict(self.tree)
        self.ids: Set[int] = self.record_context.get_ids(self.tree)
        self.records: List[NodeType] = self.record_context.get_records(self.tree)
        self.len: int = len(self.records)


    def get_record(self, id: int) -> RecordType:
        if id not in self.id_record_dict:
            raise ValueError(f"Record with id {id} does not exist")

        node = self.id_record_dict[id]
        path = self.tree_context.get_record_path(node)
        return self.RecordClass(id, path)

    def get_sub_db(self, name:RecordPath) -> '_TreeDB[NodeType, RecordType]':
        tokens = self.record_context.path_manager.tokenize(name)
        node = self.tree_context.get_child(self.tree, tokens)
        return _TreeDB(path = None, tree = node, tree_db_context = self.record_context, tree_context = self.tree_context, NodeClass = self.NodeClass, RecordClass = self.RecordClass)

    def create_record(self, name:RecordPath) -> int:
        # RecordContext에서 레코드 생성
        record = self.record_context.create_record(self.tree, name, self.ids)
        
        # TreeDB 상태 업데이트
        record_id = self.record_context.get_id(record)
        self.id_record_dict[record_id] = record
        self.ids.add(record_id)
        self.records.append(record)
        self.len += 1
        
        return record_id

    def remove_record(self, id: int) -> None:
        if id not in self.id_record_dict:
            raise ValueError(f"Record with id {id} does not exist")
        
        node = self.id_record_dict[id]
        self.tree_context.remove_child(node, remove_empty_parent=False)
        self.id_record_dict.pop(id)
        self.ids.remove(id)
        self.records.remove(node)
        self.len -= 1

    def __len__(self) -> int:
        return self.len

    def __contains__(self, id: int) -> bool:
        return id in self.ids


class TreeDB(_TreeDB[NodeType, RecordType]):
    """
    _TreeDB를 확장하여 실제 파일 시스템에 파일/폴더를 생성/삭제하는 클래스
    """
    
    def __init__(self, 
        path: Optional[Path], 
        tree: Optional[NodeType], 
        tree_db_context: RecordContext[NodeType], 
        tree_context: TreeContext[NodeType],
        NodeClass: Type[NodeType],
        RecordClass: Type[RecordType]
    ):
        super().__init__(path, tree, tree_db_context, tree_context, NodeClass, RecordClass)
        self.fs_context = FileSystemContext()
    
    def create_record(self, name: RecordPath) -> int:
        """레코드를 생성하고 실제 파일 시스템에 파일/폴더를 생성합니다."""
        # 부모 클래스의 create_record 호출
        record_id = super().create_record(name)
        
        # 생성된 레코드 가져오기
        record = self.get_record(record_id)
        
        # 실제 파일/폴더 생성
        self.fs_context.create(record.path)
        
        return record_id
    
    def remove_record(self, id: int) -> None:
        """레코드를 제거하고 실제 파일 시스템에서 파일/폴더를 삭제합니다."""
        # 레코드 가져오기 (삭제 전에)
        record = self.get_record(id)
        record_path = record.path
        
        # 부모 클래스의 remove_record 호출
        super().remove_record(id)
        
        # 실제 파일/폴더 삭제
        self.fs_context.remove(record_path)
    
    def get_sub_db(self, name: RecordPath) -> 'TreeDB[NodeType, RecordType]':
        """하위 데이터베이스를 가져옵니다."""
        # 부모 클래스의 로직을 재사용하되 TreeDB로 반환
        tokens = self.record_context.path_manager.tokenize(name)
        node = self.tree_context.get_child(self.tree, tokens)
        return TreeDB(path=None, tree=node, tree_db_context=self.record_context, tree_context=self.tree_context, NodeClass=self.NodeClass, RecordClass=self.RecordClass)