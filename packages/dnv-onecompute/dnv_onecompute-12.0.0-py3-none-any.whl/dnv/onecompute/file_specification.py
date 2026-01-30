"""Module for the FileSpecification class, representing a file's location and storage details."""

from dataclasses import dataclass

from dnv.onecompute.flowmodel import TypeMeta


@dataclass(init=True)
class FileSpecification(TypeMeta):
    """
    A class representing a file specification, which includes information about whether the file
    is located in a shared folder, its filename, and the directory in which it is stored.
    """

    sharedfolder: bool
    """
    Gets or sets a boolean value indicating whether the file is stored in a shared
    folder.
    """

    filename: str
    """
    Gets or sets the name of the file.
    """

    directory: str
    """
    Gets or sets the name of the directory in which the file is stored.
    """

    @property
    def type(self) -> str:
        """
        Retrieves the type. Included for compatibility with TypeMeta-inherited classes.
        """
        return ""
