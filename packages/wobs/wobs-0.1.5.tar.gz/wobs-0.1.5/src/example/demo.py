from wobs.observer import init, shutdown, new_span_as_current, new_track_point, get_status, WobsLoggingFormat
from opentelemetry import trace, context
import time
import argparse

import logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = WobsLoggingFormat(
    "%(asctime)s %(filename)s:%(lineno)d [%(levelname)s] [%(trace_id)s,%(span_id)s] %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def test_trace():
    trace_id_hex = "0af7651916cd43dd8448eb211c80319c" # 32 hex
    span_id_hex = "b9c7c989f97918e1" # 16 hex
    
    # 创建一个span，并设置属性和事件
    with new_span_as_current("test_span", trace_id=trace_id_hex) as span:
        span.set_attributes({"key": "value", "key2": "value2"})
        span.set_status(trace.StatusCode.ERROR, "error message")
        span.add_event("event1", {"event_attr": "event_value"})
        # 如果失败了，设置trace的状态和错误信息
        span.set_status(get_status(False), "error message")
        # 记录一个埋点
        new_track_point("test_trace")
        logger.info("In span: %s", span.name)
    logger.info("Out of span")
    
def test_exception():
    with new_span_as_current("test_exception") as span:
        span.set_attribute("key", "value")
        span.add_event("event1", {"event_attr": "event_value"})
        new_track_point("test_exception")
        # 模拟一个异常，异常发生后，Trace中会自动记录异常信息和堆栈
        raise Exception("raise exception test")
    
def test_rotation():
    a = 10000
    print("start test_rotation", time.time())
    for i in range(a):
        with new_span_as_current("test_rotation_{}".format(i)) as span:
            span.set_attribute("key", "value")
            span.add_event("event1", {"event_attr": "event_value"})
            new_track_point("test_rotation_{}".format(i))
    print("end test_rotation", time.time())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--modelservice",
        "-e",
        help="The endpoint of model service.",
        type=str,
        default="",
        nargs='?',
        const="",
    )
    parsed_args = parser.parse_args()
    print("modelservice:", parsed_args.modelservice, parsed_args.__dict__)
    # 初始化observer，指定trackpoint和trace文件存放目录，这里设置为当前路径，默认可不填，和C++、Golang版本保持一致
    init("test", track_point_dir='./', trace_dir='./')

    test_trace()
    new_track_point('test', {'args': parsed_args.__dict__})

    # 程序结束后关闭observer，这一步是可选的
    shutdown()