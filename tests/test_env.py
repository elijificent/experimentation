# pylint: disable=missing-docstring

# Kind of hard to test this as the environment variables
# also set the database connection string, without mocking.
# This seems a bit unnecessary as writing to the database
# is free, and it means all test are "integration" tests
# by default. Offline testing can be explored in the future,
# or locally through env variables
from src.env import Env
from src.shared import db


def test_init():
    assert db.env.env_stage == Env.load_current_env().env_stage
