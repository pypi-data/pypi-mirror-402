"""ONNX policy wrapper for inference."""

from pathlib import Path

import numpy as np
import onnxruntime as ort

from poliwrap.policy import PolicyWrapper


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
