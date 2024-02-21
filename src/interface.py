# pylint: disable=broad-exception-raised
"""
Functionality that will be used by the flask app
to interact with the framework
"""

import uuid

from src.database.models import Experiment, ExperimentStatus
from src.database.repository import ExperimentRepository
from src.services import ExperimentService, ExperimentVariantService


class ExperimentInterface:
    """
    How the server would interact with the experiment
    """

    @staticmethod
    def experiment_in_progress(experiment_uuid: uuid.UUID) -> bool:
        """
        Check if the experiment is in progress/has ended in a valid state.
        """
        return ExperimentService.experiment_in_progress(experiment_uuid)

    @staticmethod
    def get_variant_name(
        experiment_uuid: uuid.UUID, participant_uuid: uuid.UUID
    ) -> str:
        """
        Get the variant name for the participant
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if experiment is None:
            raise Exception("Experiment not found")

        if not ExperimentInterface.experiment_in_progress(experiment_uuid):
            return "default"

        if ExperimentService.participant_in_experiment(
            experiment_uuid, participant_uuid
        ):

            variant_uuid = ExperimentService.get_variant_uuid_for_participant(
                experiment_uuid, participant_uuid
            )
            return ExperimentVariantService.get_variant(variant_uuid).name

        if experiment.experiment_status in [
            ExperimentStatus.COMPLETED,
            ExperimentStatus.PAUSED,
        ]:
            return "default"

        new_variant_uuid = ExperimentService.add_participant_to_experiment(
            experiment_uuid, participant_uuid
        )
        return ExperimentVariantService.get_variant(new_variant_uuid).name
