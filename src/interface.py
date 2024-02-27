# pylint: disable=broad-exception-raised
"""
Functionality that will be used by the flask app
to interact with the framework
"""

import uuid
from typing import Optional

from src.database.models import Experiment, ExperimentStatus, ExperimentVariant
from src.database.repository import ExperimentRepository, ExperimentVariantRepository
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

    @staticmethod
    def get_experiment_summary(experiment_uuid: uuid.UUID) -> dict:
        """
        Get the summary of the experiment
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)

        if not experiment:
            return {}

        variants: list[ExperimentVariant] = [
            ExperimentVariantService.get_variant(variant_uuid)
            for variant_uuid in experiment.experiment_variants
        ]
        variant_to_participants = {
            variant.variant_uuid: len(variant.participants) for variant in variants
        }
        total_allocation = sum(variant.allocation for variant in variants)

        return {
            "experiment": ExperimentRepository.read(experiment_uuid),
            "variants": variants,
            "variant_to_participants": variant_to_participants,
            "total_allocation": total_allocation,
        }

    @staticmethod
    def get_all_experiments() -> list[Experiment]:
        """
        Get all the experiments
        """
        return ExperimentRepository.get_all()

    @staticmethod
    def get_experiment(experiment_uuid: uuid.UUID) -> Optional[Experiment]:
        """
        Get the experiment
        """
        return ExperimentRepository.read(experiment_uuid)

    @staticmethod
    def update_variant_allocations(
        experiment_uuid: uuid.UUID, allocations: list[float]
    ) -> bool:
        """
        Update the variant allocations with the new values provided.
        The order of the allocations should match the order of the variants UUIDS
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if not experiment:
            return False

        if len(allocations) != len(experiment.experiment_variants):
            return False

        if not ExperimentInterface.experiment_in_progress(experiment_uuid):
            return False

        for i, variant_uuid in enumerate(experiment.experiment_variants):
            ExperimentVariantService.update_allocation(variant_uuid, allocations[i])

        return True
    
    @staticmethod
    def update_variant_descriptions(
        experiment_uuid: uuid.UUID, descriptions: list[str]
    ) -> bool:
        """
        Update the variant descriptions with the new values provided.
        The order of the descriptions should match the order of the variants UUIDS
        """
        experiment: Experiment = ExperimentRepository.read(experiment_uuid)
        if not experiment:
            return False

        if len(descriptions) != len(experiment.experiment_variants):
            return False

        if not ExperimentInterface.experiment_in_progress(experiment_uuid):
            return False

        for i, variant_uuid in enumerate(experiment.experiment_variants):
            ExperimentVariantRepository.update(variant_uuid, description=descriptions[i])

        return True
