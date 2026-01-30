# VXSched

VXSched 是一个轻量级的 Python 事件调度器，支持多种触发器（Cron、间隔、一次性）和事件驱动的架构。它旨在简化定时任务和事件处理的管理。

## 特性

*   **轻量级**: 单文件实现，易于集成。
*   **灵活的触发器**:
    *   `CronTrigger`: 支持标准 Cron 表达式。
    *   `IntervalTrigger`: 支持固定时间间隔执行。
    *   `OnceTrigger`: 支持特定时间点的一次性执行。
*   **事件驱动**: 基于事件和处理器的设计，解耦任务逻辑。
*   **装饰器支持**: 使用装饰器轻松注册事件处理器。
*   **配置管理**: 内置只读配置管理和持久化参数存储。
*   **CLI 工具**: 提供命令行工具快速初始化和运行项目。

## 依赖

*   `pydantic`
*   `vxutils` (需要确保该模块在路径中)

## 快速开始

### 1. 初始化项目

使用 `init` 命令初始化配置目录和示例文件：

```bash
python vxsched.py init -t my_project -e
```

这将创建 `my_project` 目录，包含配置文件 `config.json` 和示例处理器 `mods/handlers.py`。

### 2. 编写处理器

在 `mods/handlers.py` 中定义你的事件处理器：

```python
import logging
from vxutils import loggerConfig
from vxsched import register, Event, Scheduler, INIT_EVENT, daily, every,APP

# 注册一个自定义事件处理器
@register("my_task")
def handle_my_task(app: Scheduler, event: Event):
    logging.info(f"Processing my_task: {event}")

# 在调度器启动时注册定时任务
@register(INIT_EVENT)
def on_init(app: Scheduler, event: Event):
    logging.info("Scheduler started!")
    
    # 每天 08:00 执行
    app.submit("my_task", trigger=daily("08:00:00"))
    
    # 每 3 秒执行一次
    app.submit(Event(type="my_task", data={"msg": "Hello"}), trigger=every(3))
    
if __name__ == "__main__":
    try:
        loggerConfig(level="INFO", filename="", force=True)
        APP.start()
        APP.submit(Event(type="test"))
        APP.wait()
    except KeyboardInterrupt:
        pass
    finally:
        APP.stop()

```

### 3. 运行调度器

使用 `run` 命令启动调度器：

```bash
python vxsched.py run -m my_project/mods
```

## API 参考

### 触发器装饰器

*   `@daily(time_str)`: 每天指定时间触发 (e.g., "08:00:00")。
*   `@weekly(time_str, day_of_week)`: 每周指定时间触发 (day_of_week: 0-6, 0 is Monday)。
*   `@every(interval)`: 每隔 `interval` 秒触发。
*   `@crontab(expression)`: 使用 Cron 表达式触发。
*   `@once(datetime)`: 在指定时间触发一次。

注意：这些函数返回 `Trigger` 对象，通常用于 `app.submit(..., trigger=...)`。

### 注册处理器

使用 `@register(event_type)` 装饰器将函数注册为事件处理器。

```python
@register("event_name")
def my_handler(app: Scheduler, event: Event):
    ...
```

### 提交任务

使用 `app.submit(event, trigger=...)` 提交任务。

*   `event`: 可以是 `Event` 对象或事件类型字符串。
*   `trigger`: (可选) 触发器对象。如果不提供，默认为立即执行一次。

```python
# 立即执行
app.submit("simple_task")

# 延迟/定时执行
app.submit("recurring_task", trigger=every(60))
```

## 内置事件

*   `INIT_EVENT` (`__INIT__`): 调度器启动时触发。用于初始化资源或提交初始定时任务。
*   `SHUTDOWN_EVENT` (`__SHUTDOWN__`): 调度器停止时触发。用于清理资源。

## 配置与参数

*   **Config**: `vxsched.json` 中的配置加载后为只读属性，通过 `app.config` 访问。
*   **Params**: `app.params` 用于存储需要在重启后持久化的运行时参数。使用 `app.params.set_params(key, value, persist=True)` 保存。
