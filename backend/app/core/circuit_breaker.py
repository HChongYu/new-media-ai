"""
熔断器（Circuit Breaker）

零新增依赖的标准库实现，用于保护 LLM 等外部依赖，避免在下游
持续故障时仍堆积大量等待超时的请求，并给下游恢复留出时间。

三态流转：
- CLOSED（关闭）：正常放行；连续失败达到阈值后跳闸到 OPEN
- OPEN（打开）：请求被快速失败（不真正发起调用）；冷却结束后进入 HALF_OPEN
- HALF_OPEN（半开）：只放行一个试探请求；
  成功 → CLOSED，失败 → 重新 OPEN 并重新计时冷却

asyncio 场景下状态判断与迁移均为无 await 的同步小段，单事件循环内
天然原子，无需加锁。
"""
import enum
import logging
import time

logger = logging.getLogger(__name__)


class CircuitState(str, enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """熔断器打开（或半开试探名额已满）时的快速失败异常"""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"熔断器[{name}]已打开，请求被快速失败")


class AsyncCircuitBreaker:
    """异步调用熔断器（同步调用前的 allow/record 判定同样适用）"""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_seconds: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = 0.0
        self._trial_in_flight = False

    @property
    def state(self) -> CircuitState:
        """当前状态；OPEN 冷却到期时惰性迁移到 HALF_OPEN"""
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self.recovery_seconds:
                self._state = CircuitState.HALF_OPEN
                logger.info("熔断器[%s]冷却结束，进入 HALF_OPEN", self.name)
        return self._state

    def allow_request(self) -> bool:
        """
        调用前检查是否放行。

        CLOSED 直接放行；HALF_OPEN 仅放行一个试探请求，其余快速失败，
        避免下游尚未恢复时被并发请求再次打垮。
        """
        current = self.state
        if current == CircuitState.CLOSED:
            return True
        if current == CircuitState.HALF_OPEN and not self._trial_in_flight:
            self._trial_in_flight = True
            return True
        return False

    def record_success(self) -> None:
        """调用成功：试探成功则关闭熔断，清零计数"""
        if self._state != CircuitState.CLOSED:
            logger.info("熔断器[%s]调用成功，恢复为 CLOSED", self.name)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at = 0.0
        self._trial_in_flight = False

    def record_failure(self) -> None:
        """调用失败：CLOSED 下累计计数，HALF_OPEN 下立即重新跳闸"""
        self._trial_in_flight = False
        if self._state == CircuitState.HALF_OPEN:
            self._trip_open("半开试探失败")
            return
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._trip_open(f"连续失败 {self._failure_count} 次")

    def _trip_open(self, reason: str) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = time.monotonic()
        logger.warning(
            "熔断器[%s]跳闸 OPEN（%s），冷却 %.0f 秒",
            self.name, reason, self.recovery_seconds,
        )
