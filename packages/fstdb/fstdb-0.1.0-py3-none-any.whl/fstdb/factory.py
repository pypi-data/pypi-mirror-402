from pathlib import Path
from typing import Optional, Generic, Type, TypeVar, TYPE_CHECKING
from .db.path_manager import RecordNameChecker, String___ID_Int_Checker, Tokenizer, RecordPathManager
from .tree import TreeNode
from .db.tree_db import _TreeDB, TreeDB
from .db.context import RecordContext
from .tree.context import TreeContext
from .tools.file_finder import FileFinder

if TYPE_CHECKING:
    from .db.tools.viewer import TreeDBViewer

NodeType = TypeVar('NodeType', bound=TreeNode)
class DBFactory(Generic[NodeType]):
    NodeClass: Type[NodeType]
    
    def __init__(self, default_db_path: Path):
        """
        DBFactory 초기화
        
        Args:
            default_db_path: 기본 데이터베이스 경로 (선택적)
        """
        self._default_db_path = default_db_path
    
    @property
    def db_path(self) -> Path:
        """기본 데이터베이스 경로 (하위 호환성을 위해 유지)"""
        return self._default_db_path

    def create_name_checker(self) -> RecordNameChecker:
        return String___ID_Int_Checker()

    def create_tokenizer(self) -> Tokenizer:
        return Tokenizer()
    
    def create_record_path_manager(self) -> RecordPathManager:
        """
        RecordPathManager 인스턴스를 생성합니다.
        
        Returns:
            RecordPathManager 인스턴스
        """
        tokenizer = self.create_tokenizer()
        name_checker = self.create_name_checker()
        return RecordPathManager(tokenizer=tokenizer, name_checker=name_checker)
    
    def create_tree_node(self, name: str) -> TreeNode:
        return self.NodeClass(name)

    def create_file_finder(self) -> FileFinder:
        """
        FileFinder 인스턴스를 생성합니다.

        Returns:
            FileFinder 인스턴스
        """
        return FileFinder()

    def create_tree_context(self) -> TreeContext[NodeType]:
        return TreeContext[NodeType]()

    def create_tree_db_context(self) -> RecordContext[NodeType]:
        """
        RecordContext 인스턴스를 생성하고 FileFinder와 RecordPathManager를 주입합니다.

        Returns:
            RecordContext 인스턴스
        """
        file_finder = self.create_file_finder()
        path_manager = self.create_record_path_manager()
        tree_context = self.create_tree_context()
        return RecordContext[NodeType](file_finder=file_finder, path_manager=path_manager, tree_context=tree_context)

    def create_tree_db(self, path: Optional[Path] = None) -> TreeDB[NodeType]:
        """
        TreeDB 인스턴스를 생성합니다.
        
        Args:
            path: 데이터베이스 경로 (None이면 기본 경로 사용)
        
        Returns:
            TreeDB 인스턴스
        """
        db_path = path if path is not None else self.db_path
        tree_db_context = self.create_tree_db_context()
        tree_context = self.create_tree_context()
        return TreeDB[NodeType](path=db_path, tree=None, tree_db_context=tree_db_context, tree_context=tree_context)
    
    
    def create_viewer(self, tree_db: TreeDB[NodeType]) -> 'TreeDBViewer':
        """
        TreeDBViewer 인스턴스를 생성합니다.
        
        Args:
            tree_db: TreeDB 인스턴스
        
        Returns:
            TreeDBViewer 인스턴스
        """
        from .db.tools.viewer import TreeDBViewer
        return TreeDBViewer(tree_db)