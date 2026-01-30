from .userInfo import InitUserInfo
from .trackpoint import track_event, init_trackpoint_manager
from .file_trace import init_trace_manager, get_tracer
from opentelemetry import trace

_trace_manager = None

def set_config(config: dict):
    pass

def init(module_name: str, track_point_dir: str = None, trace_dir: str = None):
    InitUserInfo()
    global _trace_manager
    _trace_manager = init_trace_manager(service_name=module_name, file_path=trace_dir)
    init_trackpoint_manager(module_name=module_name, trackpoint_dir=track_point_dir)

def shutdown():
    global _trace_manager
    if _trace_manager:
        _trace_manager.force_flush()

def tracer():
    return get_tracer()

def new_span(name: str, trace_id: str = None, span_id: str = None):
    """
    创建一个新的span
    :param name: span名称
    :param trace_id: trace_id,如果传入则使用该trace_id,否则生成新的,格式为32位16进制字符串,如"0af7651916cd43dd8448eb211c80319c"
    :param span_id: span_id,如果传入了trace_id,则使用该span_id作为parentspanid,格式为16位16进制字符串,如"b9c7c989f97918e1"
    :return: Span对象
    """
    if trace_id:
        context = trace.set_span_in_context(trace.NonRecordingSpan(trace.SpanContext(
            trace_id=int(trace_id, 16),
            span_id=int(span_id, 16) if span_id else int('ffffffffffffffff', 16),
            is_remote=True,  # 标记为远端
            trace_flags=trace.TraceFlags(0x01)  # 采样标志
        )))
        return get_tracer().start_span(name, context=context)
    return get_tracer().start_span(name)

def new_span_as_current(name: str, trace_id: str = None, span_id: str = None):
    """
    创建一个新的span,并设置该span为当前span
    :param name: span名称
    :param trace_id: trace_id,如果传入则使用该trace_id,否则生成新的,格式为32位16进制字符串,如"0af7651916cd43dd8448eb211c80319c"
    :param span_id: span_id,如果传入了trace_id,则使用该span_id作为parentspanid,格式为16位16进制字符串,如"b9c7c989f97918e1"
    :return: Span对象迭代器
    """
    if trace_id:
        context = trace.set_span_in_context(trace.NonRecordingSpan(trace.SpanContext(
            trace_id=int(trace_id, 16),
            span_id=int(span_id, 16) if span_id else int('ffffffffffffffff', 16),
            is_remote=True,  # 标记为远端
            trace_flags=trace.TraceFlags(0x01)  # 采样标志
        )))
        return get_tracer().start_as_current_span(name, context=context)
    return get_tracer().start_as_current_span(name)

def new_track_point(event_name: str, properties: dict = None):
    return track_event(event_name, properties)

def get_status(success: bool = False) -> trace.StatusCode:
    if success:
        return trace.StatusCode.OK
    else:
        return trace.StatusCode.ERROR
    

# 创建可自动获取trace_id和span_id的日志格式化器
import logging
class WobsLoggingFormat(logging.Formatter):
    def format(self, record):
        span_context = trace.get_current_span().get_span_context()
        if span_context.is_valid:
            record.trace_id = format(span_context.trace_id, '032x')
            record.span_id = format(span_context.span_id, '016x')
        else:
            record.trace_id = ""
            record.span_id = ""
        return super().format(record)