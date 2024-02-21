# pylint: disable=missing-docstring
import uuid
from datetime import datetime, timedelta

import pytest

from src.database.models import (
    Experiment,
    ExperimentParticipant,
    ExperimentStatus,
    ExperimentVariant,
)
from src.database.repository import (
    ExperimentParticipantRepository,
    ExperimentRepository,
    ExperimentVariantRepository,
)
from src.services import (
    AuthService,
    ExperimentService,
    ExperimentVariantService,
    ParticipantService,
)

# Setup some test data
yesterday = datetime.now() - timedelta(days=1)
today = datetime.now()
next_week = datetime.now() + timedelta(days=7)


marvel_participant_uuids = [uuid.uuid4() for _i in range(3)]
marvel_participants: list[ExperimentParticipant] = [
    ExperimentParticipantRepository.create(participant_uuid=uuid)
    for uuid in marvel_participant_uuids
]

dc_participant_uuids = [uuid.uuid4() for _i in range(3)]
dc_participants: list[ExperimentParticipant] = [
    ExperimentParticipantRepository.create(participant_uuid=uuid)
    for uuid in dc_participant_uuids
]
mcu_variant: ExperimentVariant = ExperimentVariantRepository.create(
    name="Marvel",
    description="Movies from the Marvel universe",
    allocation=0.5,
    participants=marvel_participant_uuids,
)
dceu_variant: ExperimentVariant = ExperimentVariantRepository.create(
    name="DC",
    description="Movies from the DC universe",
    allocation=0.5,
    participants=dc_participant_uuids,
)

test_experiment: Experiment = ExperimentRepository.create(
    name="Marvel vs DC",
    description="Testing which movie universe is more popular",
    experiment_variants=[mcu_variant.variant_uuid, dceu_variant.variant_uuid],
)


def test_variant_in_experiment():
    assert ExperimentService.variant_in_experiment(
        test_experiment.experiment_uuid, mcu_variant.variant_uuid
    )
    assert ExperimentService.variant_in_experiment(
        test_experiment.experiment_uuid, dceu_variant.variant_uuid
    )
    assert not ExperimentService.variant_in_experiment(
        test_experiment.experiment_uuid, uuid.uuid4()
    )
    assert not ExperimentService.variant_in_experiment(
        uuid.uuid4(), mcu_variant.variant_uuid
    )


def test_experiment_in_progress():
    assert not ExperimentService.experiment_in_progress(test_experiment.experiment_uuid)
    with pytest.raises(Exception) as e_info:
        ExperimentService.experiment_in_progress(uuid.uuid4())
    assert "Experiment not found" in str(e_info.value)

    misc_experiment: Experiment = ExperimentRepository.create(
        experiment_status=ExperimentStatus.COMPLETED
    )
    assert ExperimentService.experiment_in_progress(misc_experiment.experiment_uuid)

    ExperimentRepository.update(
        misc_experiment.experiment_uuid,
        experiment_status=ExperimentStatus.PAUSED,
    )
    assert ExperimentService.experiment_in_progress(misc_experiment.experiment_uuid)

    ExperimentRepository.update(
        misc_experiment.experiment_uuid,
        experiment_status=ExperimentStatus.STOPPED,
    )
    assert not ExperimentService.experiment_in_progress(misc_experiment.experiment_uuid)


def test_add_variant_to_experiment():
    assert not ExperimentService.add_variant_to_experiment(
        test_experiment.experiment_uuid, mcu_variant.variant_uuid
    )
    assert not ExperimentService.add_variant_to_experiment(
        test_experiment.experiment_uuid, dceu_variant.variant_uuid
    )
    assert not ExperimentService.add_variant_to_experiment(
        test_experiment.experiment_uuid, mcu_variant.variant_uuid
    )

    with pytest.raises(Exception) as e_info:
        ExperimentService.add_variant_to_experiment(
            uuid.uuid4(), mcu_variant.variant_uuid
        )

    assert "Experiment not found" in str(e_info.value)

    misc_experiment: Experiment = ExperimentRepository.create(
        name="Misc",
        description="Testing something else",
    )

    assert ExperimentService.add_variant_to_experiment(
        misc_experiment.experiment_uuid, mcu_variant.variant_uuid
    )
    assert not ExperimentService.add_variant_to_experiment(
        misc_experiment.experiment_uuid, mcu_variant.variant_uuid
    )


