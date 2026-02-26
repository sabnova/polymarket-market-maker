import asyncio
import time
from collections import deque
from typing import Deque, Dict, Set

from trading import perform_trade


class TradingLogicDirector:
    """
    Centralized trade orchestration layer.

    This director is intentionally conservative:
    - coalesces bursty websocket events into one decision cycle per market
    - prevents duplicate in-flight executions for the same market
    - reruns once after a burst if fresh events arrived mid-execution
    """

    def __init__(self, min_interval_seconds: float = 0.75, max_reason_history: int = 8):
        self.min_interval_seconds = min_interval_seconds
        self.max_reason_history = max_reason_history
        self._in_flight: Dict[str, asyncio.Task] = {}
        self._dirty: Set[str] = set()
        self._last_dispatch: Dict[str, float] = {}
        self._reasons: Dict[str, Deque[str]] = {}

    def schedule_trade(self, market: str, reason: str = "event") -> None:
        """Schedule a trade decision for a market with event-context tracking."""
        if market not in self._reasons:
            self._reasons[market] = deque(maxlen=self.max_reason_history)
        self._reasons[market].append(reason)

        existing_task = self._in_flight.get(market)
        if existing_task and not existing_task.done():
            self._dirty.add(market)
            return

        delay = self._get_required_delay(market)
        try:
            task = asyncio.create_task(self._run_market_cycle(market, delay))
        except RuntimeError:
            # No active event loop: skip scheduling instead of crashing data handlers.
            print(f"[Director] No active event loop; dropping trade schedule for {market}")
            return

        self._in_flight[market] = task

    def _get_required_delay(self, market: str) -> float:
        last_dispatch = self._last_dispatch.get(market, 0.0)
        elapsed = time.monotonic() - last_dispatch
        return max(0.0, self.min_interval_seconds - elapsed)

    async def _run_market_cycle(self, market: str, delay: float) -> None:
        try:
            if delay > 0:
                await asyncio.sleep(delay)

            while True:
                self._last_dispatch[market] = time.monotonic()
                reasons = ", ".join(self._reasons.get(market, []))
                if reasons:
                    print(f"[Director] {market} decision cycle. Triggers: {reasons}")

                await perform_trade(market)

                if market not in self._dirty:
                    break

                self._dirty.discard(market)
                # Yield to event loop, then re-run once with freshest market state.
                await asyncio.sleep(0)
        except Exception as ex:
            print(f"[Director] Error while executing market {market}: {ex}")
        finally:
            self._in_flight.pop(market, None)
            self._reasons.pop(market, None)


director = TradingLogicDirector()
