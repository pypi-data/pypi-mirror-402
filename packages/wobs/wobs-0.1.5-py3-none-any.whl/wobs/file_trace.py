from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExporter,
)
from opentelemetry.sdk.resources import Resource
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from .userInfo import GetUserInfo, get_default_observer_config, get_username

class FileSpanExporter(SpanExporter):
    """Exporter that writes spans to a local file with rotation support."""
    
    def __init__(self, service_name: str = 'unknown_service', file_path: str = None, max_bytes: int = None, backup_count: int = None):
        config = get_default_observer_config()
        self.file_path = file_path or config.TRACE
        self.filename = f"trace_{service_name}_{get_username()}.trace"
        self.max_bytes = max_bytes or config.DEFAULT_MAX_FILE_SIZE
        self.backup_count = backup_count or config.DEFAULT_MAX_FILES
        
        # 创建logger
        self.logger = logging.getLogger(f'trace.logger.{service_name}')
        self.logger.setLevel(logging.INFO)
        
        # 确保没有重复的handler
        if not self.logger.handlers:
            # 创建旋转文件处理器
            handler = RotatingFileHandler(
                os.path.join(self.file_path, self.filename), 
                maxBytes=self.max_bytes, 
                backupCount=self.backup_count
            )
            handler.setLevel(logging.INFO)
            
            # 创建格式化器
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            
            # 添加处理器到logger
            self.logger.addHandler(handler)
            self.logger.propagate = False  # Don't propagate to parent loggers
        
        # 初始化resource信息
        self.resource = Resource.create({})
        
    def export(self, spans):
        """Export spans to a local file with rotation support."""
        # 将span数据转换为指定格式的JSON
        for span in spans:
            # 构建符合trace_data_format.md格式的数据
            span_dict = {
                "host": self.resource.attributes.get("host.name", "") if hasattr(self.resource, 'attributes') else "",
                "service": self.resource.attributes.get("service.name", "unknown") if hasattr(self.resource, 'attributes') else "unknown",
                "resource": dict(self.resource.attributes) if hasattr(self.resource, 'attributes') else {},
                "name": span.name,
                "kind": span.kind.name,
                "traceID": format(span.context.trace_id, '032x'),
                "spanID": format(span.context.span_id, '016x'),
                "parentSpanID": format(span.parent.span_id, '016x') if span.parent else "",
                "links": [
                    {
                        "TraceID": format(link.context.trace_id, '032x'),
                        "SpanId": format(link.context.span_id, '016x'),
                        "TraceState": "",  # TraceState信息，设置为空字符串
                        "Attributes": dict(link.attributes) if link.attributes else {}
                    } for link in span.links
                ],
                "logs": [{
                    "Name": event.name,
                    "Time": event.timestamp,
                    "attribute": dict(event.attributes) if event.attributes else {}
                } for event in span.events],  # 日志信息，设置为空数组
                "traceState": "",  # TraceState信息，设置为空字符串
                "start": span.start_time / 1000,
                "end": span.end_time / 1000,
                "duration": (span.end_time - span.start_time) / 1000 if span.end_time and span.start_time else 0,
                "attribute": dict(span.attributes) if span.attributes else {},
                "statusCode": span.status.status_code.name if span.status else "UNSET",
                "statusMessage": span.status.description if span.status else ""
            }
            
            # 记录到文件
            json_str = json.dumps(span_dict)
            self._write_to_file(json_str)
                
        return True
    
    def _write_to_file(self, json_str):
        """Write JSON string to file asynchronously."""
        self.logger.info(json_str)
    
    def shutdown(self):
        """Shutdown the exporter."""
        # 关闭所有handler
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
    
    def set_resource(self, resource):
        """Set the resource for the exporter."""
        self.resource = resource


class TraceManager:
    """Trace 管理接口类"""
    
    def __init__(self):
        self.tracer_provider = None
        self.exporter = None
        self.processor = None
        
    def setup_tracer_provider(self, exporter: FileSpanExporter, service_name: str = 'unknown_service') -> TracerProvider:
        """
        设置TracerProvider和相关组件
        
        Args:
            exporter: Trace导出器
            service_name: 服务名称
            
        Returns:
            TracerProvider实例
        """
        # 配置trace
        trace.set_tracer_provider(TracerProvider())
        self.tracer_provider = trace.get_tracer_provider()
        # 设置resource
        res_dict = {
            "service.name": service_name,
        }
        info = GetUserInfo().get_non_empty_values()
        for k, v in info.items():
            res_dict[f'env.{k}'] = v
        resource = Resource.create(res_dict)

        exporter.set_resource(resource)
        self.exporter = exporter
        
        self.processor = BatchSpanProcessor(exporter)
        self.tracer_provider.add_span_processor(self.processor)
        
        return self.tracer_provider
    
    def get_tracer(self, name: str = __name__) -> trace.Tracer:
        """
        获取tracer
        
        Args:
            name: tracer名称
            
        Returns:
            Tracer实例
        """
        return trace.get_tracer(name)
    
    def force_flush(self):
        """强制刷新处理器以确保导出"""
        if self.processor:
            self.processor.force_flush()
    
    def shutdown(self):
        """关闭所有组件"""
        if self.processor:
            self.processor.shutdown()
        if self.exporter:
            self.exporter.shutdown()


def init_trace_manager(service_name: str = "unknown_service", file_path: str = None, max_bytes: int = None, backup_count: int = None) -> TraceManager:
    """初始化TraceManager"""
    exporter = FileSpanExporter(service_name, file_path, max_bytes, backup_count)
    trace_manager = TraceManager()
    trace_manager.setup_tracer_provider(exporter, service_name)
    return trace_manager


def get_tracer(name: str = __name__) -> trace.Tracer:
    """获取tracer"""
    return trace.get_tracer(name)
