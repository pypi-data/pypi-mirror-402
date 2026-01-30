from pathlib import Path
from typing import Union
from earthscope_sdk.client.dropoff.models import DropoffCategory


class Validator:
    """
    A class that handles file validation for dropoff files.
    """

    def __init__(self, path: Path, category: Union[str, DropoffCategory]):
        self.path = path.expanduser().resolve()
        self.category = (
            DropoffCategory(category) if isinstance(category, str)
            else category
        )

    def validate_basics(self) -> None:
        """
        Perform basic client side validation.
        Checks if the file exsist and it is non-empty.
        """
        if not self.path.exists():
            raise FileNotFoundError(f"Path {self.path} does not exist.")
        if not self.path.is_file():
            raise ValueError(f"Path {self.path} is not a file.")
        if self.path.stat().st_size == 0:
            raise ValueError(f"Path {self.path} is empty.")

    def validate_miniseed(self) -> None:
        """
        Validate that the file is in valid MiniSEED format.
        Raises ValueError if invalid.
        """
        try:
            from pymseed import MS3Record
        except ImportError as e:
            raise ImportError(
                "pymseed is required for MiniSEED validation. "
                "Please install it via 'pip install pymseed'."
            ) from e

        try:
            for _ in MS3Record.from_file(
                str(self.path),
                unpack_data=True,
                skip_not_data=True
            ):
                pass
        except (OSError, IOError) as e:
            raise ValueError(
                f"Could not open file {self.path} for MiniSEED validation: {e}"
            ) from e
        except Exception as e:
            raise ValueError(
                f"File {self.path} is not a valid MiniSEED format: {e}"
            ) from e

    def validate_all(self) -> None:
        """
        Run all validations for a given file based on category.
        Raises ValueError if any validation fails.
        """
        self.validate_basics()
        if self.category == "miniseed":
            self.validate_miniseed()
        # Additional categories and their validations can be added here.
