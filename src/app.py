import datetime
import random
import uuid
from enum import Enum
from typing import Optional
from urllib.parse import quote

from pymongo import MongoClient

from src.env import Env, EnvStage

DB_NAME_TO_URI = {
    "ab_testing": "mongodb+srv://{db_user}:{db_password}@abtesting"
    ".8azxalb.mongodb.net/?retryWrites=true&w=majority"
}


class DbClient:
    """
    A wrapper for the pymongo client and enviromental concerns. There are two ways to
    initialize the client, either by providing the DB URI directly, and including
    the needed credentials, or by providing a valid username and password for a
    user with access to the database.

    Args:
        env_stage (EnvStage): The stage of the environment
        db_name (str): The name of the database, defaults to "ab_testing"
            which contains experimentation models
    """

    def __init__(self, env_stage: EnvStage = EnvStage.DEV, db_name: str = "ab_testing"):
        self.env = Env(env_stage)
        env_db_uri = self.env["MONGO_DB_URI"]
        if env_db_uri is not None:
            self.client = MongoClient(env_db_uri, uuidRepresentation="standard")
            return

        db_uri = DB_NAME_TO_URI[db_name].format(
            db_user=quote(self.env["MONGO_USER"]),
            db_password=quote(self.env["MONGO_PASSWORD"]),
        )  # pylint: disable=W1401
        self.client = MongoClient(db_uri, uuidRepresentation="standard")

    def get_collection(self, db_name: str, collection_name: str):
        """
        Get a collection from the mongo database
        """
        db_with_env = f"{db_name}-{self.env.env_stage.value}"
        db = self.client[db_with_env]
        return db[collection_name]


class ExperimentStatus(Enum):
    """
    The state the experiment is in. Most states are self-explanatory, but "stopped"
    is used when the experiment is stopped for some extraneous reason, where
    resuming would not make sense.
    """

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


class Experiment:
    """
    The root model for AB testing, represents an hypothesis to be tested
    """

    DB_NAME = "ab_testing"
    COLLECTION_NAME = "experiments"

    def __init__(
        self,
        name: str,
        description: str,
        experiment_uuid: Optional[uuid.UUID] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        experiment_variants: Optional[list[uuid.UUID]] = None,
        experiement_status: Optional[ExperimentStatus] = None,
        db: Optional[DbClient] = None,
    ):
        self.name = name
        self.description = description

        if experiment_uuid is None:
            self.experiment_uuid = uuid.uuid4()
        else:
            self.experiment_uuid = experiment_uuid

        self.start_date = start_date
        self.end_date = end_date
        if experiment_variants is None:
            self.experiment_variants = []
        else:
            self.experiment_variants = experiment_variants

        if experiement_status is None:
            self.experiement_status = ExperimentStatus.CREATED
        else:
            self.experiement_status = experiement_status

        if db is not None:
            self.db = db
        else:
            self.db = DbClient()

    def insert(self):
        """
        Save the experiment to the mongo database
        """
        collection = self.db.get_collection(self.DB_NAME, self.COLLECTION_NAME)
        collection.insert_one(
            {
                "name": self.name,
                "description": self.description,
                "experiment_uuid": self.experiment_uuid,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "experiment_variants": self.experiment_variants,
                "experiement_status": self.experiement_status.value,
            }
        )

    def update(self):
        """
        Update the experiment in the mongo database
        """
        collection = self.db.get_collection("ab_testing", "experiments")
        collection.update_one(
            {"experiment_uuid": self.experiment_uuid},
            {
                "$set": {
                    "name": self.name,
                    "description": self.description,
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "experiment_variants": self.experiment_variants,
                    "experiement_status": self.experiement_status.value,
                }
            },
        )

    def get_variant_uuids(self) -> list[uuid.UUID]:
        """
        Get the uuids of the experiment variants
        """
        return self.experiment_variants

    def get_variant_objs(self) -> list["ExperimentVariant"]:
        """
        Get the experiment variants as objects
        """
        return [
            ExperimentVariant.load(variant, self.db)
            for variant in self.get_variant_uuids()
        ]

    def participant_in_experiment(self, participant_uuid: uuid.UUID) -> bool:
        """
        Check if a participant is in the experiment
        """
        variant = self.get_variant_for_participant(participant_uuid)
        return variant is not None

    def get_variant_for_participant(
        self, participant_uuid: uuid.UUID
    ) -> Optional[uuid.UUID]:
        """
        Get the variant for a participant, if they are in the experiment
        """
        for variant_uuid in self.experiment_variants:
            variant = ExperimentVariant.load(variant_uuid, self.db)
            if variant.participant_in_variant(participant_uuid):
                return variant.variant_uuid
        return None

    def get_current_allocations(self) -> dict[uuid.UUID, float]:
        """
        Get the percentage of participants allocated to each variant
        """

        total_participants = 0
        allocations = {}
        for variant in self.get_variant_objs():
            allocations[variant.variant_uuid] = variant.number_of_participants()
            total_participants = sum(allocations.values())

        if total_participants > 0:
            allocations = {
                key: value / total_participants for key, value in allocations.items()
            }
        return allocations

    def get_expected_allocations(self) -> dict[uuid.UUID, float]:
        """
        Get the expected percentage of participants allocated to each variant
        """
        return {
            variant.variant_uuid: variant.allocation
            for variant in self.get_variant_objs()
        }

    def add_participant_to_experiment(self, participant_uuid: uuid.UUID) -> uuid.UUID:
        """
        Add a participant to the experiment
        """
        variant = self.get_variant_for_participant(participant_uuid)
        if variant is None:
            expected_allocations = self.get_expected_allocations()

            variant_allocated = random.choices(
                list(expected_allocations.keys()), list(expected_allocations.values())
            )[0]

            variant = ExperimentVariant.load(variant_allocated, self.db)
            variant.add_participant(participant_uuid)
            variant.update()

            return variant_allocated

        raise Exception("Participant already in experiment")  # pylint: disable=W0719

    def add_variant(self, variant: "ExperimentVariant"):
        """
        Add a variant to the experiment
        """
        self.experiment_variants.append(variant.variant_uuid)

    @staticmethod
    def load(experiment_uuid: uuid.UUID, db: DbClient) -> "Experiment":
        """
        Load an experiment from the mongo database
        """
        collection = db.get_collection(Experiment.DB_NAME, Experiment.COLLECTION_NAME)

        experiment = collection.find_one({"experiment_uuid": experiment_uuid})
        experiment_fields = {
            "name": experiment["name"],
            "description": experiment["description"],
            "experiment_uuid": experiment["experiment_uuid"],
            "start_date": experiment["start_date"],
            "end_date": experiment["end_date"],
            "experiment_variants": experiment["experiment_variants"],
            "experiement_status": ExperimentStatus(experiment["experiement_status"]),
            "db": db,
        }
        return Experiment(**experiment_fields)


