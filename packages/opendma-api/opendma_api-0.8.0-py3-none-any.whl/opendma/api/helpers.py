#
# Basic classes and exceptions used in OpenDMA.
# This file is auto-generated.
#

from typing import TypeVar, Optional, Any
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime



from enum import Enum

class OdmaType(Enum):
    STRING = 1
    INTEGER = 2
    SHORT = 3
    LONG = 4
    FLOAT = 5
    DOUBLE = 6
    BOOLEAN = 7
    DATETIME = 8
    BINARY = 9
    REFERENCE = 10
    CONTENT = 11
    ID = 100
    GUID = 101

    def to_string(self) -> str:
        """
        Returns the string representation of this type.
        """
        return self.name.lower()

    @staticmethod
    def from_string(value: str) -> "OdmaType":
        """
        Parse string representation into this OdmaType enum (case-insensitive).
        Raises ValueError if the value does not match any OdmaType.
        """
        try:
            return OdmaType[value.upper()]
        except KeyError:
            raise ValueError(f"Invalid string representation of OdmaType: '{value}'")


class OdmaQName:
    """
    Represents a qualified name in OpenDMA, consisting of a namespace and a name.

    Both the namespace and the name must not be empty, and they are immutable after creation.
    """

    def __init__(self, namespace: str, name: str) -> None:
        """
        Constructs an OdmaQName object with the specified namespace and name.

        :param namespace: The namespace part of the qualified name. Must not be empty.
        :param name: The name part of the qualified name. Must not be empty.
        :raises ValueError: If either the namespace or name is empty.
        """
        if not namespace.strip():
            raise ValueError("Namespace must not be empty")
        if not name.strip():
            raise ValueError("Name must not be empty")
        if ':' in name:
            raise ValueError("Name must not contain colon ':' character")
        if namespace.startswith(':') or namespace.endswith(':') or '::' in namespace:
            raise ValueError("Segments in Namespace must have at least 1 character")

        self._namespace = namespace
        self._name = name

    @property
    def namespace(self) -> str:
        """
        Gets the namespace part of the qualified name.

        :return: The namespace string.
        """
        return self._namespace

    @property
    def name(self) -> str:
        """
        Gets the name part of the qualified name.

        :return: The name string.
        """
        return self._name

    def __eq__(self, other) -> bool:
        """
        Compares two OdmaQName objects for equality.
        Two OdmaQName objects are considered equal if their namespace and name are both equal.

        :param other: The OdmaQName object to compare with.
        :return: True if the objects are equal, otherwise False.
        """
        if isinstance(other, OdmaQName):
            return self.namespace == other.namespace and self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash((self.namespace, self.name))

    def __str__(self) -> str:
        """
        Returns a string representation of the OdmaQName object.
        The format is "namespace:name".

        :return: The string representation of this OdmaQName.
        """
        return f"{self.namespace}:{self.name}"

    def __repr__(self):
        """
        Returns a string representation for debugging purposes of the OdmaQName object.
        The format is "namespace:name".

        :return: The debug string representation of this OdmaQName.
        """
        return str(self)

    @staticmethod
    def from_string(qname_str: str) -> "OdmaQName":
        """
        Parses a string in the format 'namespace:name' into an OdmaQName instance.

        :param qname_str: A string in the format 'namespace:name'
        :return: An OdmaQName instance
        :raises ValueError: If the input does not contain a valid string representation of a qualified name
        """

        if ':' not in qname_str:
            raise ValueError(f"Invalid OdmaQName format (missing colon): '{qname_str}'")

        namespace, name = qname_str.rsplit(':', 1)

        if not namespace.strip():
            raise ValueError(f"Namespace must not be empty in OdmaQName: '{qname_str}'")

        if not name.strip():
            raise ValueError(f"Name must not be empty in OdmaQName: '{qname_str}'")

        return OdmaQName(namespace.strip(), name.strip())


class OdmaId:
    """
    Represents a unique identifier for an OdmaObject in an OdmaRepository.
    """

    def __init__(self, id: str) -> None:
        """
        Constructs an OdmaId with the specified ID.

        :param id: The unique identifier string. Must not be empty.
        :raises ValueError: If the id is empty.
        """
        if not id or id.strip() == "":
            raise ValueError("ID must not be empty")
        self._id = id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OdmaId):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __str__(self) -> str:
        return self._id

    def __repr__(self):
        return str(self)
 

