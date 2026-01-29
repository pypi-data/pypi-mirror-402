from pathlib import Path
from typing import Optional, Generic, Type, TypeVar, TYPE_CHECKING
from .db.path_manager import RecordNameChecker, String___ID_Int_Checker, Tokenizer, RecordPathManager
from .tree import TreeNode, NodeType
from .db.tree_db import _TreeDB, TreeDB, DBType
from .db.context import RecordContext
from .tree.context import TreeContext
from .tools.file_finder import FileFinder
from .db.record import Record, RecordType

if TYPE_CHECKING:
    from .db.tools.viewer import TreeDBViewer


class DBFactory(Generic[NodeType, RecordType, DBType]):
    def __init__(self, 
        NodeClass: Type[NodeType] = TreeNode, 
        TreeDBClass: Type[DBType] = TreeDB,
        RecordClass: Type[RecordType] = Record
    ):
        """
        DBFactory 초기화
        
        Args:
            NodeClass: 사용할 TreeNode 서브클래스
            TreeDBClass: 사용할 TreeDB 서브클래스 (기본값: TreeDB)
            RecordClass: 사용할 Record 서브클래스 (기본값: Record)
        """
        self.NodeClass = NodeClass
        self.TreeDBClass = TreeDBClass
        self.RecordClass = RecordClass

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
        return TreeContext[NodeType](NodeClass=self.NodeClass)

    def create_tree_db_context(self) -> RecordContext[NodeType]:
        """
        RecordContext 인스턴스를 생성하고 FileFinder와 RecordPathManager를 주입합니다.

        Returns:
            RecordContext 인스턴스
        """
        file_finder = self.create_file_finder()
        path_manager = self.create_record_path_manager()
        tree_context = self.create_tree_context()
        return RecordContext[NodeType](file_finder=file_finder, path_manager=path_manager, tree_context=tree_context, NodeClass=self.NodeClass)

    def create_tree_db(self, path: Optional[Path] = None) -> DBType:
        """
        TreeDB 인스턴스를 생성합니다.
        
        Args:
            path: 데이터베이스 경로 (None이면 기본 경로 사용)
        
        Returns:
            TreeDB 인스턴스
        """
        
        tree_db_context = self.create_tree_db_context()
        tree_context = self.create_tree_context()
        
        # TreeDBClass가 제네릭 클래스인지 확인하여 인덱싱 시도
        # 이미 구체화된 서브클래스(예: CustomTreeDB)는 인덱싱이 불가능하므로 직접 인스턴스화
        try:
            # 제네릭 클래스인 경우 인덱싱 사용
            return self.TreeDBClass[NodeType, RecordType](path=path, tree=None, tree_db_context=tree_db_context, tree_context=tree_context, NodeClass=self.NodeClass, RecordClass=self.RecordClass)
        except TypeError:
            # 제네릭이 아닌 구체화된 클래스인 경우 직접 인스턴스화
            return self.TreeDBClass(path=path, tree=None, tree_db_context=tree_db_context, tree_context=tree_context, NodeClass=self.NodeClass, RecordClass=self.RecordClass)
    
    
    def create_viewer(self, tree_db: DBType) -> 'TreeDBViewer':
        """
        TreeDBViewer 인스턴스를 생성합니다.
        
        Args:
            tree_db: TreeDB 인스턴스
        
        Returns:
            TreeDBViewer 인스턴스
        """
        from .db.tools.viewer import TreeDBViewer
        return TreeDBViewer(tree_db)