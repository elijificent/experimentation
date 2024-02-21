"""
A class that holds the shared models and database client
so that it does not need to be passed around to every
function that needs it
"""

from src.database.database import DbClient
from src.env import Env

env = Env.load_current_env()
db = DbClient(env.env_stage)
