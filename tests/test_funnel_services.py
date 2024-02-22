# pylint: disable=missing-docstring


import uuid
from datetime import datetime, timedelta

from src.database.models import FunnelEvent, FunnelStep
from src.database.repository import FunnelEventRepository, ParticipantToUserRepository
from src.services import AuthService, FunnelEventService, Helpful, ParticipantService


def test_create_funnel_event():
    session_uuid = uuid.uuid4()
    event_step = FunnelStep.SIGNING_UP
    event_time = datetime.now() - timedelta(days=1)

    new_event: FunnelEvent = FunnelEventService.create_funnel_event(session_uuid, event_step, event_time)
    assert new_event is not None
    assert new_event.session_uuid == session_uuid
    assert new_event.event_step == event_step
    assert new_event.event_time == event_time
    assert new_event.event_uuid is not None


def test_attempt_to_link_participant():
    assert not FunnelEventService.attempt_to_link_participant(
        uuid.uuid4(), None
    )
    assert not FunnelEventService.attempt_to_link_participant(
        uuid.uuid4(), uuid.uuid4()
    )
    username = Helpful.random_string(10)
    user = AuthService.create_user(username, "test_password")

    participant_uuid = uuid.uuid4()

    assert FunnelEventService.attempt_to_link_participant(
        participant_uuid, user.user_uuid
    )

    linking = ParticipantToUserRepository.read(participant_uuid)
    assert linking is not None
    assert linking.user_uuid == user.user_uuid
