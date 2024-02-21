from urllib.parse import quote

from pymongo import MongoClient
from pymongo.collection import Collection

from src.database.models import BaseCollectionModel
from src.env import Env, EnvStage

DB_NAME_TO_URI = {
    "ab_testing": "mongodb+srv://{db_user}:{db_password}@{deployment_domain}/?retryWrites=true&w=majority"
}


class DbClient:
    """
    A wrapper for the pymongo client and enviromental concerns. There are two ways to
    initialize the client, either by providing the DB URI directly, and including
    the needed credentials, or by providing a valid username and password for a
    user with access to the database.

    Args:
        env_stage (EnvStage): The stage of the environment
        deployment (str): The name of the atlas deployment,
            used to grab the client URI, defaults to "ab_testing"
    """

    def __init__(
        self, env_stage: EnvStage = EnvStage.DEV, deployment: str = "ab_testing"
    ):
        self.env = Env(env_stage)
        env_db_uri = self.env["MONGO_DB_URI"]
        if env_db_uri is not None:
            self.client = MongoClient(env_db_uri, uuidRepresentation="standard")
            return

        db_uri = DB_NAME_TO_URI[deployment].format(
            db_user=quote(self.env["MONGO_USER"]),
            db_password=quote(self.env["MONGO_PASSWORD"]),
            deployment_domain=self.env["MONGO_DEPLOYMENT_SUBDOMAIN"],
        )
        self.client = MongoClient(db_uri, uuidRepresentation="standard")

    def get_collection(self, model_instance: BaseCollectionModel) -> Collection:
        """
        Get a collection from the mongo database
        """
        db_name = model_instance.DB_NAME
        collection_name = model_instance.COLLECTION_NAME

        db_with_env = f"{db_name}--{self.env.env_stage.value}"
        db = self.client[db_with_env]
        return db[collection_name]