def test_participant_in_experiment():
    assert ExperimentService.participant_in_experiment(
        test_experiment.experiment_uuid, marvel_participant_uuids[0]
    )
    assert ExperimentService.participant_in_experiment(
        test_experiment.experiment_uuid, dc_participant_uuids[0]
    )

    assert not ExperimentService.participant_in_experiment(
        test_experiment.experiment_uuid, uuid.uuid4()
    )
    assert not ExperimentService.participant_in_experiment(
        uuid.uuid4(), marvel_participant_uuids[0]
    )


def test_add_participant_to_experiment():
    misc_variant: ExperimentVariant = ExperimentVariantRepository.create(
        name="Misc",
        description="Misc",
    )

    misc_experiment: Experiment = ExperimentRepository.create(
        name="Misc",
        description="Testing something else",
        experiment_variants=[],
    )

    misc_participant: ExperimentParticipant = ExperimentParticipantRepository.create()

    with pytest.raises(Exception) as e_info:
        ExperimentService.add_participant_to_experiment(
            misc_experiment.experiment_uuid, misc_participant.participant_uuid
        )
    assert "No variants in experiment" in str(e_info.value)

    ExperimentService.add_variant_to_experiment(
        misc_experiment.experiment_uuid, misc_variant.variant_uuid
    )

    assert ExperimentService.add_participant_to_experiment(
        misc_experiment.experiment_uuid, misc_participant.participant_uuid
    )
    with pytest.raises(Exception) as e_info:
        ExperimentService.add_participant_to_experiment(
            misc_experiment.experiment_uuid, misc_participant.participant_uuid
        )
    assert "Participant already in experiment" in str(e_info.value)

    with pytest.raises(Exception) as e_info:
        ExperimentService.add_participant_to_experiment(uuid.uuid4(), uuid.uuid4())
    assert "Experiment not found" in str(e_info.value)

    ExperimentRepository.update(
        misc_experiment.experiment_uuid,
        experiment_status=ExperimentStatus.COMPLETED,
    )

    with pytest.raises(Exception) as e_info:
        ExperimentService.add_participant_to_experiment(
            misc_experiment.experiment_uuid, misc_participant.participant_uuid
        )
    assert "Experiment has ended" in str(e_info.value)


def test_get_experiment():
    assert (
        ExperimentService.get_experiment(test_experiment.experiment_uuid)
        == test_experiment
    )
    assert ExperimentService.get_experiment(uuid.uuid4()) is None


def test_get_variant_for_participant():
    marvel_fan = marvel_participants[-1]
    dc_fan = dc_participants[-1]

    assert (
        ExperimentService.get_variant_uuid_for_participant(
            test_experiment.experiment_uuid, marvel_fan.participant_uuid
        )
        == mcu_variant.variant_uuid
    )
    assert (
        ExperimentService.get_variant_uuid_for_participant(
            test_experiment.experiment_uuid, dc_fan.participant_uuid
        )
        == dceu_variant.variant_uuid
    )
    assert (
        ExperimentService.get_variant_uuid_for_participant(
            uuid.uuid4(), marvel_fan.participant_uuid
        )
        is None
    )
    assert (
        ExperimentService.get_variant_uuid_for_participant(
            test_experiment.experiment_uuid, uuid.uuid4()
        )
        is None
    )


