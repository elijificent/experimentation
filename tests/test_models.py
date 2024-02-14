# pylint: disable=missing-docstring

import uuid
from datetime import datetime, timedelta

from src.app import (
    DbClient,
    Experiment,
    ExperimentParticipant,
    ExperimentStatus,
    ExperimentVariant,
)
from src.env import EnvStage

yesterday = datetime.now() - timedelta(days=1)
today = datetime.now()
next_week = datetime.now() + timedelta(days=7)

client = DbClient(EnvStage.TESTING)


def test_experiment_initialization():
    experiment = Experiment(
        name="Test Experiment - 101",
        description="This is a test experiment",
        start_date=yesterday,
        end_date=next_week,
        experiment_variants=[uuid.uuid4(), uuid.uuid4(), uuid.uuid4()],
        experiement_status=ExperimentStatus.RUNNING,
        db=client,
    )
    assert experiment.name == "Test Experiment - 101"
    assert experiment.description == "This is a test experiment"
    assert experiment.start_date == yesterday
    assert experiment.end_date == next_week
    assert len(experiment.experiment_variants) == 3
    assert experiment.experiement_status == ExperimentStatus.RUNNING


def test_experiment_initialization_defaults():
    experiment = Experiment(
        name="Test Experiment - 101",
        description="This is a test experiment",
        db=client,
    )

    assert experiment.name == "Test Experiment - 101"
    assert experiment.description == "This is a test experiment"
    assert experiment.start_date is None
    assert experiment.end_date is None
    assert len(experiment.experiment_variants) == 0
    assert experiment.experiement_status == ExperimentStatus.CREATED


def test_experiment_add_variants():
    variant = ExperimentVariant("Test Variant", "This is a test variant", db=client)
    variant.insert()
    another_variant = ExperimentVariant(
        "Another Test Variant", "This is another test variant", db=client
    )
    another_variant.insert()

    experiment = Experiment(
        name="Test Experiment - 101",
        description="This is a test experiment",
        experiment_variants=[],
        db=client,
    )
    experiment.insert()

    experiment = Experiment.load(experiment.experiment_uuid, client)
    assert len(experiment.get_variant_objs()) == 0

    experiment.add_variant(variant)
    experiment.update()

    experiment = Experiment.load(experiment.experiment_uuid, client)
    assert len(experiment.get_variant_objs()) == 1

    experiment.add_variant(another_variant)
    experiment.update()
    assert len(experiment.get_variant_objs()) == 2


def test_participant_in_experiment():
    participant = ExperimentParticipant(db=client)
    participant.insert()
    rando = ExperimentParticipant(db=client)
    rando.insert()

    variant = ExperimentVariant("Test Variant", "This is a test variant", db=client)
    variant.insert()

    experiment = Experiment("Test Experiment", "This is a test experiment", db=client)
    experiment.add_variant(variant)
    experiment.insert()
    experiment.update()

    variant.add_participant(participant.participant_uuid)
    variant.update()

    assert experiment.participant_in_experiment(participant.participant_uuid)
    assert not experiment.participant_in_experiment(rando.participant_uuid)
    assert not experiment.participant_in_experiment(uuid.uuid4())


def test_get_experiment_allocations():
    variant_1 = ExperimentVariant(
        "Test Variant 1", "This is a test variant", allocation=0.5, db=client
    )
    variant_1.insert()
    variant_2 = ExperimentVariant(
        "Test Variant 2", "This is a test variant", allocation=0.5, db=client
    )
    variant_2.insert()

    experiment = Experiment("Test Experiment", "This is a test experiment", db=client)
    experiment.add_variant(variant_1)
    experiment.add_variant(variant_2)
    experiment.insert()

    assert experiment.get_expected_allocations() == {
        variant_1.variant_uuid: 0.5,
        variant_2.variant_uuid: 0.5,
    }


def test_get_current_experiment_allocations():
    variant_1 = ExperimentVariant(
        "Test Variant 1", "This is a test variant", allocation=0.5, db=client
    )
    variant_1.insert()
    variant_2 = ExperimentVariant(
        "Test Variant 2", "This is a test variant", allocation=0.5, db=client
    )
    variant_2.insert()

    for _i in range(5):
        participant = ExperimentParticipant(db=client)
        participant.insert()
        variant_1.add_participant(participant.participant_uuid)
        variant_1.update()

    for _i in range(9):
        participant = ExperimentParticipant(db=client)
        participant.insert()
        variant_2.add_participant(participant.participant_uuid)
        variant_2.update()

    experiment = Experiment("Test Experiment", "This is a test experiment", db=client)
    assert experiment.get_current_allocations() == {}

    experiment.add_variant(variant_1)
    experiment.add_variant(variant_2)
    experiment.insert()

    assert experiment.get_current_allocations() == {
        variant_1.variant_uuid: 5.0 / 14,
        variant_2.variant_uuid: 9.0 / 14,
    }

    participant = ExperimentParticipant(db=client)
    participant.insert()
    variant_2.add_participant(participant.participant_uuid)
    variant_2.update()

    assert experiment.get_current_allocations() == {
        variant_1.variant_uuid: 5.0 / 15,
        variant_2.variant_uuid: 10.0 / 15,
    }

    empty_variant = ExperimentVariant(
        "Empty Variant", "This is an empty variant", db=client
    )
    empty_variant.insert()
    another_empty_variant = ExperimentVariant(
        "Another Empty Variant", "This is another empty variant", db=client
    )
    another_empty_variant.insert()

    experiment = Experiment(
        "Empty Experiment", "This is an empty experiment", db=client
    )
    experiment.add_variant(empty_variant)
    experiment.add_variant(another_empty_variant)
    experiment.insert()
    assert experiment.get_current_allocations() == {
        empty_variant.variant_uuid: 0.0,
        another_empty_variant.variant_uuid: 0.0,
    }


def test_add_participant_to_experiment():
    participant = ExperimentParticipant(db=client)
    participant.insert()

    variant_red = ExperimentVariant(
        "Red Variant", "This is a red variant", allocation=0.5, db=client
    )
    variant_red.insert()
    variant_blue = ExperimentVariant(
        "Blue Variant", "This is a blue variant", allocation=0.5, db=client
    )
    variant_blue.insert()
    variant_purple = ExperimentVariant(
        "Purple Variant", "This is a purple variant", allocation=0.5, db=client
    )
    variant_purple.insert()

    experiment = Experiment("Color Experiment", "This is a color experiment", db=client)
    experiment.add_variant(variant_red)
    experiment.add_variant(variant_blue)
    experiment.add_variant(variant_purple)
    experiment.insert()

    new_variant = experiment.add_participant_to_experiment(participant.participant_uuid)

    assert new_variant in [
        variant_red.variant_uuid,
        variant_blue.variant_uuid,
        variant_purple.variant_uuid,
    ]