class OdmaGuid:
    """
    OdmaGuid represents a globally unique object identifier for an OdmaObject.
    It combines the OdmaId of the object with the OdmaId of the repository.
    This class is immutable and thread-safe.
    """

    def __init__(self, object_id: OdmaId, repository_id: OdmaId):
        """
        Constructs an OdmaGuid with the specified obejct_id and repository_id.

        :param object_id: The OdmaId of the object. Must not be None.
        :param repository_id: The OdmaId of the repository. Must not be null.
        :raises ValueError: If the object_id or repository_id is missing.
        """
        if object_id is None:
            raise ValueError("objectId must not be null")
        if repository_id is None:
            raise ValueError("repositoryId must not be null")
        self._object_id = object_id
        self._repository_id = repository_id

    @property
    def object_id(self):
        """
        Returns the OdmaId of the object.
        
        :return: The OdmaId of the object.
        """
        return self._object_id

    @property
    def repository_id(self):
        """
        Returns the OdmaId of the repository.
        
        :return: The OdmaId of the repository.
        """
        return self._repository_id

    def __eq__(self, other):
        if isinstance(other, OdmaGuid):
            return (self._object_id == other._object_id and
                    self._repository_id == other._repository_id)
        return False

    def __hash__(self):
        return hash((self._object_id, self._repository_id))

    def __str__(self):
        return f"`{self._object_id}` in `{self._repository_id}`"

    def __repr__(self):
        return str(self)


class OdmaException(Exception):
    """
    OdmaException is the base class for all exceptions related to the OpenDMA framework.
    """

    def __init__(self, message="An error occurred in OpenDMA"):
        """
        Initialize the OdmaException with an error message.
        
        :param message: The error message describing the exception (default: "An error occurred in OpenDMA").
        """
        super().__init__(message)


class OdmaObjectNotFoundException(OdmaException):
    """
    Exception raised when an OpenDMA implementation is unable to locate the requested object.
    """

    def __init__(self, repositoryId=None, objectId=None, message=None):
        """
        Initialize the OdmaObjectNotFoundException with an error message and IDs.
        
        :param repositoryId: The unique identifier of the repository (optional).
        :param objectId: The unique identifier of the object that was not found or null, if the repository does not exist (optional).
        :param message: Custom error message (optional).
        """
        self._repositoryId = repositoryId
        self._objectId = objectId
        if message is None:
            if objectId is None:
                message = f"Repository not found: {repositoryId}" if repositoryId else "Object not found"
            else:
                message = f"Object `{objectId}` not found in repository `{repositoryId}`" if repositoryId else "Object not found: `{objectId}`"
        super().__init__(message)

    def get_repository_id(self):
        """
        Retrieve the unique identifier of the repository.
        
        :return: The ID of the repository.
        """
        return self._repositoryId

    def get_object_id(self):
        """
        Retrieve the unique identifier of the object that was not found or None, if the repository does not exist.
        
        :return: The ID of the object that was not found or None, if the repository does not exist.
        """
        return self._objectId


class OdmaPropertyNotFoundException(OdmaException):
    """
    Exception raised when the OpenDMA implementation is unable to locate the requested property.
    
    This exception stores the `qname` of the missing property.
    """

    def __init__(self, propertyName=None, message=None):
        """
        Initialize the OdmaPropertyNotFoundException with an error message and a qualified name.
        
        :param propertyName: The qualified name of the property that was not found (optional).
        :param message: Custom error message (optional).
        """
        self._propertyName = propertyName
        if message is None:
            message = f"Property not found: {propertyName}" if propertyName else "Property not found"
        super().__init__(message)

    def get_property_name(self):
        """
        Retrieve the qualified name of the property that was not found.
        
        :return: The QName of the missing property.
        """
        return self._propertyName


class OdmaInvalidDataTypeException(OdmaException):
    """
    Exception raised when the provided data type does not match the expected data type.
    """

    def __init__(self, message="Invalid data type provided"):
        """
        Initialize the OdmaInvalidDataTypeException with an error message.
        
        :param message: The error message describing the exception (default: "Invalid data type provided").
        """
        super().__init__(message)


class OdmaAccessDeniedException(OdmaException):
    """
    Exception raised when the current user context does not have sufficient permissions for an operation in OpenDMA.
    """

    def __init__(self, message="Access denied: insufficient permissions"):
        """
        Initialize the OdmaAccessDeniedException with an error message.
        
        :param message: The error message describing the exception (default: "Access denied: insufficient permissions").
        """
        super().__init__(message)


class OdmaQuerySyntaxException(OdmaException):
    """
    Exception raised when a query in the OpenDMA framework is syntactically incorrect.
    """

    def __init__(self, message="Query syntax error in OpenDMA"):
        """
        Initialize the OdmaQuerySyntaxException with an error message.
        
        :param message: The error message describing the exception (default: "Query syntax error in OpenDMA").
        """
        super().__init__(message)


class OdmaServiceException(OdmaException):
    """
    Exception raised when the backend service failed.
    """

    def __init__(self, message="Backend service failed"):
        """
        Initialize the OdmaServiceException with an error message.
        
        :param message: The error message describing the exception (default: "Backend service failed").
        """
        super().__init__(message)


class OdmaAuthenticationException(OdmaException):
    """
    Exception raised when the provided credentials are invalid, authentication fails or the session has expired.
    """

    def __init__(self, message="Credentials are invalid, authentication has failed or the session has expired"):
        """
        Initialize the OdmaAuthenticationException with an error message.
        
        :param message: The error message describing the exception (default: "Credentials are invalid, authentication has failed or the session has expired").
        """
        super().__init__(message)
