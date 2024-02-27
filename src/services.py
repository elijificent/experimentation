# pylint: disable=broad-exception-raised

"""
Application specfic logic for working with models.
For example, `add_participant_to_experiment` is
a service function that adds a participant to an experiment,
which only makes sense in the context of an  A/B testing
application, not in the context of generic database models.
"""

import random
import uuid
from datetime import datetime
from typing import Optional, Union

import bcrypt
import requests

from src.database.models import (
    BaseCollectionModel,
    Experiment,
    ExperimentParticipant,
    ExperimentStatus,
    ExperimentVariant,
    FunnelEvent,
    FunnelStep,
    ParticipantToUser,
    User,
)
from src.database.repository import (
    ExperimentParticipantRepository,
    ExperimentRepository,
    ExperimentVariantRepository,
    FunnelEventRepository,
    ParticipantToUserRepository,
    UserRepository,
)


class ExperimentService:
    """
    Service functions for working with experiments
    """

    @staticmethod
    def variant_in_experiment(
        experiment_uuid: uuid.UUID, variant_uuid: uuid.UUID
    ) -> bool:
        """
        Check if a variant is in an experiment
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            return False

        return variant_uuid in experiment.experiment_variants

    @staticmethod
    def add_variant_to_experiment(
        experiment_uuid: uuid.UUID, variant_uuid: uuid.UUID
    ) -> bool:
        """
        Add a variant to an experiment
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            raise Exception("Experiment not found")

        added_successfully = ExperimentRepository.push_variant(
            experiment_uuid, variant_uuid
        )

        return added_successfully

    @staticmethod
    def participant_in_experiment(
        experiment_uuid: uuid.UUID, participant_uuid: uuid.UUID
    ) -> bool:
        """
        Check if a participant is in an experiment
        """
        variant_uuid = ExperimentService.get_variant_uuid_for_participant(
            experiment_uuid, participant_uuid
        )

        return variant_uuid is not None

    @staticmethod
    def add_participant_to_experiment(
        experiment_uuid: uuid.UUID, participant_uuid: uuid.UUID
    ) -> uuid.UUID:
        """
        Add a participant to an experiment. Returns the UUID of
        the variant the participant was assigned to
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            raise Exception("Experiment not found")

        if experiment.experiment_status in [
            ExperimentStatus.STOPPED,
            ExperimentStatus.COMPLETED,
        ]:
            raise Exception("Experiment has ended")

        if len(experiment.experiment_variants) == 0:
            raise Exception("No variants in experiment")

        if ExperimentService.participant_in_experiment(
            experiment_uuid, participant_uuid
        ):
            raise Exception("Participant already in experiment")

        variants = [
            ExperimentVariantService.get_variant(variant_uuid)
            for variant_uuid in experiment.experiment_variants
        ]
        variant_allocations = [variant.allocation for variant in variants]
        if sum(variant_allocations) == 0:
            raise Exception("No allocation for any variant")

        selected_variant = random.choices(variants, weights=variant_allocations)[0]
        ExperimentVariantService.add_participant_to_variant(
            selected_variant.uuid, participant_uuid
        )

        return selected_variant.uuid

    @staticmethod
    def get_experiment(experiment_uuid: uuid.UUID) -> Optional[Experiment]:
        """
        Get an experiment by its UUID
        """
        return ExperimentRepository.read(experiment_uuid)

    @staticmethod
    def get_variant_uuid_for_participant(
        experiment_uuid: uuid.UUID, participant_uuid: uuid.UUID
    ) -> Optional[uuid.UUID]:
        """
        Get the variant uuid a participant is assigned to in an experiment.
        Returns None if the participant is not in the experiment
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            return None

        for variant_uuid in experiment.experiment_variants:
            in_variant = ExperimentVariantService.participant_in_variant(
                variant_uuid, participant_uuid
            )
            if in_variant:
                return variant_uuid
        return None

    @staticmethod
    def experiment_in_progress(experiment_uuid: uuid.UUID) -> bool:
        """
        Check if the experiment is in progress/has ended in a valid state.
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            raise Exception("Experiment not found")

        return experiment.experiment_status in [
            ExperimentStatus.RUNNING,
            ExperimentStatus.PAUSED,
            ExperimentStatus.COMPLETED,
        ]

    @staticmethod
    def start_experiment(experiment_uuid: uuid.UUID) -> ExperimentStatus:
        """
        Attempts to begin an experiment. Returns the new status of the experiment
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            raise Exception("Experiment not found")

        if experiment.experiment_status == ExperimentStatus.RUNNING:
            print("Experiment already running")
            return ExperimentStatus.RUNNING

        if experiment.experiment_status in [
            ExperimentStatus.STOPPED,
            ExperimentStatus.COMPLETED,
        ]:
            print("Experiment has ended")
            return experiment.experiment_status

        if experiment.experiment_status == ExperimentStatus.CREATED:
            updated_experiment: Experiment = ExperimentRepository.update(
                experiment_uuid,
                experiment_status=ExperimentStatus.RUNNING,
                start_date=datetime.now(),
            )
        else:
            updated_experiment: Experiment = ExperimentRepository.update(
                experiment_uuid, experiment_status=ExperimentStatus.RUNNING
            )
        return updated_experiment.experiment_status

    @staticmethod
    def pause_experiment(experiment_uuid: uuid.UUID) -> ExperimentStatus:
        """
        Attempts to pause an experiment. Returns the new status of the experiment
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            raise Exception("Experiment not found")

        if experiment.experiment_status == ExperimentStatus.PAUSED:
            print("Experiment already paused")
            return ExperimentStatus.PAUSED

        if experiment.experiment_status == ExperimentStatus.CREATED:
            print("Experiment has not started")
            return ExperimentStatus.CREATED

        if experiment.experiment_status in [
            ExperimentStatus.STOPPED,
            ExperimentStatus.COMPLETED,
        ]:
            print("Experiment has ended")
            return experiment.experiment_status

        updated_experiment: Experiment = ExperimentRepository.update(
            experiment_uuid, experiment_status=ExperimentStatus.PAUSED
        )
        return updated_experiment.experiment_status

    @staticmethod
    def end_experiment(
        experiment_uuid: uuid.UUID,
        end_state: ExperimentStatus,
    ) -> ExperimentStatus:
        """
        Attempts to move the experiment to a stopped or completed state. Returns the new status of the experiment
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            raise Exception("Experiment not found")

        if experiment.experiment_status in [
            ExperimentStatus.STOPPED,
            ExperimentStatus.COMPLETED,
        ]:
            print("Experiment already ended")
            return experiment.experiment_status

        updated_experiment: Experiment = ExperimentRepository.update(
            experiment_uuid, experiment_status=end_state, end_date=datetime.now()
        )
        return updated_experiment.experiment_status

    @staticmethod
    def stop_experiment(experiment_uuid: uuid.UUID) -> ExperimentStatus:
        """
        Attempts to stop an experiment. Returns the new status of the experiment
        """
        return ExperimentService.end_experiment(
            experiment_uuid, ExperimentStatus.STOPPED
        )

    @staticmethod
    def complete_experiment(experiment_uuid: uuid.UUID) -> ExperimentStatus:
        """
        Attempts to complete an experiment. Returns the new status of the experiment
        """
        return ExperimentService.end_experiment(
            experiment_uuid, ExperimentStatus.COMPLETED
        )


