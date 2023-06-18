import torch
from torch import nn

from ._base_net import BaseNet


class BigNet(BaseNet):
    @classmethod
    @property
    def name(cls) -> str:
        return "big_net"

    def _define_net(
        self, state_shape: tuple[int, int, int], num_actions: int
    ) -> nn.Sequential:
        channel_dim, x_dim, y_dim = state_shape  # unpack dimensions

        h_out_1 = self._calc_conv_outdim(x_dim, 8, 4, 1)
        w_out_1 = self._calc_conv_outdim(y_dim, 8, 4, 1)
        h_out_2 = self._calc_conv_outdim(h_out_1, 4, 2, 1)
        w_out_2 = self._calc_conv_outdim(w_out_1, 4, 2, 1)
        num_flat_features = h_out_2 * w_out_2

        # adapted from: https://github.com/KaleabTessera/DQN-Atari#dqn-neurips-architecture-implementation
        return nn.Sequential(
            # conv1
            nn.Conv2d(channel_dim, 32, kernel_size=8, stride=4, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(),
            # conv2
            nn.Conv2d(32, 128, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(),
            # fc 1
            nn.Flatten(),
            nn.Linear(128 * num_flat_features, 1024),
            nn.LeakyReLU(),
            # nn.Dropout(0.5),
            # fc 2
            nn.Linear(1024, 256),
            nn.ReLU(),
            # fc 3
            nn.Linear(256, 64),
            nn.ReLU(),
            # fc 4
            nn.Linear(64, 16),
            nn.ReLU(),
            # output
            nn.Linear(16, num_actions),
        )