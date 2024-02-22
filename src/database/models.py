"""
Simple models for AB testing, they represent wrappers for data that will be stored
and retrieved from the database.
"""

import datetime
import inspect
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union


@dataclass
class BaseCollectionModel:
    """
    A base collection for all models to inherit from
    """

    @property
    def DB_NAME(self):  # pylint: disable=invalid-name
        """
        The name of the database the collection is in,
        minus the enviroment stage
        """
        raise NotImplementedError

    @property
    def COLLECTION_NAME(self):  # pylint: disable=invalid-name
        """
        The name of the collection
        """
        raise NotImplementedError

    @property
    def UUID_FIELD(self):  # pylint: disable=invalid-name
        """
        The name of the UUID field on the collection, for
        indexing and other operations
        """
        raise NotImplementedError

    @property
    def uuid(self):
        """
        The UUID of the model
        """
        return self.__dict__[self.UUID_FIELD]

    @classmethod
    def instance_fields(cls):
        """
        All the fields that are desired to be stored in the database
        """

        return [
            field for field in cls().__dict__ if field not in cls().__class__.__dict__
        ]

    def to_dict(self):
        """
        Return a dictionary of the fields of the model
        """
        fields_dict = {}

        for field in self.instance_fields():
            value = self.__dict__[field]

            if isinstance(value, Enum):
                fields_dict[field] = value.value
            else:
                fields_dict[field] = value

        return fields_dict

    @classmethod
    def field_types(cls) -> dict[str, Any]:
        """
        Return a dictionary of the field names and their types
        """
        init_signature = inspect.signature(cls.__init__)
        parameter_types = {}

        for parameter in init_signature.parameters.values():
            if parameter.name == "self":
                continue

            parameter_name = parameter.name
            parameter_type = parameter.annotation

            parameter_types[parameter_name] = parameter_type

        return parameter_types

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __str__(self) -> str:
        return self.__repr__()


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


class FunnelStep(Enum):
    """
    Steps in the user 'funnel', how far along the user is
    """

    LANDED = "landed"
    SIGNING_UP = "signing_up"
    SIGNED_UP = "signed_up"


class Experiment(BaseCollectionModel):
    """
    The root model for AB testing, represents an hypothesis to be tested
    """

    DB_NAME = "ab_testing"
    COLLECTION_NAME = "experiments"
    UUID_FIELD = "experiment_uuid"

    def __init__(
        self,
        name: Optional[str] = "",
        description: Optional[str] = "",
        experiment_uuid: Optional[uuid.UUID] = None,
        experiment_variants: Optional[list[uuid.UUID]] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        experiment_status: Union[ExperimentStatus, str] = ExperimentStatus.CREATED,
    ):
        self.name = name
        self.description = description
        self.experiment_uuid = experiment_uuid
        self.start_date = start_date
        self.end_date = end_date

        if isinstance(experiment_status, str):
            self.experiment_status = ExperimentStatus(experiment_status.lower())
        else:
            self.experiment_status = experiment_status

        if experiment_variants is None:
            self.experiment_variants = []
        else:
            self.experiment_variants = experiment_variants


class ExperimentVariant(BaseCollectionModel):
    """
    A variant/grouping for an experiment
    """

    DB_NAME = "ab_testing"
    COLLECTION_NAME = "experiment_variants"
    UUID_FIELD = "variant_uuid"

    def __init__(
        self,
        name: Optional[str] = "",
        description: Optional[str] = "",
        variant_uuid: Optional[uuid.UUID] = None,
        allocation: Optional[float] = 1,
        participants: Optional[list[uuid.UUID]] = None,
    ):
        self.name = name
        self.description = description
        self.variant_uuid = variant_uuid
        self.allocation = allocation

        if participants is None:
            self.participants = []
        else:
            self.participants = participants


class ExperimentParticipant(BaseCollectionModel):
    """
    A participant in an experiment
    """

    DB_NAME = "ab_testing"
    COLLECTION_NAME = "experiment_participants"
    UUID_FIELD = "participant_uuid"

    def __init__(
        self,
        participant_uuid: Optional[uuid.UUID] = None,
    ):
        self.participant_uuid = participant_uuid


class User(BaseCollectionModel):
    """
    A user that has an account in the system
    """

    DB_NAME = "application"
    COLLECTION_NAME = "users"
    UUID_FIELD = "user_uuid"

    def __init__(
        self,
        username: Optional[str] = None,
        hashed_password: Optional[str] = None,
        random_salt: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ):
        self.username = username
        self.hashed_password = hashed_password
        self.random_salt = random_salt
        self.user_uuid = user_uuid


class ParticipantToUser(BaseCollectionModel):
    """
    A mapping of a participant to a user
    """

    DB_NAME = "application"
    COLLECTION_NAME = "participants_to_users"
    UUID_FIELD = "participant_uuid"

    def __init__(
        self,
        participant_uuid: Optional[uuid.UUID] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ):
        self.participant_uuid = participant_uuid
        self.user_uuid = user_uuid


class FunnelEvent(BaseCollectionModel):
    """
    A funnel event
    """

    DB_NAME = "application"
    COLLECTION_NAME = "funnel_events"
    UUID_FIELD = "event_uuid"

    def __init__(
        self,
        session_uuid: Optional[uuid.UUID] = None,
        event_step: Union[FunnelStep, str] = FunnelStep.LANDED,
        event_time: Optional[datetime.datetime] = None,
        event_uuid: Optional[uuid.UUID] = None,
    ):
        self.session_uuid = session_uuid
        self.session_uuid = session_uuid
        self.event_time = event_time
        self.event_uuid = event_uuid

        if isinstance(event_step, str):
            self.event_step = FunnelStep(event_step.lower())
        else:
            self.event_step = event_step
