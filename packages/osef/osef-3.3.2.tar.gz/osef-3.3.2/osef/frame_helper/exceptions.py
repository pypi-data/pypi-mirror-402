"""Custom exceptions for OSEF related errors"""


class FieldError(KeyError):
    """Exception when a field is missing in an OSEF frame."""

    def __init__(self, field_key: str):
        """Raise an exception when a field is missing in an OSEF frame.

        :param field_key: Field key that raised the exception.
        """
        super().__init__(f"OSEF frame does not contain any '{field_key}' field.")


class ObjectIdError(ValueError):
    """Exception when an object ID is not in an OSEF frame."""

    def __init__(self, object_id: int):
        """Raise an exception when an object ID is missing in an OSEF frame.

        :param object_id: Object ID that raised the exception.
        """
        super().__init__(
            f"OSEF frame does not contain any object with ID '{object_id}'."
        )
