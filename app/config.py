from dataclasses import dataclass


@dataclass
class Config:
    """A configuration object holding all parameters for an experiment."""

    # training parameters
    max_episodes: int = 5_000
    start_epsilon_decay: int = 1_000

    # environment parameters
    frame_skip: int = 4
    input_dim: int = 64
    frame_stack_gap: int = 2
    step_penalty: float = 0.01

    # agent parameters
    agent_name: str = "double_dqn_cnn"
    load_agent: bool = False
    alpha: float = 0.0001
    epsilon_min: float = 0.1
    gamma: float = 0.999  # discount factor gamma
    memory_size: int = 5_000
    batch_size: int = 32
    epochs: int = 1

    # extra agent parameters
    target_net_update_interval: int = 1024

    # save parameter
    model_save_interval: int = 2048
    video_record_interval: int = 2048

    # debugging
    verbose: bool = False
    save_state_img: bool = False
