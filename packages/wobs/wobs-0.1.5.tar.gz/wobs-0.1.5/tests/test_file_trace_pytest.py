"""
使用 pytest 编写的测试文件 - file_trace.py
"""
import os
import tempfile
import json
from unittest.mock import MagicMock
from pathlib import Path
import time

# 添加项目路径以便导入模块
import sys
sys.path.insert(0, '/Users/panxiangpeng/Work/code/wuying-guestos-observer-python')

from wobs.file_trace import FileSpanExporter, TraceManager, init_trace_manager


def test_file_span_exporter_initialization():
    """测试 FileSpanExporter 初始化"""
    temp_dir = tempfile.mkdtemp()
    service_name = "test_service_1"
    
    try:
        exporter = FileSpanExporter(
            service_name=service_name,
            file_path=temp_dir,
            max_bytes=1024,
            backup_count=2
        )
        
        assert exporter is not None
        assert exporter.file_path == temp_dir
        # 检查文件名包含正确的服务名
        assert f"trace_{service_name}_" in exporter.filename
        assert ".trace" in exporter.filename
        assert exporter.max_bytes == 1024
        assert exporter.backup_count == 2
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_file_span_exporter_export():
    """测试 FileSpanExporter 导出功能"""
    temp_dir = tempfile.mkdtemp()
    service_name = "test_service_2"
    print(temp_dir)
    
    try:
        exporter = FileSpanExporter(
            service_name=service_name,
            file_path=temp_dir,
            max_bytes=1024,
            backup_count=2
        )
        
        # 模拟 span 数据
        mock_span = MagicMock()
        mock_span.name = "test-span"
        mock_span.kind.name = "INTERNAL"
        mock_span.context.trace_id = 123456789
        mock_span.context.span_id = 987654321
        mock_span.parent = None
        mock_span.links = []
        mock_span.events = []
        mock_span.start_time = 1000000000
        mock_span.end_time = 1000001000
        mock_span.attributes = {"key": "value"}
        mock_span.status = MagicMock()
        mock_span.status.status_code.name = "OK"
        mock_span.status.description = "Success"
        
        # 调用 export 方法
        result = exporter.export([mock_span])
        time.sleep(1)  # 等待异步写入完成
        
        # 验证返回值
        assert result is True
        
        # 验证文件是否被创建（检查是否有文件）
        files = os.listdir(temp_dir)
        assert len(files) >= 1
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_trace_manager_initialization():
    """测试 TraceManager 初始化"""
    manager = TraceManager()
    
    assert manager is not None
    assert manager.tracer_provider is None
    assert manager.exporter is None
    assert manager.processor is None


def test_trace_manager_setup_tracer_provider():
    """测试 TraceManager setup_tracer_provider 方法"""
    temp_dir = tempfile.mkdtemp()
    service_name = "test_service_3"
    
    try:
        # 创建 exporter
        exporter = FileSpanExporter(
            service_name=service_name,
            file_path=temp_dir,
            max_bytes=1024,
            backup_count=2
        )
        
        # 创建 TraceManager 并设置 tracer provider
        manager = TraceManager()
        tracer_provider = manager.setup_tracer_provider(exporter, service_name)
        
        # 验证返回值
        assert tracer_provider is not None
        assert manager.tracer_provider is not None
        assert manager.exporter is not None
        assert manager.processor is not None
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_init_trace_manager():
    """测试 init_trace_manager 函数"""
    temp_dir = tempfile.mkdtemp()
    service_name = "test_service_4"
    
    try:
        manager = init_trace_manager(
            service_name=service_name,
            file_path=temp_dir,
            max_bytes=1024,
            backup_count=2
        )
        
        assert manager is not None
        assert isinstance(manager, TraceManager)
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)