import pickle
import zlib
from collections import deque
from pathlib import Path
from typing import Deque, Self

import numpy as np

from app.memory.transition import Transition


def ensure_transitions(func):
    """Ensure buffer has at least one transition, else raise ValueError."""

    def _decorator(self, *args, **kwargs):
        if len(self) == 0:
            raise ValueError("Attempt to sample empty replay memory.")
        return func(self, *args, **kwargs)

    return _decorator


class ReplayMemory:
    def __init__(self: Self, capacity: int, batch_size: int, preload_memory: Path):
        self.capacity = capacity
        self.batch_size = batch_size
        self.buffer: Deque[bytes] = deque(maxlen=capacity)
        if preload_memory:
            self.__fill_buffer_from_file(preload_memory)

    def push(self: Self, transition: Transition) -> None:
        bytes_ = zlib.compress(pickle.dumps(transition))
        self.buffer.append(bytes_)

    def __fill_buffer_from_file(self: Self, memory_file: Path) -> None:
        with open(memory_file, "+rb") as mf:
            all_bytes_ = pickle.load(mf)
            self.buffer.extend(all_bytes_[: self.capacity])
            print(f"Preloaded {len(all_bytes_)} transitions from {memory_file}")

    def __getitem__(self: Self, index: int) -> Transition:
        bytes_ = self.buffer[index]
        return pickle.loads(zlib.decompress(bytes_))

    def __len__(self: Self) -> int:
        return len(self.buffer)

    @ensure_transitions
    def __draw_random_indices(self: Self) -> list[int]:
        """Draw random indices, always include most recent transition."""
        sample_size = min(len(self), self.batch_size) - 1
        indices = np.random.choice(len(self), sample_size, replace=False).tolist()
        pad = [-1] * (self.batch_size - len(indices))
        return [*indices, *pad]

    @ensure_transitions
    def sample(self: Self) -> list[Transition]:
        """Sample batch of pre-configured size."""
        indices = self.__draw_random_indices()
        return [self[i] for i in indices]