class ExperimentVariant:
    """
    A variant/grouping for an experiment
    """

    DB_NAME = "ab_testing"
    COLLECTION_NAME = "experiment_variants"

    def __init__(
        self,
        name: str,
        description: str,
        variant_uuid: Optional[uuid.UUID] = None,
        allocation: Optional[float] = None,
        participants: Optional[list[uuid.UUID]] = None,
        db: Optional[DbClient] = None,
    ):
        self.name = name
        self.description = description

        if variant_uuid is None:
            self.variant_uuid = uuid.uuid4()
        else:
            self.variant_uuid = variant_uuid

        if allocation is None:
            self.allocation = 1.0
        else:
            self.allocation = allocation

        if participants is None:
            self.participants = []
        else:
            self.participants = participants

        if db is not None:
            self.db = db
        else:
            self.db = DbClient()

    def insert(self):
        """
        Save the experiment variant to the mongo database
        """
        collection = self.db.get_collection(self.DB_NAME, self.COLLECTION_NAME)
        collection.insert_one(
            {
                "name": self.name,
                "description": self.description,
                "allocation": self.allocation,
                "participants": self.participants,
                "variant_uuid": self.variant_uuid,
            }
        )

    def update(self):
        """
        Update the experiment variant in the mongo database
        """
        collection = self.db.get_collection(self.DB_NAME, self.COLLECTION_NAME)
        collection.update_one(
            {"variant_uuid": self.variant_uuid},
            {
                "$set": {
                    "name": self.name,
                    "description": self.description,
                    "allocation": self.allocation,
                    "participants": self.participants,
                }
            },
        )

    @staticmethod
    def load(variant_uuid: uuid.UUID, db: DbClient) -> "ExperimentVariant":
        """
        Load an experiment variant from the mongo database
        """
        collection = db.get_collection(
            ExperimentVariant.DB_NAME, ExperimentVariant.COLLECTION_NAME
        )
        variant = collection.find_one({"variant_uuid": variant_uuid})
        variant_fields = {
            "name": variant["name"],
            "description": variant["description"],
            "allocation": variant["allocation"],
            "participants": variant["participants"],
            "variant_uuid": variant["variant_uuid"],
            "db": db,
        }
        return ExperimentVariant(**variant_fields)

    def participant_in_variant(self, participant_uuid: uuid.UUID) -> bool:
        """
        Check if a participant is in the variant
        """
        return participant_uuid in self.participants

    def number_of_participants(self) -> int:
        """
        Get the number of participants in the variant
        """
        return len(self.participants)

    def add_participant(self, participant_uuid: uuid.UUID):
        """
        Add a participant to the variant
        """
        self.participants.append(participant_uuid)


class ExperimentParticipant:
    """
    A participant in an experiment
    """

    DB_NAME = "ab_testing"
    COLLECTION_NAME = "experiment_participants"

    def __init__(
        self,
        participant_uuid: Optional[uuid.UUID] = None,
        db: Optional[DbClient] = None,
    ):
        if participant_uuid is None:
            self.participant_uuid = uuid.uuid4()
        else:
            self.participant_uuid = participant_uuid

        if db is not None:
            self.db = db
        else:
            self.db = DbClient()

    def insert(self):
        """
        Save the experiment participant to the mongo database
        """
        collection = self.db.get_collection(self.DB_NAME, self.COLLECTION_NAME)
        collection.insert_one({"participant_uuid": self.participant_uuid})

    def update(self):
        """
        Update the experiment participant in the mongo database
        """
        collection = self.db.get_collection(self.DB_NAME, self.COLLECTION_NAME)
        collection.update_one(
            {"participant_uuid": self.participant_uuid},
            {"$set": {"participant_uuid": self.participant_uuid}},
        )

    @staticmethod
    def load(participant_uuid: uuid.UUID, db: DbClient) -> "ExperimentParticipant":
        """
        Load an experiment participant from the mongo database
        """
        collection = db.get_collection(
            ExperimentParticipant.DB_NAME, ExperimentParticipant.COLLECTION_NAME
        )
        participant = collection.find_one({"participant_uuid": participant_uuid})
        return ExperimentParticipant(participant["participant_uuid"], db=db)
