"""
控制面板数据获取器

通过轮询 API 获取 H5 控制面板的实时数据，并通过回调函数传递给开发者。

环境变量:
    RABO_REMOTE_API_URL: 控制面板 API 地址（必需）
    RABO_REMOTE_NS: 命名空间（可选，默认 'default'）

用法:
    import rclpy
    from rabo_dev_kit import RemoteControl

    def on_control(data):
        # data: {'btn-forward': {'value': 'down'}, 'slider-speed': {'value': 50}, ...}
        if data.get('btn-forward', {}).get('value') == 'down':
            print("前进按钮按下!")

    rclpy.init()
    rc = RemoteControl(remote_id="your_panel_id", callback=on_control)
    rclpy.spin(rc)

多个控制面板:
    rc1 = RemoteControl(remote_id="panel_1", callback=on_robot1)
    rc2 = RemoteControl(remote_id="panel_2", callback=on_robot2)

    executor = MultiThreadedExecutor()
    executor.add_node(rc1)
    executor.add_node(rc2)
    executor.spin()
"""

import os
import json
import requests
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from typing import Callable, Dict, Any, Optional


class RemoteControl(Node):
    """
    控制面板数据获取器

    轮询控制面板 API，获取 H5 页面发送的控制数据，通过回调函数传递给开发者。

    Args:
        remote_id: 控制面板 ID
        callback: 数据回调函数，接收 dict 类型的控制数据
        poll_rate: 轮询频率，单位 Hz，默认 10Hz
        api_url: 完整的 API URL，默认从环境变量 RABO_REMOTE_API_URL 获取
        ns: 命名空间，默认从环境变量 RABO_REMOTE_NS 获取

    Example:
        >>> rc = RemoteControl(remote_id="abc123", callback=on_control)
    """

    def __init__(
        self,
        remote_id: str,
        callback: Callable[[Dict[str, Any]], None],
        poll_rate: float = 10.0,
        api_url: Optional[str] = None,
        ns: Optional[str] = None,
    ):
        self.ns = ns or os.getenv('RABO_REMOTE_NS', 'default')
        node_name = f"remote_control_{remote_id[:8]}"

        # 使用 ROS2 原生 namespace
        super().__init__(node_name, namespace=self.ns)

        self.remote_id = remote_id
        self.callback = callback
        # 从环境变量获取 URL 模板，替换 {remote_id} 占位符
        url_template = api_url or os.getenv('RABO_REMOTE_API_URL', '')
        self.api_url = url_template.replace('{remote_id}', remote_id)

        # 内部 topic: /{ns}/_remote_control/{remote_id}
        topic = f"_remote_control/{remote_id}"

        # 发布者 & 订阅者
        self.publisher = self.create_publisher(String, topic, 10)
        self.create_subscription(String, topic, self._on_message, 10)

        # 定时器
        self.timer = self.create_timer(1.0 / poll_rate, self._poll)

        # 状态
        self._last_data = None
        self._session = requests.Session()

        self.get_logger().info(
            f"RemoteControl started: /{self.ns}/_remote_control/{remote_id}"
        )

    def _poll(self):
        """定时轮询 API"""
        try:
            resp = self._session.get(self.api_url, timeout=2)
            if resp.status_code != 200:
                return

            result = resp.json()
            data = result.get('data', {})

            # 仅在数据变化时发布
            if data and data != self._last_data:
                msg = String()
                msg.data = json.dumps(data)
                self.publisher.publish(msg)
                self._last_data = data

        except requests.RequestException as e:
            self.get_logger().warn(
                f"API request failed: {e}",
                throttle_duration_sec=5
            )
        except Exception as e:
            self.get_logger().error(f"Poll error: {e}")

    def _on_message(self, msg: String):
        """接收消息并调用回调"""
        try:
            data = json.loads(msg.data)
            self.callback(data)
        except json.JSONDecodeError as e:
            self.get_logger().error(f"JSON decode error: {e}")
        except Exception as e:
            self.get_logger().error(f"Callback error: {e}")

    def get_latest(self) -> Dict[str, Any]:
        """
        获取最新的控制数据（非阻塞）

        Returns:
            最新的控制数据，如果没有数据则返回空字典
        """
        return self._last_data or {}
