"""
python.emulation.clock
======================
Deterministic FPGA Tick and Simulation Clock Controller.
Allows:
- Synchronous single-tick stepping: tick()
- Synchronous batch execution: run_ticks(N)
- Optional background real-time ticker for interactive PuTTY/CLI sessions
"""

import threading
import time
from typing import List, Callable


class FPGASimulationClock:
    """
    Deterministic simulation clock coordinator.
    Registers sub-models and executes their synchronous posedge clk / update_tick routines.
    """

    def __init__(self, tick_rate_hz: float = 10.0):
        self.tick_rate_hz = tick_rate_hz
        self.total_ticks: int = 0
        self._listeners: List[Callable[[], None]] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def register_listener(self, callback: Callable[[], None]):
        """Registers an RTL model tick callback."""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def register_model(self, model: any):
        """Registers an RTL model by attaching its tick/update_tick/step method."""
        if hasattr(model, 'tick') and callable(getattr(model, 'tick')):
            self.register_listener(model.tick)
        elif hasattr(model, 'update_tick') and callable(getattr(model, 'update_tick')):
            self.register_listener(model.update_tick)
        elif hasattr(model, 'step') and callable(getattr(model, 'step')):
            self.register_listener(model.step)

    @property
    def tick_count(self) -> int:
        return self.total_ticks

    @property
    def is_running(self) -> bool:
        return self._running

    def tick(self):
        """Executes exactly one discrete clock update tick across all models."""
        with self._lock:
            self.total_ticks += 1
            for listener in self._listeners:
                listener()

    def run_ticks(self, count: int):
        """Deterministically runs exactly count ticks synchronously."""
        for _ in range(count):
            self.tick()

    def reset_clock(self):
        """Resets tick counter."""
        with self._lock:
            self.total_ticks = 0

    def start_background(self):
        """Starts real-time background clock ticker for live interactive CLI."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="FPGA-Clock-Daemon")
        self._thread.start()

    def start_autonomous_ticks(self):
        self.start_background()

    def stop_background(self):
        """Stops background clock ticker."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def stop_autonomous_ticks(self):
        self.stop_background()

    def _loop(self):
        interval = 1.0 / self.tick_rate_hz
        while self._running:
            t0 = time.perf_counter()
            self.tick()
            elapsed = time.perf_counter() - t0
            sleep_time = max(0.001, interval - elapsed)
            time.sleep(sleep_time)