def test_start_experiment():
    with pytest.raises(Exception) as e_info:
        ExperimentService.start_experiment(uuid.uuid4())
    assert "Experiment not found" in str(e_info.value)

    misc_experiment: Experiment = ExperimentRepository.create(
        name="Random",
        description="Testing starting an experiment",
        experiment_variants=[],
    )

    assert misc_experiment.start_date is None

    assert (
        ExperimentService.start_experiment(misc_experiment.experiment_uuid)
        == ExperimentStatus.RUNNING
    )
    misc_experiment = ExperimentRepository.read(misc_experiment.experiment_uuid)
    current_start_date = misc_experiment.start_date
    assert current_start_date is not None
    assert misc_experiment.experiment_status == ExperimentStatus.RUNNING

    ExperimentService.start_experiment(misc_experiment.experiment_uuid)
    assert misc_experiment.start_date == current_start_date
    assert misc_experiment.experiment_status == ExperimentStatus.RUNNING

    ExperimentRepository.update(
        misc_experiment.experiment_uuid,
        experiment_status=ExperimentStatus.COMPLETED,
    )

    assert (
        ExperimentService.start_experiment(misc_experiment.experiment_uuid)
        == ExperimentStatus.COMPLETED
    )
    assert misc_experiment.start_date == current_start_date


def test_pause_experiment():
    misc_experiment: Experiment = ExperimentRepository.create(
        name="Random",
        description="Testing pausing an experiment",
        experiment_variants=[],
    )

    with pytest.raises(Exception) as e_info:
        ExperimentService.pause_experiment(uuid.uuid4())
    assert "Experiment not found" in str(e_info.value)

    assert (
        ExperimentService.pause_experiment(misc_experiment.experiment_uuid)
        == ExperimentStatus.CREATED
    )
    ExperimentRepository.update(
        misc_experiment.experiment_uuid,
        experiment_status=ExperimentStatus.PAUSED,
    )

    assert (
        ExperimentService.pause_experiment(misc_experiment.experiment_uuid)
        == ExperimentStatus.PAUSED
    )

    ExperimentRepository.update(
        misc_experiment.experiment_uuid,
        experiment_status=ExperimentStatus.STOPPED,
    )
    assert (
        ExperimentService.pause_experiment(misc_experiment.experiment_uuid)
        == ExperimentStatus.STOPPED
    )


def test_end_experiment():
    misc_experiment: Experiment = ExperimentRepository.create(
        name="Random",
        description="Testing ending an experiment",
        experiment_variants=[],
    )

    with pytest.raises(Exception) as e_info:
        ExperimentService.end_experiment(uuid.uuid4(), ExperimentStatus.COMPLETED)
    assert "Experiment not found" in str(e_info.value)

    assert (
        ExperimentService.end_experiment(
            misc_experiment.experiment_uuid, ExperimentStatus.COMPLETED
        )
        == ExperimentStatus.COMPLETED
    )
    assert (
        ExperimentService.end_experiment(
            misc_experiment.experiment_uuid, ExperimentStatus.STOPPED
        )
        == ExperimentStatus.COMPLETED
    )

    misc_experiment = ExperimentRepository.create()
    assert (
        ExperimentService.end_experiment(
            misc_experiment.experiment_uuid, ExperimentStatus.STOPPED
        )
        == ExperimentStatus.STOPPED
    )


def test_complete_experiment():
    misc_experiment: Experiment = ExperimentRepository.create(
        name="Random",
        description="Testing completing an experiment",
        experiment_variants=[],
    )

    assert (
        ExperimentService.complete_experiment(misc_experiment.experiment_uuid)
        == ExperimentStatus.COMPLETED
    )


def test_stop_experiment():
    misc_experiment: Experiment = ExperimentRepository.create(
        name="Random",
        description="Testing stopping an experiment",
        experiment_variants=[],
    )

    assert (
        ExperimentService.stop_experiment(misc_experiment.experiment_uuid)
        == ExperimentStatus.STOPPED
    )
