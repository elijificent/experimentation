# pylint: disable=missing-docstring

import uuid

import pytest

from src.database.models import Experiment, ExperimentStatus
from src.database.repository import (
    ExperimentParticipantRepository,
    ExperimentRepository,
    ExperimentVariantRepository,
)
from src.interface import ExperimentInterface
from src.services import ExperimentService, ExperimentVariantService, ParticipantService


def build_full_basic_experiment() -> dict:
    participant_uuids = [uuid.uuid4() for _i in range(12)]
    for p_uuid in participant_uuids:
        ParticipantService.create_participant(p_uuid)

    variant_names = [
        "red_no_text",
        "red_with_text",
        "blue_no_text",
        "blue_with_text",
        "control",
    ]
    variants = []
    for i, v_name in enumerate(variant_names):
        new_variant = ExperimentVariantRepository.create(
            name=v_name,
            description="variations on how to display the button",
            participants=[
                participant_uuids[p_index] for p_index in range(12) if p_index % 5 == i
            ],
        )
        variants.append(new_variant)

    experiment = ExperimentRepository.create(
        name="Button Color + Text Experiment",
        description="Change the color and text of the button",
        experiment_variants=[v.variant_uuid for v in variants],
    )

    return {
        "experiment": experiment,
        "participant_uuids": participant_uuids,
        "variants": variants,
    }


def test_get_variant_name():
    with pytest.raises(Exception) as e_info:
        ExperimentInterface.get_variant_name(uuid.uuid4(), uuid.uuid4())
    assert "Experiment not found" in str(e_info.value)

    stopped_experiment_uuid = uuid.uuid4()
    _stopped_experiment = ExperimentRepository.create(
        experiment_uuid=stopped_experiment_uuid,
        experiment_status=ExperimentStatus.STOPPED,
    )
    assert (
        ExperimentInterface.get_variant_name(stopped_experiment_uuid, uuid.uuid4())
        == "default"
    )

    experiment_vals = build_full_basic_experiment()
    experiment = experiment_vals["experiment"]
    participant_uuids = experiment_vals["participant_uuids"]
    variants = experiment_vals["variants"]

    for p_uuid in participant_uuids:
        assert (
            ExperimentInterface.get_variant_name(experiment.experiment_uuid, p_uuid)
            == "default"
        )

    ExperimentService.start_experiment(experiment.experiment_uuid)

    for i, p_uuid in enumerate(participant_uuids):
        assert (
            ExperimentInterface.get_variant_name(experiment.experiment_uuid, p_uuid)
            == variants[i % 5].name
        )
