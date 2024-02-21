# pylint: disable=broad-exception-raised

"""
Repository wrapper for crud operations. These can be extended to include
more complex queries and operations, but for now they are simple wrappers
as the application does not require it
"""
import importlib
import uuid
from enum import Enum
from typing import Optional

from src.database.crud import GenericCrud
from src.database.models import (
    BaseCollectionModel,
    Experiment,
    ExperimentParticipant,
    ExperimentVariant,
    ParticipantToUser,
    User,
)
from src.shared import db


class BaseRepository:
    """
    Generic repository that takes key word arguments and
    converts them into models
    """

    @classmethod
    def create(cls, **kwargs) -> Optional[BaseCollectionModel]:
        """
        Create a new model in the database
        """
        model_fields: list[str] = cls.model_class().instance_fields()
        model_class: BaseCollectionModel = cls.model_class()
        for arg in kwargs:
            if arg not in model_fields:
                raise Exception(f"Invalid field: {arg}")

        model_instance = model_class(**kwargs)
        model_uuid = cls.model_crud().create(db, model_instance)

        if model_uuid is None:
            return None

        model_instance.__dict__[model_class.UUID_FIELD] = model_uuid

        return model_instance

    @classmethod
    def read(cls, model_uuid: uuid.UUID) -> Optional[BaseCollectionModel]:
        """
        Returns a model from the database, if it exists, given a UUID
        """
        return cls.model_crud().read(db, model_uuid)

    @classmethod
    def update(cls, model_uuid: uuid.UUID, **kwargs) -> Optional[BaseCollectionModel]:
        """
        Update a model in the database
        """
        model_fields: list[str] = cls.model_class().instance_fields()
        current_instance = cls.read(model_uuid)

        for arg, arg_value in kwargs.items():
            if arg not in model_fields or arg == cls.model_class().UUID_FIELD:
                raise Exception(f"Invalid field: {arg}")

            if isinstance(arg_value, Enum):
                current_instance.__dict__[arg] = arg_value.value
            else:
                current_instance.__dict__[arg] = arg_value

        update_success = cls.model_crud().update(db, current_instance)
        if update_success:
            # Update does not work well with enums, so we need to read the model again
            # and allow the model to convert the enum to the correct type
            return cls.read(model_uuid)

        return None

    @classmethod
    def delete(cls, model_uuid: uuid.UUID) -> bool:
        """
        Delete a model from the database
        """
        return cls.model_crud().delete(db, model_uuid)

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        """
        Returns the class of the model
        """
        raise NotImplementedError

    @classmethod
    def model_crud(cls) -> GenericCrud:
        """
        Returns the CRUD class of the model
        """
        module = importlib.import_module("src.database.crud")
        crud_class_name = f"{cls.model_class().__name__}Crud"

        return getattr(module, crud_class_name)


class ExperimentRepository(BaseRepository):
    """
    Repository for the experiment collection
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return Experiment

    @classmethod
    def push_variant(cls, experiment_uuid: uuid.UUID, variant_uuid: uuid.UUID) -> bool:
        """
        Push a variant to the variants list of an experiment. It uses
        the $addToSet operator to ensure that the variant is not added more than once
        """
        update_result = db.get_collection(cls.model_class()).update_one(
            {cls.model_class().UUID_FIELD: experiment_uuid},
            {"$addToSet": {"experiment_variants": variant_uuid}},
        )

        if update_result.modified_count == 1:
            return True

        return False


class ExperimentVariantRepository(BaseRepository):
    """
    Repository for the experiment variant collection

    TODO: Make sure that each variant is unique to an experiment.
        This is not difficult, but would require a either a new index,
        or more validation in the code
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return ExperimentVariant

    @classmethod
    def push_participant(
        cls, variant_uuid: uuid.UUID, participant_uuid: uuid.UUID
    ) -> bool:
        """
        Push a participant to the participants list of an experiment variant. It uses
        the $addToSet operator to ensure that the participant is not added more than once
        """
        update_result = db.get_collection(cls.model_class()).update_one(
            {cls.model_class().UUID_FIELD: variant_uuid},
            {"$addToSet": {"participants": participant_uuid}},
        )

        if update_result.modified_count == 1:
            return True

        return False


class ExperimentParticipantRepository(BaseRepository):
    """
    Repository for the experiment participant collection
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return ExperimentParticipant


class UserRepository(BaseRepository):
    """
    Repository for the user collection
    """

    @classmethod
    def get_user_by_username(cls, username: str) -> Optional[User]:
        """
        Get a user by their username
        """
        user = db.get_collection(cls.model_class()).find_one({"username": username})
        if user is not None:
            return cls.model_crud().read(db, user["user_uuid"])

        return None

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return User


class ParticipantToUserRepository(BaseRepository):
    """
    Repository for the participant to user collection
    """

    @classmethod
    def model_class(cls) -> BaseCollectionModel:
        return ParticipantToUser


if __name__ == "__main__":
    experiment = ExperimentRepository.create(
        name="Test Experiment",
        description="This is a test experiment",
    )
    print(experiment)

    ExperimentRepository.update(
        experiment.experiment_uuid, description="This is an updated test experiment"
    )

    experiment = ExperimentRepository.read(experiment.experiment_uuid)
    print(experiment)
