from typing import Callable, Dict, List, Optional, Tuple

import tensorflow as tf
from absl import logging
from numpy import ndarray

from autofl.datasets import prep
from autofl.fl.participant import ModelProvider, Participant
from autofl.types import KerasWeights

from .aggregate import Aggregator, WeightedAverageAgg


class Coordinator:
    # pylint: disable-msg=too-many-arguments
    def __init__(
        self,
        controller,
        model_provider: ModelProvider,
        participants: List[Participant],
        C: float,
        E: int,
        xy_val: Tuple[ndarray, ndarray],
        aggregator: Optional[Aggregator] = None,
    ) -> None:
        self.controller = controller
        self.model = model_provider.init_model()
        self.participants = participants
        self.C = C
        self.E = E
        self.xy_val = xy_val
        self.aggregator = aggregator if aggregator else WeightedAverageAgg()

    # Common initialization happens implicitly: By updating the participant weights to
    # match the coordinator weights ahead of every training round we achieve common
    # initialization.
    def fit(self, num_rounds: int):
        # Init history
        loss, acc = self.evaluate(self.xy_val)
        history: Dict[str, List[float]] = {
            "acc": [acc],
            "loss": [loss],
            "val_acc": [acc],
            "val_loss": [loss],
        }
        # Train rounds
        for r in range(num_rounds):
            # Determine who participates in this round
            num_indices = abs_C(self.C, self.num_participants())
            indices = self.controller.indices(num_indices)
            logging.info(
                "Round {}/{}: Participants {}".format(r + 1, num_rounds, indices)
            )
            # Train
            self.fit_round_seq(indices)
            # Evaluate
            if self.xy_val:
                loss, acc = self.evaluate(self.xy_val)
                history["loss"].append(loss)  # FIXME
                history["acc"].append(acc)  # FIXME
                history["val_loss"].append(loss)
                history["val_acc"].append(acc)
        return history

    def fit_round_seq(self, indices: List[int]) -> None:
        """Train on each participant sequentially"""
        # Collect training results from the participants of this round
        theta_updates = []
        theta = self.model.get_weights()
        for index in indices:
            theta_update = self._single_step(index, theta)
            theta_updates.append(theta_update)
        # Aggregate training results
        theta_prime = self.aggregator.aggregate(theta_updates)
        # Update own model parameters
        self.model.set_weights(theta_prime)

    def _single_step(self, random_index: int, theta: KerasWeights) -> KerasWeights:
        participant = self.participants[random_index]
        # Train one round on this particular participant:
        # - Push current model parameters to this participant
        # - Train for a number of epochs
        # - Pull updated model parameters from participant
        theta_prime = participant.train_round(theta, epochs=self.E)
        return theta_prime

    def evaluate(self, xy_val: Tuple[ndarray, ndarray]) -> Tuple[float, float]:
        ds_val = prep.init_ds_val(xy_val)
        # Assume the validation `tf.data.Dataset` to yield exactly one batch containing
        # all examples in the validation set
        loss, accuracy = self.model.evaluate(ds_val, steps=1)
        return float(loss), float(accuracy)

    def num_participants(self) -> int:
        return len(self.participants)


def abs_C(C: float, num_participants: int) -> int:
    return int(min(num_participants, max(1, C * num_participants)))


def create_evalueate_fn(
    orig_model: tf.keras.Model, xy_val: Tuple[ndarray, ndarray]
) -> Callable[[KerasWeights], Tuple[float, float]]:
    ds_val = prep.init_ds_val(xy_val)
    model = tf.keras.models.clone_model(orig_model)
    # FIXME refactor model compilation
    model.compile(
        loss=tf.keras.losses.categorical_crossentropy,
        optimizer=tf.keras.optimizers.Adam(),
        metrics=["accuracy"],
    )

    def fn(theta: KerasWeights) -> Tuple[float, float]:
        model.set_weights(theta)
        # Assume the validation `tf.data.Dataset` to yield exactly one batch containing
        # all examples in the validation set
        return model.evaluate(ds_val, steps=1)

    return fn