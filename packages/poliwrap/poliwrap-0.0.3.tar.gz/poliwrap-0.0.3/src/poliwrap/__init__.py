from poliwrap.policy import PolicyWrapper

__all__ = ["PolicyWrapper"]

try:
    from poliwrap.policy import ONNXPolicyWrapper
    __all__.append("ONNXPolicyWrapper")
except ImportError:
    pass

try:
    from poliwrap.policy import PytorchPolicyWrapper
    __all__.append("PytorchPolicyWrapper")
except ImportError:
    pass


def hello() -> str:
    return "Hello from poliwrap!"
