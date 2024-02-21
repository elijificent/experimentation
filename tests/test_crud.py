# pylint: disable=missing-docstring

import uuid

import pytest

from src.database.crud import ExperimentCrud
from src.database.models import Experiment, ExperimentStatus
from src.shared import db


def test_model_class():
    assert ExperimentCrud.model_class() == Experiment


def test_empty_create():
    experiment = Experiment()
    created_uuid = ExperimentCrud.create(db, experiment)
    assert created_uuid is not None


def test_create():
    experiment_uuid = uuid.uuid4()
    new_experiment = Experiment(
        name="hello world",
        description="this is a test",
        experiment_uuid=experiment_uuid,
    )
    no_experiment = ExperimentCrud.read(db, experiment_uuid)
    assert no_experiment is None

    created_uuid = ExperimentCrud.create(db, new_experiment)
    assert created_uuid == experiment_uuid

    experiment: Experiment = ExperimentCrud.read(db, experiment_uuid)
    assert experiment.name == "hello world"
    assert experiment.description == "this is a test"
    assert experiment.experiment_uuid == experiment_uuid
    assert experiment.experiment_status == ExperimentStatus.CREATED
    assert experiment.experiment_variants == []

    another_experiment = Experiment(experiment_uuid=experiment_uuid)
    created_uuid = ExperimentCrud.create(db, another_experiment)
    assert created_uuid is None


def test_read():
    assert ExperimentCrud.read(db, uuid.uuid4()) is None

    new_experiment = Experiment()
    created_uuid = ExperimentCrud.create(db, new_experiment)

    assert created_uuid is not None

    experiment: Experiment = ExperimentCrud.read(db, created_uuid)

    assert experiment is not None
    assert experiment.experiment_uuid == created_uuid
    assert experiment.experiment_status == ExperimentStatus.CREATED


def test_update_no_uuid():
    with pytest.raises(Exception) as e_info:
        ExperimentCrud.update(db, Experiment())

    assert "Model does not exist" in str(e_info.value)


def test_update_no_model():
    with pytest.raises(Exception) as e_info:
        ExperimentCrud.update(db, Experiment(experiment_uuid=uuid.uuid4()))

    assert "Model does not exist" in str(e_info.value)


def test_update():
    new_experiment = Experiment()
    created_uuid = ExperimentCrud.create(db, new_experiment)
    experiment: Experiment = ExperimentCrud.read(db, created_uuid)

    experiment.name = "hello world"
    experiment.description = "this is not a test"
    experiment.experiment_status = "running"
    experiment.experiment_variants = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

    updated = ExperimentCrud.update(db, experiment)

    assert updated

    updated_experiment: Experiment = ExperimentCrud.read(db, created_uuid)

    assert updated_experiment.name == "hello world"
    assert updated_experiment.description == "this is not a test"
    assert updated_experiment.experiment_status == ExperimentStatus.RUNNING
    assert len(updated_experiment.experiment_variants) == 3


def test_delete():
    new_experiment = Experiment()
    created_uuid = ExperimentCrud.create(db, new_experiment)
    experiment: Experiment = ExperimentCrud.read(db, created_uuid)

    assert experiment is not None

    deleted = ExperimentCrud.delete(db, experiment.experiment_uuid)

    assert deleted

    no_experiment = ExperimentCrud.read(db, created_uuid)
    assert no_experiment is None
