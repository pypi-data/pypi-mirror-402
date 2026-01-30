# Wuying GuestOS Observer Python
## 功能
* 记录埋点和Trace数据
* 埋点的数据格式是JSON对象，包含埋点名称（eventName）、时间（time）、属性（properties）和一些其它的配置信息，比如实例名称、版本等信息。
* Trace数据格式是JSON对象，包含TraceID、SpanID、ParentSpanID、Name、Kind、StartTime、EndTime、Duration、Attributes、Events、Links、StatusCode、StatusMessage等信息。以SLS Trace数据格式输出到本地文件, 通过定制opentelemetry-python的Exporter实现。
## 使用方法
1. 创建一个Python项目，并安装OpenTelemetry SDK
2. 使用示例可以参考demo.py
~~~python
from wobs.observer import init, shutdown, new_span_as_current, new_track_point


if __name__ == "__main__":
    # 初始化observer，指定trackpoint和trace文件存放目录，这里设置为当前路径，默认可不填，和C++、Golang版本保持一致
    init("test", track_point_dir='./', trace_dir='./')

    # 创建一个span，并设置属性和事件
    with new_span_as_current("test_trace") as span:
        # 设置属性
        span.set_attribute("key", "value")
        # 添加事件
        span.add_event("event1", {"event_attr": "event_value"})
        # 如果失败了，设置trace的状态和错误信息
        span.set_status(get_status(False), "error message")
        # 记录一个埋点
        new_track_point("test_trace")

    # 程序结束后关闭observer，这一步是可选的
    shutdown()
~~~

### 如何使用远端的trace_id创建span
创建span时，可以指定trace_id和span_id，这样trace_id和span_id就会作为span的父span，从而实现链路追踪。这里在new_span_as_current和new_span方法中做了封装，可以直接传入trace_id和span_id，具体的实现可以参考wobs/observer.py。
~~~python
    with new_span_as_current("test_trace", trace_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", span_id="xxxxxxxxxxxxxxxx") as span:
        span.set_attribute("key", "value")
~~~

## 发布
修改pyproject.toml文件中的version字段，并执行以下命令进行发布
~~~sh
uv build
uv run twine upload dist/*
~~~

## 依赖
* Opentelemetry python sdk