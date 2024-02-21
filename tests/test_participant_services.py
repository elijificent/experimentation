# pylint: disable=missing-docstring

import random
import uuid

import pytest

from src.database.models import ExperimentParticipant
from src.database.repository import (
    ExperimentParticipantRepository,
    ParticipantToUserRepository,
)
from src.services import ParticipantService


def test_create_participant():
    new_uuid = uuid.uuid4()
    participant: ExperimentParticipant = ParticipantService.create_participant(new_uuid)

    assert participant is not None
    assert participant.participant_uuid == new_uuid

    with pytest.raises(Exception) as e_info:
        ParticipantService.create_participant(new_uuid)
    assert "Participant already exists" in str(e_info.value)


def test_get_participant():
    new_uuid = uuid.uuid4()
    participant: ExperimentParticipant = ParticipantService.create_participant(new_uuid)

    assert ParticipantService.get_participant(new_uuid) == participant
    assert ParticipantService.get_participant(uuid.uuid4()) is None


def test_link_participant_to_user():
    new_uuid = uuid.uuid4()
    participant: ExperimentParticipant = ParticipantService.create_participant(new_uuid)
    user_uuid = uuid.uuid4()

    assert ParticipantService.link_participant_to_user(
        participant.participant_uuid, user_uuid
    )
    linking = ParticipantToUserRepository.read(participant.participant_uuid)
    assert linking.participant_uuid == participant.participant_uuid
    assert linking.user_uuid == user_uuid

    with pytest.raises(Exception) as e_info:
        ParticipantService.link_participant_to_user(
            participant.participant_uuid, user_uuid
        )
    assert "Participant already linked to a user" in str(e_info.value)

    with pytest.raises(Exception) as e_info:
        ParticipantService.link_participant_to_user(None, user_uuid)
    assert "Participant and user UUIDs are required" in str(e_info.value)

    with pytest.raises(Exception) as e_info:
        ParticipantService.link_participant_to_user(participant.participant_uuid, None)
    assert "Participant and user UUIDs are required" in str(e_info.value)
