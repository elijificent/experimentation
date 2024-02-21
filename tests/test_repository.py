# pylint: disable=missing-docstring

import uuid

import pytest

from src.database.models import Experiment, ExperimentStatus
from src.database.repository import ExperimentRepository


def test_model_class():
    assert ExperimentRepository.model_class() == Experiment


def test_empty_create():
    experiment = ExperimentRepository.create()
    assert experiment is not None
    assert experiment.experiment_uuid is not None


def test_create():
    experiment = ExperimentRepository.create(
        name="hola world",
        description="matrix - red or blue",
    )

    assert experiment.name == "hola world"
    assert experiment.description == "matrix - red or blue"
    assert experiment.experiment_uuid is not None

    with pytest.raises(Exception) as e_info:
        ExperimentRepository.create(bad_field="bad field")

    assert "Invalid field: bad_field" in str(e_info.value)


def test_create_with_uuid():
    new_uuid = uuid.uuid4()
    experiment = ExperimentRepository.create(
        name="howdy world",
        experiment_uuid=new_uuid,
    )
    assert experiment.name == "howdy world"
    assert experiment.experiment_uuid == new_uuid


def test_read():
    experiment = ExperimentRepository.create(
        name="hola world",
        description="matrix - red or blue",
    )
    read_experiment = ExperimentRepository.read(experiment.experiment_uuid)

    assert experiment.name == read_experiment.name
    assert experiment.description == read_experiment.description
    assert experiment.experiment_uuid == read_experiment.experiment_uuid
    assert experiment.experiment_status == read_experiment.experiment_status
    assert experiment.experiment_variants == read_experiment.experiment_variants


def test_update():
    experiment = ExperimentRepository.create(
        name="hola world",
        description="matrix - red or blue",
    )
    updated_experiment = ExperimentRepository.update(
        experiment.experiment_uuid,
        name="farewell world",
        description="red",
        experiment_variants=[uuid.uuid4(), uuid.uuid4()],
        experiment_status="running",
    )

    assert updated_experiment.name == "farewell world"
    assert updated_experiment.description == "red"
    assert updated_experiment.experiment_status == ExperimentStatus.RUNNING
    assert len(updated_experiment.experiment_variants) == 2


def test_update_invalid_field():
    experiment: Experiment = ExperimentRepository.create(
        name="hola world",
        description="matrix - red or blue",
    )
    with pytest.raises(Exception) as e_info:
        ExperimentRepository.update(experiment.experiment_uuid, bad_field="bad field")

    assert "Invalid field: bad_field" in str(e_info.value)


def test_delete():
    experiment = ExperimentRepository.create(
        name="hola world",
        description="matrix - red or blue",
    )
    deleted = ExperimentRepository.delete(experiment.experiment_uuid)
    assert deleted

    no_experiment = ExperimentRepository.read(experiment.experiment_uuid)
    assert no_experiment is None
