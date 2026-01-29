from dataclasses import dataclass

@dataclass
class Size:
    """Represents the size of a pixel format.

    Attributes:
        sizes (list[int]): A list of sizes for each channel.
    """
    sizes: list[int]
    def __post_init__(self) -> None:
        """Check that the sizes are all coherent."""
    def __len__(self) -> int:
        """Returns the number of sizes.

        Returns:
            int: The number of sizes.
        """
    def __getitem__(self, item: int) -> int:
        """Gets the size at the specified index.

        Args:
            item (int): The index of the size to retrieve.

        Returns:
            int: The size at the specified index.
        """
    def __eq__(self, other: object) -> bool:
        """Checks if two Size instances are equal.

        Args:
            other: The other Size instance to compare.

        Returns:
            bool: True if the instances are equal, False otherwise.
        """
    def designation(self) -> str:
        """Computes the designation string for the Size instance.

        Returns:
            str: The designation string.
        """
    @staticmethod
    def from_designation(designation: str, number_of_channels: int) -> tuple['Size', str] | None:
        """Creates a Size instance from a designation string.

        Args:
            designation (str): The designation string.
            number_of_channels (int): The number of channels.

        Returns:
            Optional[tuple[Size, str]]: A tuple containing the Size instance and the remaining substring.
        """
