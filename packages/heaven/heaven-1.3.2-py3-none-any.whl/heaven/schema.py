import msgspec
from msgspec import Struct, field, Meta as Constraints


class Schema(Struct):
    Field = field



def Field(
    default=msgspec.NODEFAULT,
    *,
    min=None, 
    max=None,
    step=None,
    desc=None,
    example=None,
    format=None,
    error_hint=None,
    **kwargs
) -> Constraints:
    """
    A unified helper for defining msgspec.Meta constraints.
    """
    # Pre-defined Patterns
    if format == "email":
        kwargs["pattern"] = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    elif format == "uuid":
        kwargs["pattern"] = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    elif format == "slug":
        kwargs["pattern"] = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"

    # Metadata
    extra = kwargs.pop("extra_json_schema", {}) or {}
    if example: extra["example"] = example
    if format: extra["format"] = format
    if error_hint: extra["error_hint"] = error_hint
    
    return Constraints(
        # We allow 'min' to stand in for both ge (numbers) and min_length (sequences)
        ge=min, 
        le=max,
        min_length=min,
        max_length=max,
        multiple_of=step,
        # Documentation
        description=desc,
        # Formats & Metadata
        extra_json_schema=extra if extra else None,
        **kwargs
    )