class ExperimentVariantService:
    """
    Service functions for working with experiment variants
    """

    @staticmethod
    def update_allocation(
        variant_uuid: uuid.UUID, new_allocation: float
    ) -> Optional[ExperimentVariant]:
        """
        Update the allocation of an experiment variant
        """
        if new_allocation < 0:
            raise Exception("Allocation must be a positive number")

        return ExperimentVariantRepository.update(
            variant_uuid, allocation=new_allocation
        )

    @staticmethod
    def participant_in_variant(
        variant_uuid: uuid.UUID, participant_uuid: uuid.UUID
    ) -> bool:
        """
        Check if a participant is in an experiment variant
        """
        variant: ExperimentVariant = ExperimentVariantRepository.read(variant_uuid)
        if variant is None:
            return False

        return participant_uuid in variant.participants

    @staticmethod
    def add_participant_to_variant(
        variant_uuid: uuid.UUID, participant_uuid: uuid.UUID
    ) -> bool:
        """
        Add a participant to an experiment variant
        """
        variant: ExperimentVariant = ExperimentVariantRepository.read(variant_uuid)
        if variant is None:
            raise Exception("Variant not found")

        added_successfully = ExperimentVariantRepository.push_participant(
            variant_uuid, participant_uuid
        )

        return added_successfully

    @staticmethod
    def get_variant(variant_uuid: uuid.UUID) -> Optional[ExperimentVariant]:
        """
        Get a variant by its UUID
        """
        return ExperimentVariantRepository.read(variant_uuid)


COMMON_PASSWORDS = {
    "password",
    "123456",
}
INVALID_CHARACTERS = {
    "@",
    "#",
    "%",
    "{",
    "}",
}


