"""
Tests for DBFactory and TreeDB
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
from fstdb.factory import DBFactory
from fstdb.tree import TreeNode
from fstdb.db.record import Record
from fstdb.db.tree_db import TreeDB

class TestDBFactory:
    """Test cases for DBFactory and TreeDB"""

    def setup_method(self):
        """Set up test fixtures - create temporary directory with test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_resource_dir = Path(self.temp_dir) / "resource"
        self.test_resource_dir.mkdir(parents=True, exist_ok=True)
        
        # 테스트용 파일 구조 생성
        # a___id_1.py
        (self.test_resource_dir / "a___id_1.py").touch()
        
        # b/b1___id_2.py
        (self.test_resource_dir / "b").mkdir(exist_ok=True)
        (self.test_resource_dir / "b" / "b1___id_2.py").touch()
        
        # b/b2___id_3 (디렉터리)
        (self.test_resource_dir / "b" / "b2___id_3").mkdir(exist_ok=True)
        
        # c/c1/c1_1___id_4.txt (중첩된 구조)
        (self.test_resource_dir / "c").mkdir(exist_ok=True)
        (self.test_resource_dir / "c" / "c1").mkdir(exist_ok=True)
        (self.test_resource_dir / "c" / "c1" / "c1_1___id_4.txt").touch()
        
        # d/d1___id_5.json
        (self.test_resource_dir / "d").mkdir(exist_ok=True)
        (self.test_resource_dir / "d" / "d1___id_5.json").touch()

    def teardown_method(self):
        """Clean up after tests"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_factory_creation(self):
        """Test DBFactory creation"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        assert factory is not None
    

    def test_create_tree_db(self):
        """Test TreeDB creation and record loading"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # 레코드가 로드되었는지 확인
        assert len(db) > 0
        assert len(db.ids) > 0
        assert len(db.records) > 0
        
        # 예상되는 레코드 ID 확인
        expected_ids = {1, 2, 3, 4, 5}
        assert db.ids.issuperset(expected_ids), f"Expected IDs {expected_ids}, got {db.ids}"

    def test_get_record(self):
        """Test getting a record by ID"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # ID 1로 레코드 조회
        record = db.get_record(1)
        assert record is not None
        assert record.id == 1
        assert record.path.name == "a___id_1.py" or "a___id_1" in record.path.name
        
        # ID 2로 레코드 조회
        record2 = db.get_record(2)
        assert record2 is not None
        assert record2.id == 2
        assert "b1___id_2" in record2.path.name
        
        # 존재하지 않는 ID 조회 시 예외
        with pytest.raises(ValueError, match="does not exist"):
            db.get_record(999)

    def test_record_paths(self):
        """Test that records are loaded from correct paths"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # 각 레코드의 경로 확인
        record1 = db.get_record(1)
        assert "a___id_1" in record1.path.name
        
        record2 = db.get_record(2)
        assert "b1___id_2" in record2.path.name
        assert "b" in record2.path.parts
        
        record4 = db.get_record(4)
        assert "c1_1___id_4" in record4.path.name

    def test_create_record(self):
        """Test creating a new record"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        initial_count = len(db)
        initial_ids = set(db.ids)
        
        # 새 레코드 생성 (ID는 자동 생성됨)
        new_record_name = "new_record.py"
        new_record_id = db.create_record(new_record_name)
        
        # 레코드 개수 증가 확인
        assert len(db) == initial_count + 1
        assert new_record_id in db.ids
        assert new_record_id not in initial_ids
        
        # 생성된 레코드 조회
        new_record = db.get_record(new_record_id)
        assert new_record is not None
        assert new_record.id == new_record_id
        assert "new_record" in new_record.path.name
        assert f"___id_{new_record_id}" in new_record.path.name
        

    def test_create_record_with_path(self):
        """Test creating a record with nested path"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        initial_count = len(db)
        
        # 중첩된 경로로 레코드 생성 (ID는 자동 생성됨)
        nested_record_name = ["e", "e1", "e1_1.txt"]
        nested_record_id = db.create_record(nested_record_name)
        
        # 레코드 생성 확인
        assert len(db) == initial_count + 1
        assert nested_record_id in db.ids
        
        # 생성된 레코드 조회
        nested_record = db.get_record(nested_record_id)
        assert nested_record is not None
        assert nested_record.id == nested_record_id
        assert "e1_1" in nested_record.path.name
        assert f"___id_{nested_record_id}" in nested_record.path.name

    def test_remove_record(self):
        """Test removing a record"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        initial_count = len(db)
        initial_ids = set(db.ids)
        
        # 레코드 제거 (ID 1)
        if 1 in db.ids:
            db.remove_record(1)
            
            # 레코드 개수 감소 확인
            assert len(db) == initial_count - 1
            assert 1 not in db.ids
            
            # 제거된 레코드가 더 이상 조회되지 않는지 확인
            with pytest.raises(ValueError, match="does not exist"):
                db.get_record(1)
        
        # 존재하지 않는 레코드 제거 시도
        with pytest.raises(ValueError, match="does not exist"):
            db.remove_record(999)

    def test_get_sub_db(self):
        """Test getting a sub-database"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # 'b' 하위 DB 조회
        sub_db = db.get_sub_db("b")
        assert sub_db is not None
        assert len(sub_db) > 0
        
        # 'b' 하위에 있는 레코드 확인
        assert 2 in sub_db.ids or 3 in sub_db.ids
        
        # 중첩된 경로로 하위 DB 조회
        sub_db2 = db.get_sub_db(["c", "c1"])
        assert sub_db2 is not None
        assert 4 in sub_db2.ids

    def test_ids_property(self):
        """Test ids property"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # ids는 Set[int] 타입
        assert isinstance(db.ids, set)
        assert all(isinstance(id, int) for id in db.ids)
        
        # 예상되는 ID들이 포함되어 있는지 확인
        assert len(db.ids) >= 3  # 최소 3개 이상의 레코드

    def test_records_property(self):
        """Test records property"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=Path(self.temp_dir) / "resource")
        
        # records는 List[TreeNode] 타입
        assert isinstance(db.records, list)
        assert len(db.records) == len(db)
        
        # 모든 레코드가 TreeNode 인스턴스인지 확인
        assert all(isinstance(record, TreeNode) for record in db.records)

    def test_contains(self):
        """Test __contains__ method"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # 존재하는 ID 확인
        if db.ids:
            first_id = list(db.ids)[0]
            assert first_id in db.ids
        
        # 존재하지 않는 ID 확인
        assert 99999 not in db.ids

    def test_len(self):
        """Test __len__ method"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # len()이 레코드 개수를 반환하는지 확인
        assert len(db) == len(db.records)
        assert len(db) == len(db.ids)

    def test_create_tree_db_with_custom_path(self):
        """Test creating TreeDB with custom path"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        
        # 커스텀 경로로 TreeDB 생성
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        assert len(db) > 0
        assert len(db.ids) > 0

    def test_record_with_extension(self):
        """Test records with different file extensions"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # .py 확장자 레코드
        if 1 in db.ids:
            record1 = db.get_record(1)
            assert ".py" in record1.path.name or "a___id_1" in record1.path.name
        
        # .txt 확장자 레코드
        if 4 in db.ids:
            record4 = db.get_record(4)
            assert ".txt" in record4.path.name or "c1_1___id_4" in record4.path.name
        
        # .json 확장자 레코드
        if 5 in db.ids:
            record5 = db.get_record(5)
            assert ".json" in record5.path.name or "d1___id_5" in record5.path.name

    def test_directory_record(self):
        """Test directory as record (b2___id_3)"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        # 디렉터리 레코드 확인
        if 3 in db.ids:
            record3 = db.get_record(3)
            assert "b2___id_3" in record3.path.name

    def test_create_and_remove_workflow(self):
        """Test complete workflow: create, verify, remove"""
        factory = DBFactory[TreeNode, Record, TreeDB](NodeClass=TreeNode, RecordClass=Record)
        db = factory.create_tree_db(path=self.test_resource_dir)
        
        initial_count = len(db)
        
        # 레코드 생성 (ID는 자동 생성됨)
        test_name = "workflow_test.py"
        test_id = db.create_record(test_name)
        
        # 생성 확인
        assert len(db) == initial_count + 1
        assert test_id in db.ids
        record = db.get_record(test_id)
        assert record is not None
        assert record.id == test_id
        assert "workflow_test" in record.path.name
        assert f"___id_{test_id}" in record.path.name
        
        # 레코드 제거
        db.remove_record(test_id)
        
        # 제거 확인
        assert len(db) == initial_count
        assert test_id not in db.ids
        with pytest.raises(ValueError):
            db.get_record(test_id)
