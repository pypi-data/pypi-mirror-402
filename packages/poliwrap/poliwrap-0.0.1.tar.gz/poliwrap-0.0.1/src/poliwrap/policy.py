"""Policy wrapper for inference."""

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch


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


class ONNXPolicyWrapper(PolicyWrapper):
    """Wrapper for ONNX policies."""

    def __init__(self, model_path: Path) -> None:
        """Initialize the ONNX policy wrapper."""
        super().__init__(model_path)
        self._load_model()

    def _load_model(self) -> None:
        self.model = ort.InferenceSession(self.model_path, providers=ort.get_available_providers())
        self.input_names = [inp.name for inp in self.model.get_inputs()]
        self.output_names = [out.name for out in self.model.get_outputs()]

    def __call__(self, obs: dict[str, np.ndarray]) -> np.ndarray:
        # Preprocess observations
        obs = self.preprocess_observations(obs)
        # Run inference
        actions = self.model.run(
            self.output_names,
            {inp.name: obs[inp.name] for inp in self.model.get_inputs()},
        )
        # Postprocess actions (inherited method can be overridden)
        return self.postprocess_actions(actions)


class PytorchPolicyWrapper(PolicyWrapper):
    """Wrapper for Pytorch policies."""

    def __init__(self, model_path: Path) -> None:
        """Initialize the Pytorch policy wrapper."""
        super().__init__(model_path)
        self._load_model()

    def _load_model(self) -> None:
        self.device = torch.device(torch.accelerator.current_accelerator())
        self.model = torch.load(self.model_path, map_location=self.device)
        self.model.eval()
        self.model = torch.compile(self.model)

    def __call__(self, obs: dict[str, torch.Tensor]) -> torch.Tensor:
        # Preprocess observations
        obs = {k: v.to(self.device) for k, v in obs.items()}
        # Run inference
        with torch.no_grad():
            actions = self.model(**obs)
        # Postprocess actions (inherited method can be overridden)
        return actions
