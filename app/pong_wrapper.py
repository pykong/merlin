from collections import deque
from typing import Final, NamedTuple, Self, Set

import cv2 as cv
import gym
import numpy as np
from gym.spaces import Discrete

__all__ = ["PongWrapper"]


class Step(NamedTuple):
    state: np.ndarray
    reward: float
    done: bool


class PongWrapper(gym.Wrapper):
    # https://gymnasium.farama.org/environments/atari/pong/#actions
    name: Final[str] = "pong"
    default_action: Final[int] = 0
    valid_actions: Final[Set[int]] = {0, 1, 2, 3}

    def __init__(
        self: Self,
        env_name: str,
        state_dims: tuple[int, int],
        skip: int = 1,
        step_penalty: float = 0,
        state_buffer_len: int = 1,
    ):
        env = gym.make(env_name, render_mode="rgb_array")
        env.metadata["render_fps"] = 25
        super().__init__(env)
        self.state_dims = state_dims
        self.action_space = Discrete(len(self.valid_actions))
        self.skip = skip
        self.step_penalty = step_penalty
        self.state_buffer_len = state_buffer_len
        self.state_buffer = deque([], maxlen=self.state_buffer_len)

    def step(self: Self, action: int) -> Step:
        action = self.default_action if action not in self.valid_actions else action

        total_reward = 0
        next_state = None
        reward = 0
        done = False
        for _ in range(self.skip):
            next_state, reward, done, _, _ = super().step(action)
            total_reward += reward
            if done:
                break

        if total_reward == 0:
            total_reward = -self.step_penalty

        self.state_buffer.append(self.__preprocess_state(next_state, self.state_dims))
        stacked_state = self.__stack_frames(self.state_buffer)
        return Step(stacked_state, total_reward, done)

    def reset(self: Self) -> np.ndarray:
        state = self.__preprocess_state(self.env.reset()[0], self.state_dims)
        buffer_fill = [state] * self.state_buffer_len
        self.state_buffer = deque(buffer_fill, maxlen=self.state_buffer_len)
        return self.__stack_frames(self.state_buffer)

    @staticmethod
    def __stack_frames(state_buffer: deque) -> np.ndarray:
        """Stacks first and last frame from the state buffer."""
        selected_frames = [state_buffer[-1], state_buffer[0]]
        return np.concatenate(selected_frames, axis=1)

    @staticmethod
    def __preprocess_state(state, state_dims: tuple[int, int]) -> np.ndarray:
        """Shapes the observation space."""
        state = state[33:194, 16:-16]  # crop irrelevant parts of the image
        state = cv.resize(state, state_dims, interpolation=cv.INTER_AREA)  # downsample
        state = cv.cvtColor(state, cv.COLOR_BGR2GRAY)  # remove channrl dim
        # TODO: put threshold value into constant
        _, state = cv.threshold(state, 64, 255, cv.THRESH_BINARY)  # make binary
        state = cv.normalize(
            state,
            None,
            alpha=0,
            beta=1,
            norm_type=cv.NORM_MINMAX,
            dtype=cv.CV_32F,
        )
        state = np.expand_dims(state, axis=0)  # prepend channel dimension
        return state
