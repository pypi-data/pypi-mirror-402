from .recorder import DataRecorder
from .utils import get_parameter_topic

# 延迟导入（避免在没有 ROS2 环境时导入失败）
def __getattr__(name):
    if name == 'SimpleSyncBridge':
        from .sync_bridge import SimpleSyncBridge
        return SimpleSyncBridge
    elif name == 'SyncRoute':
        from .sync_bridge import SyncRoute
        return SyncRoute
    elif name == 'RemoteControl':
        from .remote_control import RemoteControl
        return RemoteControl
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['DataRecorder', 'get_parameter_topic', 'SimpleSyncBridge', 'SyncRoute', 'RemoteControl']
__version__ = '0.1.10'