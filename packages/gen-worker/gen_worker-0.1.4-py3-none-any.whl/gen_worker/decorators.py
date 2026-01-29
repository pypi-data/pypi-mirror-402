import functools
from typing import Callable, Any, Dict, Optional, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])

class ResourceRequirements:
    """
    Specifies the resource requirements for a worker function.
    """
    def __init__(
        self,
        model_name: Optional[str] = None,
        model_family: Optional[str] = None,
        min_vram_gb: Optional[float] = None,
        recommended_vram_gb: Optional[float] = None,
        requires_gpu: bool = False,
        expects_pipeline_arg: bool = False,
        max_concurrency: Optional[int] = None
        # Add other potential requirements here:
        # e.g., cpu_cores: Optional[int] = None,
        # specific_accelerators: Optional[list[str]] = None,
        # etc.
    ) -> None:
        self.model_name = model_name
        self.model_family = model_family
        self.min_vram_gb = min_vram_gb
        self.recommended_vram_gb = recommended_vram_gb
        self.requires_gpu = requires_gpu
        self.expects_pipeline_arg = expects_pipeline_arg
        self.max_concurrency = max_concurrency
        # Store all defined attributes for easy access
        self._requirements = {k: v for k, v in locals().items() if k != 'self' and v is not None}

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dictionary representation of the defined requirements."""
        return self._requirements

    def __repr__(self) -> str:
        return f"ResourceRequirements({self._requirements})"


def worker_function(
    resources: Optional[ResourceRequirements] = None,
) -> Callable[[F], F]:
    """
    Decorator to mark a function as a worker task and associate resource requirements.

    Args:
        resources: An optional ResourceRequirements object describing the function's needs.
    """
    if resources is None:
        resources = ResourceRequirements() # Default empty requirements

    def decorator(func: F) -> F:
        # Attach metadata directly to the function object.
        # The SDK's runner component will look for these attributes.
        setattr(func, '_is_worker_function', True)
        setattr(func, '_worker_resources', resources)

        # Return the original function, now marked with attributes.
        # Use functools.wraps to preserve original function metadata (like __name__, __doc__)
        # even though we are returning the function itself.
        wrapped = functools.wraps(func)(func)
        return cast(F, wrapped)

    return decorator
