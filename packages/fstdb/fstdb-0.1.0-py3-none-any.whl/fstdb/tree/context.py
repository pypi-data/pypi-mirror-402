from pathlib import Path
from typing import Generic, TypeVar, List
from .tree import TreeNode

NodeType = TypeVar('NodeType', bound=TreeNode)



class TreeContext(Generic[NodeType]):

    def remove_child(self, node: NodeType, remove_empty_parent: bool = True) -> None:
        """
        node를 전체 트리에서 제거하거한다.
        remove_empty_parent가 True인 경우 부모가 빈 경우 부모도 제거한다.
        단 root는 제거되지 않는다.
        
        Args:
            node: 제거할 노드
            remove_empty_parent: 부모가 빈 경우 부모도 제거할지 여부
        """
        if node.is_root():
            return
        
        # decouple 전에 부모를 먼저 저장
        parent = node.parent
        node.decouple_from_parent()
        
        # 부모가 빈 경우 재귀적으로 제거
        if remove_empty_parent and parent is not None and parent.is_empty():
            self.remove_child(parent, remove_empty_parent)


    def get_child(self, node: NodeType, names: List[str]) -> NodeType:
        for name in names:
            if name not in node.children:
                raise ValueError(f"Child with name {name} does not exist")
            node = node.get_child(name)

        return node

    def make_child(self, node: NodeType, names: List[str]) -> None:
        """
        경로를 추가합니다.
        첫 번째 이름이 자식 노드 중에 있으면 해당 노드에 나머지 names를 전달하고,
        없으면 생성해서 전달합니다. 더 이상 인자가 없으면 종료합니다.

        Args:
            names: 추가할 경로 토큰 리스트 (List[str])

        Example:
            >>> node = TreeNode("home")
            >>> node.add(["user", "project", "file.txt"])
            >>> node.children[0].name  # 'user'
            >>> node.children[0].children[0].name  # 'project'
        """
        if not names:
            # 더 이상 인자가 없으면 종료
            return

        # 첫 번째 이름 찾기
        first_name = names[0]

        if first_name in node:
            child = node.get_child(first_name)
        else:
            child = node.make_child(first_name)        

        if len(names) > 1:
            self.make_child(child, names[1:])

    def tree_to_text(self, node: NodeType, prefix: str = "", is_last: bool = True) -> str:
        """
        자기와 자기 아래 자식들 전체에 대해 트리 구조를 텍스트 문자열로 반환합니다.

        Args:
            node: 출력할 노드
            prefix: 현재 노드 앞에 붙을 접두사 (내부적으로 사용)
            is_last: 현재 노드가 마지막 자식인지 여부 (내부적으로 사용)

        Returns:
            트리 구조를 나타내는 문자열

        Example:
            >>> node = TreeNode("home")
            >>> tree_context = TreeContext()
            >>> tree_context.make_child(node, ["user", "project", "file.txt"])
            >>> print(tree_context.tree_to_text(node))
            /home
                └── user
                    └── project
                        └── file.txt
        """
        lines = []
        
        # 최초 호출 시 노드(최상위 노드)는 전체 경로를 출력, 그 외는 이름만 출력
        if prefix == "":
            # 최상위 노드인 경우 전체 경로 출력 (마커 없이)
            full_path = self.get_record_path(node)
            display_text = str(full_path)
            lines.append(display_text)
        else:
            # 하위 노드는 이름과 마커 함께 출력
            marker = "└── " if is_last else "├── "
            display_text = node.name
            lines.append(f"{prefix}{marker}{display_text}")
        
        prefix += "    " if is_last else "│   "
        
        for i, child in enumerate(node.children.values()):
            is_last_child = (i == len(node.children) - 1)
            child_text = self.tree_to_text(child, prefix, is_last_child)
            lines.append(child_text)
        
        return "\n".join(lines)
    
    def print_tree(self, node: NodeType, prefix: str = "", is_last: bool = True) -> None:
        """
        자기와 자기 아래 자식들 전체에 대해 트리 구조를 텍스트로 출력합니다.
        
        Args:
            node: 출력할 노드
            prefix: 현재 노드 앞에 붙을 접두사 (내부적으로 사용)
            is_last: 현재 노드가 마지막 자식인지 여부 (내부적으로 사용)
        """
        print(self.tree_to_text(node, prefix, is_last))
    
    @staticmethod
    def get_record_path(record: NodeType) -> Path:
        """
        레코드의 실제 파일 시스템 경로를 반환합니다.
        
        Args:
            record: 경로를 가져올 노드
            
        Returns:
            노드의 전체 경로를 나타내는 Path 객체
            
        Note:
            full_name은 루트 노드의 name부터 포함되어 있으므로 그냥 이어 붙이면 됩니다.
        """
        return Path(*record.full_name)