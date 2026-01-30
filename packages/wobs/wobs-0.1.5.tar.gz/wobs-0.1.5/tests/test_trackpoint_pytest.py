"""
使用 pytest 编写的测试文件 - trackpoint.py
"""
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import time

# 添加项目路径以便导入模块
import sys
sys.path.insert(0, '/Users/panxiangpeng/Work/code/wuying-guestos-observer-python')

from wobs.trackpoint import TrackPointManager, init_trackpoint_manager, track_event, track_flush


def test_trackpoint_manager_initialization():
    """测试 TrackPointManager 初始化"""
    temp_dir = tempfile.mkdtemp()
    module_name = "test_modul_1"
    
    try:
        manager = TrackPointManager(
            module_name=module_name,
            trackpoint_dir=temp_dir,
            max_file_size=1024,
            max_files=2
        )
        
        assert manager is not None
        assert manager.trackpoint_dir == temp_dir
        assert manager.module_name == module_name
        assert manager.max_file_size == 1024
        assert manager.max_files == 2
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_trackpoint_manager_get_logger():
    """测试 TrackPointManager _get_logger 方法"""
    temp_dir = tempfile.mkdtemp()
    module_name = "test_modul_2"

    try:
        manager = TrackPointManager(
            module_name=module_name,
            trackpoint_dir=temp_dir,
            max_file_size=1024,
            max_files=2
        )
        
        logger = manager._get_logger()
        assert logger is not None
        assert logger.name == f'trackpoint.logger.{module_name}'
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_trackpoint_manager_log_event_basic():
    """测试 TrackPointManager log_event 基本功能"""
    temp_dir = tempfile.mkdtemp()
    module_name = "test_modul_3"

    try:
        manager = TrackPointManager(
            module_name=module_name,
            trackpoint_dir=temp_dir,
            max_file_size=1024,
            max_files=2
        )
        
        # 记录事件
        manager.log_event("test-event", {"prop1": "value1"})
        time.sleep(1)  # 等待异步写入完成
        # 检查是否创建了文件（不需要精确验证文件名）
        files = os.listdir(temp_dir)
        # 基本验证：至少应该创建一个文件
        assert len(files) > 0
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_init_trackpoint_manager():
    """测试 init_trackpoint_manager 函数"""
    temp_dir = tempfile.mkdtemp()
    module_name = "test_modul_4"

    try:
        manager = init_trackpoint_manager(
            module_name,
            trackpoint_dir=temp_dir,
            max_file_size=1024,
            max_files=2
        )
        
        assert manager is not None
        assert isinstance(manager, TrackPointManager)
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_track_event_without_init():
    """测试在未初始化时调用 track_event"""
    # 重置全局管理器
    import wobs.trackpoint as trackpoint
    trackpoint._trackpoint_manager = None
    
    result = track_event("test-event")
    assert "Warning" in result