from pathlib import Path
from typing import Union, List, Optional, Generic, Set, Dict, Type
from ...tree import TreeNode, NodeType
from ...tree.context import TreeContext
from ...tools.file_finder import FileFinder
from ..path_manager import RecordPathManager, RecordPath

class RecordContext(Generic[NodeType]):
    """
    TreeDB 클래스 - TreeNode를 확장하여 다양한 경로 입력을 받습니다.
    
    path를 받아서 RecordPathManager를 통해 tokenize한 뒤,
    첫 번째 토큰은 name으로, 나머지는 add 메서드로 추가합니다.
    """
 
    def __init__(self, file_finder: FileFinder, path_manager: RecordPathManager, tree_context: TreeContext[NodeType], NodeClass: Type[NodeType]):
        self.file_finder = file_finder
        self.path_manager = path_manager
        self.tree_context = tree_context
        self.NodeClass = NodeClass

    def create_tree(self, db_root_path: Path) -> NodeType:
        db_root_node = self.NodeClass(db_root_path.as_posix(), parent=None)
        for record_path in self.record_paths(db_root_path):
            record_path = record_path.relative_to(db_root_path)
            tokens = self.path_manager.tokenize(record_path)
            self.tree_context.make_child(db_root_node, tokens)
        return db_root_node

    def is_record_path(self, path: RecordPath) -> bool:
        return self.path_manager.is_record_path(path)

    def record_paths(self, path: Path) -> List[Path]:
        return self.file_finder.find_paths(path, self.is_record_path)

    def get_records(self, node: NodeType) -> List[NodeType]:
        return node.find(lambda node: self.is_record(node))

    def get_id(self, node: Union[NodeType, RecordPath]) -> int:
        if isinstance(node, TreeNode):
            try:
                return self.path_manager.get_id(node.name)
            except ValueError:
                raise ValueError(f"Invalid name: node.full_name={node.full_name}, node.name={node.name}")
        else:
            return self.path_manager.get_id_from_path(node)
    
    def get_ids(self, node: NodeType) -> Set[int]:
        return {self.get_id(record) for record in self.get_records(node)}

    def get_id_record_dict(self, node: NodeType) -> Dict[int, NodeType]:
        id_record_dict: Dict[int, NodeType] = {}
        for record in self.get_records(node):
            try:
                id_record_dict[self.get_id(record)] = record
            except Exception as e:
                print(f"Error getting id_record_dict: {e}")
                continue

        return id_record_dict
    
    def compose_path(self, name:RecordPath, id: Optional[int] = None) -> RecordPath:
        return self.path_manager.compose_path(name, id)

    def make_record(self, node: NodeType, name:RecordPath, id: Optional[int] = None) -> NodeType:

        if not self.is_record_path(name):
            raise ValueError(f"Invalid name: {name}")
        
        tokens = self.path_manager.tokenize(name)
        self.tree_context.make_child(node, tokens)
        # 생성된 노드를 반환
        return self.tree_context.get_child(node, tokens)

    def is_record(self, node: NodeType) -> bool:
        if self.path_manager.is_match(node.name):
            if len(node.children) > 0:
                raise ValueError(f"Node {node.name} is a record but has children")
            return True
        return False

    def new_id(self, existing_ids: Set[int]) -> int:
        """기존 ID 집합에서 사용 가능한 새로운 ID를 생성합니다."""
        i = 1
        while i in existing_ids:
            i += 1
        return i

    def create_record(self, tree: NodeType, name: RecordPath, existing_ids: Set[int]) -> NodeType:
        """레코드를 생성하고 반환합니다. 상태 업데이트는 호출자가 담당합니다."""
        # 새로운 ID 생성
        new_id_value = self.new_id(existing_ids)
        
        # 이름에 ID가 포함되어 있지 않으면 compose_path로 추가
        if not self.is_record_path(name):
            name = self.compose_path(name, new_id_value)
        
        # 레코드 생성 및 반환
        return self.make_record(tree, name, new_id_value)
