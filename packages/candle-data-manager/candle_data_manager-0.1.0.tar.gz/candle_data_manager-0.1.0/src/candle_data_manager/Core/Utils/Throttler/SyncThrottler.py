import time
import threading
from collections import deque
from loguru import logger


class SyncThrottler:
    """
    동기 방식 Rate Limiter

    슬라이딩 윈도우 기반으로 요청 속도 제한.
    여러 시간 단위(초당, 분당) 동시 제한 지원.
    스레드 세이프.
    """

    def __init__(
        self,
        requests_per_second: float = None,
        requests_per_minute: float = None,
        name: str = "Throttler"
    ):
        """
        Args:
            requests_per_second: 초당 최대 요청 수 (None이면 제한 없음)
            requests_per_minute: 분당 최대 요청 수 (None이면 제한 없음)
            name: 로깅용 이름
        """
        self.name = name
        self._lock = threading.Lock()

        # 제한 설정
        self.limits = []

        if requests_per_second is not None:
            self.limits.append({
                "window_seconds": 1.0,
                "max_requests": requests_per_second,
                "timestamps": deque(),
            })

        if requests_per_minute is not None:
            self.limits.append({
                "window_seconds": 60.0,
                "max_requests": requests_per_minute,
                "timestamps": deque(),
            })

    def wait(self, cost: int = 1) -> float:
        """
        요청 전 호출. 필요시 대기 후 요청 기록.

        Args:
            cost: 요청 비용 (기본 1)

        Returns:
            실제 대기한 시간 (초)
        """
        with self._lock:
            total_wait = 0.0

            while True:
                now = time.time()
                max_wait = 0.0

                # 각 제한에 대해 대기 시간 계산
                for limit in self.limits:
                    wait_time = self._calculate_wait(limit, now, cost)
                    max_wait = max(max_wait, wait_time)

                if max_wait <= 0:
                    # 대기 불필요 → 요청 기록
                    for limit in self.limits:
                        for _ in range(cost):
                            limit["timestamps"].append(now)
                    return total_wait

                # 대기 필요
                logger.warning(f"[{self.name}] Rate limit 대기: {max_wait:.3f}초")

                # Lock 해제 후 대기 (다른 스레드 허용)
                self._lock.release()
                try:
                    time.sleep(max_wait)
                    total_wait += max_wait
                finally:
                    self._lock.acquire()

    def _calculate_wait(self, limit: dict, now: float, cost: int) -> float:
        """
        특정 제한에 대한 대기 시간 계산

        Args:
            limit: 제한 설정 dict
            now: 현재 시간
            cost: 요청 비용

        Returns:
            대기 시간 (초), 0이면 즉시 진행 가능
        """
        window_seconds = limit["window_seconds"]
        max_requests = limit["max_requests"]
        timestamps = limit["timestamps"]

        # 윈도우 밖의 오래된 타임스탬프 제거
        window_start = now - window_seconds
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        # 현재 윈도우 내 요청 수
        current_count = len(timestamps)

        # 여유 있으면 즉시 진행
        if current_count + cost <= max_requests:
            return 0.0

        # 대기 필요: 가장 오래된 요청이 윈도우 밖으로 나갈 때까지
        if timestamps:
            oldest = timestamps[0]
            wait_time = (oldest + window_seconds) - now + 0.001  # 약간의 여유
            return max(0.0, wait_time)

        return 0.0

    def get_stats(self) -> dict:
        """현재 상태 조회"""
        with self._lock:
            now = time.time()
            stats = {"name": self.name, "limits": []}

            for limit in self.limits:
                window_seconds = limit["window_seconds"]
                max_requests = limit["max_requests"]
                timestamps = limit["timestamps"]

                # 윈도우 내 요청 수 계산
                window_start = now - window_seconds
                count = sum(1 for t in timestamps if t >= window_start)

                stats["limits"].append({
                    "window_seconds": window_seconds,
                    "max_requests": max_requests,
                    "current_count": count,
                    "usage_percent": (count / max_requests) * 100 if max_requests > 0 else 0,
                })

            return stats
