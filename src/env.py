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
        env_path = Path(__file__).parent / f".env.{env_stage.value}"
        self.env_path = env_path
        load_dotenv(dotenv_path=self.env_path)

    def __getitem__(self, key: str) -> str:
        return os.environ.get(key)
