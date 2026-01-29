"""
Tree node module for managing file system paths as a tree structure
"""

from typing import Optional, List, Callable, Dict, TypeVar
NodeType = TypeVar('NodeType', bound='TreeNode')

class TreeNode:
    """
    트리 노드 클래스 - 파일 시스템 경로를 트리 구조로 관리
    
    각 노드는 경로의 한 토큰을 나타내며,
    단일 name을 가지고, add 메서드를 통해 자식 노드를 추가합니다.
    """

    def __init__(self, name: str, parent: Optional['TreeNode'] = None):
        """
        TreeNode 초기화

        Args:
            name: 노드의 이름 (str)
            parent: 부모 노드 (None이면 루트 노드)
        """
        self.name = name
        self.parent = parent
        self.children: Dict[str, 'TreeNode'] = {}

    def is_root(self) -> bool:
        return self.parent == None

    def get_child(self, name: str) -> Optional['TreeNode']:
        if name in self.children:
            return self.children[name]
        return None

    def set_child(self, name: str, child: 'TreeNode') -> None:
        if name in self.children:
            raise ValueError(f"Child with name {name} already exists")
        child.parent = self
        self.children[name] = child

    def __contains__(self, name: str) -> bool:
        return self.get_child(name) is not None

    def make_child(self, name: str) -> 'TreeNode':
        if name in self.children:
            raise ValueError(f"Child with name {name} already exists")
        child = TreeNode(name, parent=self)
        self.children[name] = child
        return child

    def decouple_from_parent(self) -> None:
        if self.is_root():
            raise ValueError("Root node cannot be moved out")
        self.parent.decouple_child(self.name)
        self.parent = None

    def decouple_child(self, name: str) -> None:
        if name not in self.children:
            raise ValueError(f"Child with name {name} does not exist")
        del self.children[name]

    @property
    def full_name(self) -> List[str]:
        """
        루트부터 자기 자신까지의 name을 리스트로 반환합니다.

        Returns:
            루트부터 현재 노드까지의 name 리스트

        Example:
            >>> node = TreeNode("home")
            >>> node.add(["user", "project"])
            >>> node.full_name
            ['home']
            >>> node.children[0].full_name
            ['home', 'user']
            >>> node.children[0].children[0].full_name
            ['home', 'user', 'project']
        """
        if self.parent is None:
            # 루트 노드인 경우
            return [self.name]
        else:
            # 부모의 full_name에 자신의 name 추가
            return self.parent.full_name + [self.name]



    def find(self, 
        is_target: Callable[['TreeNode'], bool], 
        depth: int = 0, 
        max_depth: Optional[int] = None, 
        inspect_target: bool = False, # whether to inspect the target node
    ) -> List['TreeNode']:
        
        target_nodes: List['TreeNode'] = []
        if max_depth is not None and depth >= max_depth:
            return target_nodes

        if is_target(self):
            target_nodes.append(self)
            if not inspect_target:
                return target_nodes

        for node in self.children.values():
            target_nodes.extend(node.find(is_target, depth + 1, max_depth, inspect_target))

        return target_nodes

    def __len__(self) -> int:
        return len(self.children)

    def is_empty(self) -> bool:
        return len(self.children) == 0