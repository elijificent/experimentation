"""
Used for working with environment variables
"""

import os
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv


class EnvStage(Enum):
    """
    Used for setting the environment stage
    """

    DEV = "dev"
    TESTING = "testing"
    PROD = "prod"


class Env:
    """
    Used for working with environment variables
    """

    def __init__(self, env_stage: EnvStage):
        self.env_stage = env_stage
        root_path = Path(__file__).parent.parent
        base_env_path = root_path / ".env"

        if env_stage != EnvStage.PROD:
            env_specific = root_path / f".env.{env_stage.value}"
            load_dotenv(env_specific)
        load_dotenv(base_env_path)

    def __getitem__(self, key: str) -> str:
        return os.environ.get(key)