class AuthService:
    """
    Service functions for working with users
    """

    @staticmethod
    def create_user(username: str, password: str) -> Optional[User]:
        """
        Create a new user
        """
        if not AuthService.validate_password(password):
            raise Exception("Password does not meet requirements")

        if not AuthService.validate_username(username):
            raise Exception("Username does not meet requirements")

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
        new_user_uuid = uuid.uuid4()

        new_user = UserRepository.create(
            username=username,
            hashed_password=hashed_password,
            random_salt=salt,
            user_uuid=new_user_uuid,
        )

        return new_user

    @staticmethod
    def get_user(user_uuid: uuid.UUID) -> Optional[User]:
        """
        Get a user by their username
        """
        return UserRepository.read(user_uuid)

    @staticmethod
    def validate_auth(user_uuid: uuid.UUID, username: str, password: str) -> bool:
        """
        Validate a user's credentials
        """
        user = AuthService.get_user(user_uuid)
        if user is None:
            return False

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), user.random_salt)
        return hashed_password == user.hashed_password and user.username == username

    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Simple username validation
        """
        if len(username) < 5 or len(username) > 50:
            return False

        if any(char in INVALID_CHARACTERS for char in username):
            return False

        current_user = UserRepository.get_user_by_username(username)
        if current_user is not None:
            return False

        return True

    @staticmethod
    def validate_password(password: str) -> bool:
        """
        Simple password validation
        """
        if len(password) < 8:
            return False

        if password in COMMON_PASSWORDS:
            return False

        return True

    @staticmethod
    def update_username(user_uuid: uuid.UUID, new_username: str) -> bool:
        """
        Update the username of a user
        """
        if not AuthService.validate_username(new_username):
            raise Exception("Invalid username")

        if AuthService.get_user(user_uuid) is None:
            raise Exception("User not found")

        return UserRepository.update(user_uuid, username=new_username)

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """
        Get a user by their username
        """
        return UserRepository.get_user_by_username(username)


class ParticipantService:
    """
    Service functions for working with participants
    """

    @staticmethod
    def create_participant(participant_uuid: uuid.UUID) -> ExperimentParticipant:
        """
        Create a new participant
        """
        current_participant = ExperimentParticipantRepository.read(participant_uuid)
        if current_participant is not None:
            raise Exception("Participant already exists")

        return ExperimentParticipantRepository.create(participant_uuid=participant_uuid)

    @staticmethod
    def get_participant(participant_uuid: uuid.UUID) -> Optional[ExperimentParticipant]:
        """
        Get a participant by their UUID
        """
        return ExperimentParticipantRepository.read(participant_uuid)

    @staticmethod
    def link_participant_to_user(
        participant_uuid: uuid.UUID, user_uuid: uuid.UUID
    ) -> Optional[BaseCollectionModel]:
        """
        Link a participant to a user
        """
        if participant_uuid is None or user_uuid is None:
            raise Exception("Participant and user UUIDs are required")

        current_linking: ParticipantToUser = ParticipantToUserRepository.read(
            participant_uuid
        )
        if current_linking is not None:
            # this would be pretty bad if it happened
            raise Exception("Participant already linked to a user")

        return ParticipantToUserRepository.create(
            participant_uuid=participant_uuid, user_uuid=user_uuid
        )


class Helpful:
    """
    Helpful methods overall
    """

    @staticmethod
    def build_button_experiment(num_participants: int) -> dict:
        """
        This will create a new experiment with 5 variants
        and num_participants participants. The participants
        will be evenly distributed across the variants.

        Returns a dictionary containing the experiment, the
        participant_uuids, and the variants.
        """
        participant_uuids = [uuid.uuid4() for _i in range(num_participants)]
        for p_uuid in participant_uuids:
            ParticipantService.create_participant(p_uuid)

        variant_names = [
            "red_no_text",
            "red_with_text",
            "blue_no_text",
            "blue_with_text",
            "control",
        ]
        variants: list[ExperimentVariant] = []
        for i, v_name in enumerate(variant_names):
            new_variant = ExperimentVariantRepository.create(
                name=v_name,
                description="variations on how to display the button",
                participants=[
                    participant_uuids[p_index]
                    for p_index in range(num_participants)
                    if p_index % 5 == i
                ],
            )
            variants.append(new_variant)

        experiment = ExperimentRepository.create(
            name="Button Color + Text Experiment",
            description="Increase engagement by changing the color and text of the button",
            experiment_variants=[v.variant_uuid for v in variants],
        )

        return {
            "experiment": experiment,
            "participant_uuids": participant_uuids,
            "variants": variants,
        }

    @staticmethod
    def random_string(length: int) -> str:
        """
        Generate a random string of a given length
        """
        return "".join(
            random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(length)
        )

    @staticmethod
    def load_url_x_times(url: str, x: int) -> None:
        """
        Load a URL x times, useful for creating new experiment
        participants
        """
        for _i in range(x):
            requests.get(url)


class FunnelEventService:
    """
    Service functions for working with funnel events
    """

    @staticmethod
    def create_funnel_event(
        session_uuid: uuid.UUID,
        event_step: FunnelStep,
        event_time: datetime,
        event_uuid: Optional[uuid.UUID] = None,
    ) -> Optional[FunnelEvent]:
        """
        Create a new funnel event
        """
        if event_uuid is None:
            event_uuid = uuid.uuid4()

        new_event = FunnelEventRepository.create(
            session_uuid=session_uuid,
            event_step=event_step,
            event_time=event_time,
            event_uuid=event_uuid,
        )

        return new_event

    @staticmethod
    def attempt_to_link_participant(
        session_uuid: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> bool:
        """
        Attempts to link the provided session uuid to a given user uuid
        """
        if session_uuid is None or user_uuid is None:
            return False

        user = AuthService.get_user(user_uuid)
        if user is not None:
            return (
                ParticipantService.link_participant_to_user(session_uuid, user_uuid)
                is not None
            )
        return False
