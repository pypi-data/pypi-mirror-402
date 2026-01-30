"""Policy wrapper for inference."""

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class PolicyWrapper(ABC):
    """Base wrapper for policy inference."""

    def __init__(self, model_path: Path):
        """
        Initialize the policy wrapper.

        Args:
            model_path: Path to the trained model file (e.g., ONNX, PyTorch, etc.)
        """
        self.model_path = model_path
        self.model = None

    @abstractmethod
    def _load_model(self) -> None:
        """
        Load the model from the specified path.

        This method should initialize self.model with the loaded model.
        Implementation depends on the model format (ONNX, PyTorch, TensorFlow, etc.)
        """

    def preprocess_observations(self, observations: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """
        Preprocess observations before inference.

        Args:
            observations: Raw observations from the environment

        Returns:
            Dict[str, np.ndarray]: Preprocessed observations ready for model input
        """
        return observations

    @abstractmethod
    def __call__(self, observations: dict[str, np.ndarray]) -> np.ndarray:
        """
        Perform inference on the given observations.

        Args:
            observations: Dictionary containing observation tensors.
                         Keys depend on the specific policy implementation.
                         Example: {'actor_obs': np.array([...]), 'estimator_obs': np.array([...])}

        Returns:
            np.ndarray: Policy actions as a numpy array
        """

    def postprocess_actions(self, actions: np.ndarray) -> np.ndarray:
        """
        Postprocess actions after inference (e.g., clipping, scaling).

        Args:
            actions: Raw actions from the model

        Returns:
            np.ndarray: Postprocessed actions ready for execution
        """
        return actions

    def reset(self) -> None:
        """
        Reset the policy state (e.g., hidden states for RNN policies).

        Override this method if your policy maintains internal state.
        """
