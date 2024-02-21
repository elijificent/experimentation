# pylint: disable=broad-exception-raised

"""
Database operations against a single collection
and instance, seperate from application logic.
The repository itself will be used to handle
the application logic of the application, and
allow for more complex queries
"""
import uuid
from enum import Enum
from typing import Optional

from src.database.client import DbClient
from src.database.models import (
    BaseCollectionModel,
    Experiment,
    ExperimentParticipant,
    ExperimentVariant,
    ParticipantToUser,
    User,
)


class GenericCrud:
    """
    Generic CRUD operations collections may use,
    these will lack any specific "business" logic for
    requirements on values, but will be able to handle
    most collections, at least for some operations.
    """

    @classmethod
    def create(
        cls, db: DbClient, model_instance: BaseCollectionModel
    ) -> Optional[uuid.UUID]:
        """
        Create a new model in the database, if a model with the same UUID does not exist. If
        you provide a UUID, it will be used, otherwise a new UUID will be generated.
        """
        collection = db.get_collection(cls.model_class())
        model_dict = model_instance.to_dict()

        if model_instance.uuid is None:
            model_uuid = uuid.uuid4()
        else:
            model_uuid = model_instance.uuid

        if cls.read(db, model_uuid) is not None:
            return None

        model_dict[cls.model_class().UUID_FIELD] = model_uuid
        insert_result = collection.insert_one(model_dict)

        if insert_result.acknowledged and insert_result.inserted_id is not None:
            return model_uuid

        raise Exception("Failed to insert model")

    @classmethod
    def read(cls, db: DbClient, model_uuid: uuid.UUID) -> Optional[BaseCollectionModel]:
        """
        Returns a model from the database, if it exists, given a UUID
        """
        model_class = cls.model_class()  # pylint: disable=invalid-name
        collection = db.get_collection(model_class)
        result = collection.find_one({model_class.UUID_FIELD: model_uuid})

        if result is None:
            return None

        class_fields = model_class.instance_fields()
        filtered_result = {field: result[field] for field in class_fields}

        return model_class(**filtered_result)

    @classmethod
    def update(cls, db: DbClient, model_instance: BaseCollectionModel) -> bool:
        """
        Update a model in the database, if it exists. Returns
        whether the model was updated or not.
        """
        model_class = cls.model_class()
        collection = db.get_collection(model_class)
        model_dict = model_instance.to_dict()
        model_uuid = model_instance.uuid

        del model_dict[model_class.UUID_FIELD]

        if cls.read(db, model_uuid) is None:
            raise Exception("Model does not exist")

        update_result = collection.update_one(
            {model_class.UUID_FIELD: model_uuid},
            {"$set": model_dict},
        )

        if update_result.acknowledged and update_result.modified_count == 1:
            return True

        return False

    @classmethod
    def delete(cls, db: DbClient, model_uuid: uuid.UUID) -> Optional[uuid.UUID]:
        """
        Delete all instances of models with the given UUID
        """
        model_class = cls.model_class()
        collection = db.get_collection(model_class)
        delete_result = collection.delete_many({model_class.UUID_FIELD: model_uuid})

        if delete_result.acknowledged:
            if delete_result.deleted_count == 1:
                return model_uuid
            elif delete_result.deleted_count > 1:
                # This should not happen, but we can convert this into a logged
                # warning, and add a check for this with observability tools
                print("Deleted more than one model")
                return model_uuid
            else:
                return None

        raise Exception("Failed to delete model")

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        """
        Returns the class of the collection
        """
        raise NotImplementedError


class ExperimentCrud(GenericCrud):
    """
    CRUD operations for the experiment collection
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return Experiment


class ExperimentVariantCrud(GenericCrud):
    """
    CRUD operations for the experiment variant collection
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return ExperimentVariant


class ExperimentParticipantCrud(GenericCrud):
    """
    CRUD operations for the experiment participant collection
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return ExperimentParticipant


class UserCrud(GenericCrud):
    """
    CRUD operations for the user collection
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return User


class ParticipantToUserCrud(GenericCrud):
    """
    CRUD operations for the participant to user collection
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return ParticipantToUser


if __name__ == "__main__":
    dev_client = DbClient()
    new_experiment = Experiment(
        name="hello world",
        description="this is a test",
    )
    print("Creating new experiment...")
    new_uuid = ExperimentCrud.create(dev_client, new_experiment)
    print("Created new experiment with UUID:", new_uuid)

    print("Reading new experiment...")
    experiment = ExperimentCrud.read(dev_client, new_uuid)
    print("Read experiment:", experiment.to_dict())
