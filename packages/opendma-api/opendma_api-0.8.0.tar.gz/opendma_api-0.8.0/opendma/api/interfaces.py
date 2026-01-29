#
# Abstract classes (ABC) representing OpenDMA objects.
# This file is auto-generated.
#

from typing import TypeVar, Optional, Any
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime

from .helpers import OdmaType, OdmaQName, OdmaId, OdmaGuid
from .helpers import OdmaType, OdmaQName, OdmaId, OdmaGuid, OdmaException, OdmaObjectNotFoundException, OdmaPropertyNotFoundException, OdmaInvalidDataTypeException, OdmaAccessDeniedException, OdmaQuerySyntaxException


TOdmaObject = TypeVar("TOdmaObject", bound="OdmaObject")
TOdmaClass = TypeVar("TOdmaClass", bound="OdmaClass")
TOdmaPropertyInfo = TypeVar("TOdmaPropertyInfo", bound="OdmaPropertyInfo")
TOdmaChoiceValue = TypeVar("TOdmaChoiceValue", bound="OdmaChoiceValue")
TOdmaRepository = TypeVar("TOdmaRepository", bound="OdmaRepository")
TOdmaAuditStamped = TypeVar("TOdmaAuditStamped", bound="OdmaAuditStamped")
TOdmaDocument = TypeVar("TOdmaDocument", bound="OdmaDocument")
TOdmaContentElement = TypeVar("TOdmaContentElement", bound="OdmaContentElement")
TOdmaDataContentElement = TypeVar("TOdmaDataContentElement", bound="OdmaDataContentElement")
TOdmaReferenceContentElement = TypeVar("TOdmaReferenceContentElement", bound="OdmaReferenceContentElement")
TOdmaVersionCollection = TypeVar("TOdmaVersionCollection", bound="OdmaVersionCollection")
TOdmaContainer = TypeVar("TOdmaContainer", bound="OdmaContainer")
TOdmaFolder = TypeVar("TOdmaFolder", bound="OdmaFolder")
TOdmaContainable = TypeVar("TOdmaContainable", bound="OdmaContainable")
TOdmaAssociation = TypeVar("TOdmaAssociation", bound="OdmaAssociation")


from abc import ABC, abstractmethod
from typing import BinaryIO

class OdmaContent(ABC):
    """
    Abstract base class representing Content data type in OpenDMA.
    It provides access to a binary stream and the size of the content.
    """
    
    @abstractmethod
    def get_stream(self) -> BinaryIO:
        """
        Gets the stream to access the content's binary data.
        This should return a file-like object.

        :return: The stream to access the content's binary data.
        """
        pass

    @abstractmethod
    def get_size(self) -> int:
        """
        Gets the size of the content in bytes.

        :return: The size of the content in bytes.
        """
        pass


from abc import ABC, abstractmethod
from typing import BinaryIO

class OdmaSearchResult(ABC):
    """
    Abstract base class representing the result of a search operation.
    It provides access to the objects found and number of objects.
    """
    
    @abstractmethod
    def get_objects(self) -> Iterable[TOdmaObject]:
        """
        Gets the collection of objects found by the search.

        :return: The collection of objects found by the search.
        """
        pass

    @abstractmethod
    def get_size(self) -> int:
        """
        Gets the number of objects found by the search or -1 if the total size is unknown.

        :return: The number of objects found by the search or -1 if the total size is unknown.
        """
        pass



class OdmaSession(ABC):
    """
    A session is the context through which objects can be retrieved from a specific OpenDMA domain.
    It is typically established for a defined account with an instance of a document management system.
    """

    @abstractmethod
    def get_repository_ids(self) -> list[OdmaId]:
        """
        Returns a list of repository OdmaIds the account has access to.

        :return: A list of repository OdmaIds the account has access to
        """
        pass

    @abstractmethod
    def get_repository(self, repository_id: OdmaId) -> "OdmaRepository":
        """
        Returns the OdmaRepository object for the given repository id.

        :param repository_id: The id of the repository to return
        :return: The OdmaRepository object for the given repository id
        :raises OdmaObjectNotFoundException: If a repository with the given id does not exist
                                             or the current account has no access
        """
        pass

    @abstractmethod
    def get_object(
        self,
        repository_id: OdmaId,
        object_id: OdmaId,
        property_names: Optional[list[OdmaQName]]
    ) -> "OdmaObject":
        """
        Returns the object of the given class identified by the given ID in the given repository.

        :param repository_id: The id of the repository to retrieve the object from
        :param object_id: The id of the object to return
        :param property_names: Array of qualified property names to retrieve from the server
                               or None to retrieve all
        :return: The object of the given class identified by the given ID in the given repository
        :raises OdmaObjectNotFoundException: If no object with this ID exists or the account has no access
        """
        pass

    @abstractmethod
    def search(
        self,
        repository_id: OdmaId,
        query_language: OdmaQName,
        query: str
    ) -> OdmaSearchResult:
        """
        Performs a search operation against a repository and returns the result.

        :param repository_id: The id of the repository to retrieve the object from
        :param query_language: The language specifier in which the query is given
        :param query: Search specification in the given query language
        :return: The search result of this operation
        :raises OdmaObjectNotFoundException: If the repository does not exist
        :raises OdmaQuerySyntaxException: If the query string is syntactically incorrect or
                                          the query language is not supported
        """
        pass

    @abstractmethod
    def get_supported_query_languages(self) -> list[OdmaQName]:
        """
        Returns a list of query languages that can be used to search the repository.

        :return: A list of query languages that can be used to search the repository
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Invalidate this session and release all associated resources.
        """
        pass

from typing import Any, Optional
from datetime import datetime
from enum import Enum, auto

class PropertyResolutionState(Enum):
    UNRESOLVED = auto()   # Reading this value requires a round-trip to a back-end system
    IDRESOLVED = auto()   # The OdmaId of the referenced object is immediately available, but reading the object value requires a round-trip to a back-end system
    RESOLVED = auto()     # The value is immediately available

class OdmaProperty(ABC):
    """Abstract base class representing a property of an OdmaObject in the OpenDMA
    architecture. It is always bound in name, data type and cardinality and can not
    change these. If this property is not read only (i.e. isReadOnly() returns false),
    it can change its value by calling the setValue(Object) method. Changes are only
    persisted in the repository after a call to the save() method of the containing object.
    """

    @abstractmethod
    def get_name(self) -> OdmaQName:
        """
        Returns the qualified name of this property.

        :return: The qualified name of this property.
        """
        pass

    @abstractmethod
    def get_type(self) -> OdmaType:
        """
        Returns the data type of this property.
        
        :return: The data type of this property.
        """
        pass

    @abstractmethod
    def get_value(self) -> Any:
        """
        Returns the value of this property. The concrete object returned
        by this method depends on the data type of this property.

        :return: The value of this property.
        """
        pass

    @abstractmethod
    def set_value(self, new_value: Any) -> None:
        """
        Sets the value of this property. The type and classof the given
        new_value has to match the data type of this OdmaProperty.

        :param new_value: the new value to set this property to.
        :raises OdmaInvalidDataTypeException: Raised if the type of the assigned value does not match the data type of this OdmaProperty.
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def is_multi_value(self) -> bool:
        """
        Checks if this property is a multi-value property.
        
        :return: `True` if and only if this property is a multi value property.
        """
        pass

    @abstractmethod
    def is_dirty(self) -> bool:
        """
        Checks if this property has unsaved changes.
        
        :return: `True` if and only if this property has unsaved changes.
        """
        pass

    @abstractmethod
    def is_read_only(self) -> bool:
        """
        Checks if this property is read-only.
        
        :return: `True` if and only if this property is read-only.
        """
        pass

    @abstractmethod
    def get_resolution_state(self) -> PropertyResolutionState:
        """
        Indicates if the value of this property is immediately available can be read without a round-trip to a back-end system.
        
        :return: the availability state of this property value.
        """
        pass

    @abstractmethod
    def get_string(self) -> Optional[str]:
        """ Retrieves the String value of this property if and only if
        the data type of this property is a single valued String.
        """
        pass

    @abstractmethod
    def get_integer(self) -> Optional[int]:
        """ Retrieves the Integer value of this property if and only if
        the data type of this property is a single valued Integer.
        """
        pass

    @abstractmethod
    def get_short(self) -> Optional[int]:
        """ Retrieves the Short value of this property if and only if
        the data type of this property is a single valued Short.
        """
        pass

    @abstractmethod
    def get_long(self) -> Optional[int]:
        """ Retrieves the Long value of this property if and only if
        the data type of this property is a single valued Long.
        """
        pass

    @abstractmethod
    def get_float(self) -> Optional[float]:
        """ Retrieves the Float value of this property if and only if
        the data type of this property is a single valued Float.
        """
        pass

    @abstractmethod
    def get_double(self) -> Optional[float]:
        """ Retrieves the Double value of this property if and only if
        the data type of this property is a single valued Double.
        """
        pass

    @abstractmethod
    def get_boolean(self) -> Optional[bool]:
        """ Retrieves the Boolean value of this property if and only if
        the data type of this property is a single valued Boolean.
        """
        pass

    @abstractmethod
    def get_datetime(self) -> Optional[datetime]:
        """ Retrieves the DateTime value of this property if and only if
        the data type of this property is a single valued DateTime.
        """
        pass

    @abstractmethod
    def get_binary(self) -> Optional[bytes]:
        """ Retrieves the Binary value of this property if and only if
        the data type of this property is a single valued Binary.
        """
        pass

    @abstractmethod
    def get_reference(self) -> Optional[TOdmaObject]:
        """ Retrieves the Reference value of this property if and only if
        the data type of this property is a single valued Reference.
        """
        pass

    @abstractmethod
    def get_reference_id(self) -> Optional[OdmaId]:
        """ Retrieves the OdmaId of the Reference value of this property if and only if
        the data type of this property is a single valued Reference.
        
        Based on the PropertyResolutionState, it is possible that this OdmaId is immediately available
        while the OdmaObject requires an additional round-trip to the server.
        """
        pass

    @abstractmethod
    def get_content(self) -> Optional[OdmaContent]:
        """ Retrieves the Content value of this property if and only if
        the data type of this property is a single valued Content.
        """
        pass

    @abstractmethod
    def get_id(self) -> Optional[OdmaId]:
        """ Retrieves the Id value of this property if and only if
        the data type of this property is a single valued Id.
        """
        pass

    @abstractmethod
    def get_guid(self) -> Optional[OdmaGuid]:
        """ Retrieves the Guid value of this property if and only if
        the data type of this property is a single valued Guid.
        """
        pass

    @abstractmethod
    def get_string_list(self) -> list[str]:
        """ Retrieves the String value of this property if and only if
        the data type of this property is a multi valued String.
        """
        pass

    @abstractmethod
    def get_integer_list(self) -> list[int]:
        """ Retrieves the Integer value of this property if and only if
        the data type of this property is a multi valued Integer.
        """
        pass

    @abstractmethod
    def get_short_list(self) -> list[int]:
        """ Retrieves the Short value of this property if and only if
        the data type of this property is a multi valued Short.
        """
        pass

    @abstractmethod
    def get_long_list(self) -> list[int]:
        """ Retrieves the Long value of this property if and only if
        the data type of this property is a multi valued Long.
        """
        pass

    @abstractmethod
    def get_float_list(self) -> list[float]:
        """ Retrieves the Float value of this property if and only if
        the data type of this property is a multi valued Float.
        """
        pass

    @abstractmethod
    def get_double_list(self) -> list[float]:
        """ Retrieves the Double value of this property if and only if
        the data type of this property is a multi valued Double.
        """
        pass

    @abstractmethod
    def get_boolean_list(self) -> list[bool]:
        """ Retrieves the Boolean value of this property if and only if
        the data type of this property is a multi valued Boolean.
        """
        pass

    @abstractmethod
    def get_datetime_list(self) -> list[datetime]:
        """ Retrieves the DateTime value of this property if and only if
        the data type of this property is a multi valued DateTime.
        """
        pass

    @abstractmethod
    def get_binary_list(self) -> list[bytes]:
        """ Retrieves the Binary value of this property if and only if
        the data type of this property is a multi valued Binary.
        """
        pass

    @abstractmethod
    def get_reference_iterable(self) -> Iterable[TOdmaObject]:
        """ Retrieves the Reference value of this property if and only if
        the data type of this property is a multi valued Reference.
        """
        pass

    @abstractmethod
    def get_content_list(self) -> list[OdmaContent]:
        """ Retrieves the Content value of this property if and only if
        the data type of this property is a multi valued Content.
        """
        pass

    @abstractmethod
    def get_id_list(self) -> list[OdmaId]:
        """ Retrieves the Id value of this property if and only if
        the data type of this property is a multi valued Id.
        """
        pass

    @abstractmethod
    def get_guid_list(self) -> list[OdmaGuid]:
        """ Retrieves the Guid value of this property if and only if
        the data type of this property is a multi valued Guid.
        """
        pass



class OdmaCoreObject(ABC):
    """
    Generic capabilities of an object in OpenDMA. Do not use directly. Instead, use OdmaObject.
    """

    @abstractmethod
    def get_property(self, property_name: OdmaQName) -> OdmaProperty:
        """
        Returns an OdmaProperty for the property identified by the given qualified name.
        The named property is automatically retrieved from the server if it is not yet in the local cache.
        To optimize performance, consider calling prepareProperties($propertyNames,$refresh) first when
        accessing multiple properties.

        :param property_name: The qualified name of the property to return.
        :return: The property identified by the given qualified name.
        :raises OdmaPropertyNotFoundException: Raised if the given qualified name does not identify a property in the effective properties of the class of this object.
        """
        pass

    @abstractmethod
    def prepare_properties(self, property_names: Optional[list[OdmaQName]], refresh: bool) -> None:
        """
        Checks if the specified properties are already in the local cache and retrieves them from the server if not.
        If refresh is set to true, all specified properties are always retrieved from the server.
        Such a refresh will reset unsaved changes of properties to the latest state on the server.
        If a given qualified name does not identify a property, it is silently ignored.

        :param property_names: List of qualified names of properties to retrieve, or None to retrieve all.
        :param refresh: Indicates whether properties should be refreshed even if they are in the local cache.
        """
        pass

    @abstractmethod
    def set_property(self, property_name: OdmaQName, new_value: Any) -> None:
        """
        Sets the specified property to a new value.
        This is a shortcut for getProperty(propertyName).setValue(newValue). It avoids the retrieval of the property
        in the getProperty(propertyName) method if the property is not yet in the local cache.

        :param property_name: The qualified name of the property to be changed.
        :param new_value: The new value for the property.
        :raises OdmaPropertyNotFoundException: Raised if the given qualified name does not identify a property in the effective properties of this object's class.
        :raises OdmaInvalidDataTypeException: Raised if the type of new_value does not match the property's data type.
        :raises OdmaAccessDeniedException: Raised if the current user does not have permission to modify the property.
        """
        pass

    @abstractmethod
    def is_dirty(self) -> bool:
        """
        Checks if there are pending changes to properties that have not been persisted to the server.

        :return: True if there are pending changes, False otherwise.
        """
        pass

    @abstractmethod
    def save(self) -> None:
        """
        Persists the current pending changes to properties at the server.
        """
        pass

    @abstractmethod
    def instance_of(self, class_or_aspect_name: OdmaQName) -> bool:
        """
        Determines whether this object's class or one of its ancestors matches or incorporates the specified class or aspect.

        :param class_or_aspect_name: The qualified name of the class or aspect to test.
        :return: True if the object matches or incorporates the given class or aspect, False otherwise.
        """
        pass

class OdmaObject(OdmaCoreObject):
    """
    Root of the class hierarchy. Every class in OpenDMA extends this class. All objects in OpenDMA have the properties defined for this class.
    """

    @abstractmethod
    def get_odma_class(self) -> "OdmaClass":
        """
        Returns Reference to a valid class object describing this object.<br>
        Shortcut for <code>get_property(PROPERTY_CLASS).get_reference()</code>.
        
        Property opendma:Class: Reference to Class (opendma)
        [SingleValue] [ReadOnly] [Required]
        The opendma:Class describes the layout and features of this object. Here you can find a set of odma:PropertyInfo objects that describe all the properties with their qualified name, data type and cardinality. It also provides the text to be displayed to users to refer to these objects as well as flags indicating if these objects are system owner or should be hidden from end users.
        
        :return: Reference to a valid class object describing this object
        """
        pass

    @abstractmethod
    def get_aspects(self) -> Iterable[TOdmaClass]:
        """
        Returns References to valid aspect objects describing this object.<br>
        Shortcut for <code>get_property(PROPERTY_ASPECTS).get_reference_iterable()</code>.
        
        Property opendma:Aspects: Reference to Class (opendma)
        [MultiValue] [ReadOnly] [Optional]
        The opendma:Aspects can augment the layout and features defined by opendma:Class for this object.
        
        :return: References to valid aspect objects describing this object
        """
        pass

    @abstractmethod
    def get_id(self) -> OdmaId:
        """
        Returns the unique object identifier.<br>
        Shortcut for <code>get_property(PROPERTY_ID).get_id()</code>.
        
        Property opendma:Id: String
        [SingleValue] [ReadOnly] [Required]
        This identifier is unique within it's Repository and  must be immutable during the lifetime of this object. You can use it to refer to this object and retrieve it again at a later time.
        
        :return: the unique object identifier
        """
        pass

    @abstractmethod
    def get_guid(self) -> OdmaGuid:
        """
        Returns the global unique object identifier.<br>
        Shortcut for <code>get_property(PROPERTY_GUID).get_guid()</code>.
        
        Property opendma:Guid: String
        [SingleValue] [ReadOnly] [Required]
        A combination of the unique object identifier and the unique repository identifier. Use it to refer to this object across multiple repositories.
        
        :return: the global unique object identifier
        """
        pass

    @abstractmethod
    def get_repository(self) -> "OdmaRepository":
        """
        Returns the Repository this object belongs to.<br>
        Shortcut for <code>get_property(PROPERTY_REPOSITORY).get_reference()</code>.
        
        Property opendma:Repository: Reference to Repository (opendma)
        [SingleValue] [ReadOnly] [Required]
        
        :return: the Repository this object belongs to
        """
        pass

class OdmaClass(OdmaObject):
    """
    The Class specific version of the OdmaObject interface
    offering short-cuts to all defined OpenDMA properties.

    Describes Classes and Aspects in OpenDMA. Every object in OpenDMA has a reference to an instance of this class describing it.
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns the name part of the qualified name of the class described by this object.<br>
        Shortcut for <code>get_property(PROPERTY_NAME).get_string()</code>.
        
        Property opendma:Name: String
        [SingleValue] [Writable] [Required]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :return: the name part of the qualified name of the class described by this object
        """
        pass

    @abstractmethod
    def set_name(self, new_value: str) -> None:
        """
        Sets the name part of the qualified name of the class described by this object.<br>
        Shortcut for <code>get_property(PROPERTY_NAME).set_value()</code>.
        
        Property opendma:Name: String
        [SingleValue] [Writable] [Required]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :param new_value: the new value for the name part of the qualified name of the class described by this object
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_namespace(self) -> Optional[str]:
        """
        Returns the namespace part of the qualified name of the class described by this object.<br>
        Shortcut for <code>get_property(PROPERTY_NAMESPACE).get_string()</code>.
        
        Property opendma:Namespace: String
        [SingleValue] [Writable] [Optional]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :return: the namespace part of the qualified name of the class described by this object
        """
        pass

    @abstractmethod
    def set_namespace(self, new_value: Optional[str]) -> None:
        """
        Sets the namespace part of the qualified name of the class described by this object.<br>
        Shortcut for <code>get_property(PROPERTY_NAMESPACE).set_value()</code>.
        
        Property opendma:Namespace: String
        [SingleValue] [Writable] [Optional]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :param new_value: the new value for the namespace part of the qualified name of the class described by this object
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_display_name(self) -> str:
        """
        Returns Text shown to end users to refer to this class.<br>
        Shortcut for <code>get_property(PROPERTY_DISPLAYNAME).get_string()</code>.
        
        Property opendma:DisplayName: String
        [SingleValue] [Writable] [Required]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :return: Text shown to end users to refer to this class
        """
        pass

    @abstractmethod
    def set_display_name(self, new_value: str) -> None:
        """
        Sets Text shown to end users to refer to this class.<br>
        Shortcut for <code>get_property(PROPERTY_DISPLAYNAME).set_value()</code>.
        
        Property opendma:DisplayName: String
        [SingleValue] [Writable] [Required]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :param new_value: the new value for Text shown to end users to refer to this class
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_super_class(self) -> Optional["OdmaClass"]:
        """
        Returns Super class of this class or aspect..<br>
        Shortcut for <code>get_property(PROPERTY_SUPERCLASS).get_reference()</code>.
        
        Property opendma:SuperClass: Reference to Class (opendma)
        [SingleValue] [ReadOnly] [Optional]
        OpenDMA guarantees this relationship to be loop-free. You can use it to explore the class hierarchy starting from the class described by this object. All opendma:PropertyInfo objects contained in the opendma:Properties set of the super class are also part of the opendma:Properties set of this class.
        
        :return: Super class of this class or aspect.
        """
        pass

    @abstractmethod
    def get_included_aspects(self) -> Iterable[TOdmaClass]:
        """
        Returns List of aspects that are included in this class.<br>
        Shortcut for <code>get_property(PROPERTY_INCLUDEDASPECTS).get_reference_iterable()</code>.
        
        Property opendma:IncludedAspects: Reference to Class (opendma)
        [MultiValue] [Writable] [Optional]
        If this object describes an Aspect, i.e. the opendma:Aspect property is true, it cannot have any Aspects itself. For classes, this set contains all elements of the opendma:Aspects set of the super class. All opendma:PropertyInfo objects contained in the opendma:Properties set of any of the opendma:Class objects in this set are also part of the opendma:Properties set of this class.
        
        :return: List of aspects that are included in this class
        """
        pass

    @abstractmethod
    def get_declared_properties(self) -> Iterable[TOdmaPropertyInfo]:
        """
        Returns List of properties declared by this class.<br>
        Shortcut for <code>get_property(PROPERTY_DECLAREDPROPERTIES).get_reference_iterable()</code>.
        
        Property opendma:DeclaredProperties: Reference to PropertyInfo (opendma)
        [MultiValue] [Writable] [Optional]
        Set of opendma:PropertyInfo objects describing properties newly introduced by this level in the class hierarchy. All elements of this set are also contained in the opendma:Properties set. Properties cannot be overwritten, i.e. the qualified nyme of any property described by an opendma:PropertyInfo object in this set cannot be used in the opendma:Properties sets of the super class or any Aspect.
        
        :return: List of properties declared by this class
        """
        pass

    @abstractmethod
    def get_properties(self) -> Iterable[TOdmaPropertyInfo]:
        """
        Returns List of effective properties.<br>
        Shortcut for <code>get_property(PROPERTY_PROPERTIES).get_reference_iterable()</code>.
        
        Property opendma:Properties: Reference to PropertyInfo (opendma)
        [MultiValue] [ReadOnly] [Optional]
        Set of opendma:PropertyInfo objects describing all properties of an object of this class. This set combines the opendma:DeclaredProperties set with the opendma:Properties of the super class as well as the opendma:Properties sets of all aspect objects listed in opendma:Aspects. Properties cannot be overwritten, i.e. the qualified nyme of any property described by an opendma:PropertyInfo object in the opendma:DeclaredProperties set cannot be used in the opendma:Properties sets of the super class or any Aspect.
        
        :return: List of effective properties
        """
        pass

    @abstractmethod
    def get_aspect(self) -> bool:
        """
        Returns Indicates if this object represents an Aspect (true) or a Class (false).<br>
        Shortcut for <code>get_property(PROPERTY_ASPECT).get_boolean()</code>.
        
        Property opendma:Aspect: Boolean
        [SingleValue] [ReadOnly] [Required]
        
        :return: Indicates if this object represents an Aspect (true) or a Class (false)
        """
        pass

    @abstractmethod
    def get_hidden(self) -> bool:
        """
        Returns Indicates if this class should be hidden from end users and probably administrators.<br>
        Shortcut for <code>get_property(PROPERTY_HIDDEN).get_boolean()</code>.
        
        Property opendma:Hidden: Boolean
        [SingleValue] [Writable] [Required]
        
        :return: Indicates if this class should be hidden from end users and probably administrators
        """
        pass

    @abstractmethod
    def set_hidden(self, new_value: bool) -> None:
        """
        Sets Indicates if this class should be hidden from end users and probably administrators.<br>
        Shortcut for <code>get_property(PROPERTY_HIDDEN).set_value()</code>.
        
        Property opendma:Hidden: Boolean
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for Indicates if this class should be hidden from end users and probably administrators
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_system(self) -> bool:
        """
        Returns Indicates if instances of this class are owned and managed by the system.<br>
        Shortcut for <code>get_property(PROPERTY_SYSTEM).get_boolean()</code>.
        
        Property opendma:System: Boolean
        [SingleValue] [Writable] [Required]
        
        :return: Indicates if instances of this class are owned and managed by the system
        """
        pass

    @abstractmethod
    def set_system(self, new_value: bool) -> None:
        """
        Sets Indicates if instances of this class are owned and managed by the system.<br>
        Shortcut for <code>get_property(PROPERTY_SYSTEM).set_value()</code>.
        
        Property opendma:System: Boolean
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for Indicates if instances of this class are owned and managed by the system
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_retrievable(self) -> bool:
        """
        Returns Indicates if instances of this class can by retrieved by their Id.<br>
        Shortcut for <code>get_property(PROPERTY_RETRIEVABLE).get_boolean()</code>.
        
        Property opendma:Retrievable: Boolean
        [SingleValue] [ReadOnly] [Required]
        
        :return: Indicates if instances of this class can by retrieved by their Id
        """
        pass

    @abstractmethod
    def get_searchable(self) -> bool:
        """
        Returns Indicates if instances of this class can be retrieved in a search.<br>
        Shortcut for <code>get_property(PROPERTY_SEARCHABLE).get_boolean()</code>.
        
        Property opendma:Searchable: Boolean
        [SingleValue] [ReadOnly] [Required]
        
        :return: Indicates if instances of this class can be retrieved in a search
        """
        pass

    @abstractmethod
    def get_sub_classes(self) -> Iterable[TOdmaClass]:
        """
        Returns List of classes or aspects that extend this class.<br>
        Shortcut for <code>get_property(PROPERTY_SUBCLASSES).get_reference_iterable()</code>.
        
        Property opendma:SubClasses: Reference to Class (opendma)
        [MultiValue] [ReadOnly] [Optional]
        The value of the `opendma:SubClasses` property is exactly the set of valid class objects whose `opendma:SuperClass` property contains a reference to this class info object
        
        :return: List of classes or aspects that extend this class
        """
        pass

    @abstractmethod
    def get_qname(self) -> OdmaQName:
        """
        Returns the qualified name of this class.
        A convenience shortcut to getting the name and namespace separately
        
        :return: The qualified name of this class
        """
        pass

class OdmaPropertyInfo(OdmaObject):
    """
    The PropertyInfo specific version of the OdmaObject interface
    offering short-cuts to all defined OpenDMA properties.

    Describes a property in OpenmDMA. Every object in OpenDMA has a reference to an opendma:Class which has the opendma:Properties set of PropertyInfo objects. Each describes one of the properties on the object.
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns The name part of the qualified name of this property.<br>
        Shortcut for <code>get_property(PROPERTY_NAME).get_string()</code>.
        
        Property opendma:Name: String
        [SingleValue] [Writable] [Required]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :return: The name part of the qualified name of this property
        """
        pass

    @abstractmethod
    def set_name(self, new_value: str) -> None:
        """
        Sets The name part of the qualified name of this property.<br>
        Shortcut for <code>get_property(PROPERTY_NAME).set_value()</code>.
        
        Property opendma:Name: String
        [SingleValue] [Writable] [Required]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :param new_value: the new value for The name part of the qualified name of this property
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_namespace(self) -> Optional[str]:
        """
        Returns The namespace part of the qualified name of this property.<br>
        Shortcut for <code>get_property(PROPERTY_NAMESPACE).get_string()</code>.
        
        Property opendma:Namespace: String
        [SingleValue] [Writable] [Optional]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :return: The namespace part of the qualified name of this property
        """
        pass

    @abstractmethod
    def set_namespace(self, new_value: Optional[str]) -> None:
        """
        Sets The namespace part of the qualified name of this property.<br>
        Shortcut for <code>get_property(PROPERTY_NAMESPACE).set_value()</code>.
        
        Property opendma:Namespace: String
        [SingleValue] [Writable] [Optional]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :param new_value: the new value for The namespace part of the qualified name of this property
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_display_name(self) -> str:
        """
        Returns Text shown to end users to refer to this property.<br>
        Shortcut for <code>get_property(PROPERTY_DISPLAYNAME).get_string()</code>.
        
        Property opendma:DisplayName: String
        [SingleValue] [Writable] [Required]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :return: Text shown to end users to refer to this property
        """
        pass

    @abstractmethod
    def set_display_name(self, new_value: str) -> None:
        """
        Sets Text shown to end users to refer to this property.<br>
        Shortcut for <code>get_property(PROPERTY_DISPLAYNAME).set_value()</code>.
        
        Property opendma:DisplayName: String
        [SingleValue] [Writable] [Required]
        The qualified name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :param new_value: the new value for Text shown to end users to refer to this property
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_data_type(self) -> int:
        """
        Returns Numeric data type ID.<br>
        Shortcut for <code>get_property(PROPERTY_DATATYPE).get_integer()</code>.
        
        Property opendma:DataType: Integer
        [SingleValue] [Writable] [Required]
        The data type of the property described by this object. See also the OdmaType enumeration for a mapping between the numeric type id and the type.
        
        :return: Numeric data type ID
        """
        pass

    @abstractmethod
    def set_data_type(self, new_value: int) -> None:
        """
        Sets Numeric data type ID.<br>
        Shortcut for <code>get_property(PROPERTY_DATATYPE).set_value()</code>.
        
        Property opendma:DataType: Integer
        [SingleValue] [Writable] [Required]
        The data type of the property described by this object. See also the OdmaType enumeration for a mapping between the numeric type id and the type.
        
        :param new_value: the new value for Numeric data type ID
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_reference_class(self) -> Optional["OdmaClass"]:
        """
        Returns The opendma:Class values of the property described by this object must be an instance of if and only if the data type is "Reference" (8), null otherwise.<br>
        Shortcut for <code>get_property(PROPERTY_REFERENCECLASS).get_reference()</code>.
        
        Property opendma:ReferenceClass: Reference to Class (opendma)
        [SingleValue] [Writable] [Optional]
        
        :return: The opendma:Class values of the property described by this object must be an instance of if and only if the data type is "Reference" (8), null otherwise
        """
        pass

    @abstractmethod
    def set_reference_class(self, new_value: Optional["OdmaClass"]) -> None:
        """
        Sets The opendma:Class values of the property described by this object must be an instance of if and only if the data type is "Reference" (8), null otherwise.<br>
        Shortcut for <code>get_property(PROPERTY_REFERENCECLASS).set_value()</code>.
        
        Property opendma:ReferenceClass: Reference to Class (opendma)
        [SingleValue] [Writable] [Optional]
        
        :param new_value: the new value for The opendma:Class values of the property described by this object must be an instance of if and only if the data type is "Reference" (8), null otherwise
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_multi_value(self) -> bool:
        """
        Returns Indicates if this property has single or multi cardinality.<br>
        Shortcut for <code>get_property(PROPERTY_MULTIVALUE).get_boolean()</code>.
        
        Property opendma:MultiValue: Boolean
        [SingleValue] [Writable] [Required]
        
        :return: Indicates if this property has single or multi cardinality
        """
        pass

    @abstractmethod
    def set_multi_value(self, new_value: bool) -> None:
        """
        Sets Indicates if this property has single or multi cardinality.<br>
        Shortcut for <code>get_property(PROPERTY_MULTIVALUE).set_value()</code>.
        
        Property opendma:MultiValue: Boolean
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for Indicates if this property has single or multi cardinality
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_required(self) -> bool:
        """
        Returns Indicates if at least one value is required.<br>
        Shortcut for <code>get_property(PROPERTY_REQUIRED).get_boolean()</code>.
        
        Property opendma:Required: Boolean
        [SingleValue] [Writable] [Required]
        
        :return: Indicates if at least one value is required
        """
        pass

    @abstractmethod
    def set_required(self, new_value: bool) -> None:
        """
        Sets Indicates if at least one value is required.<br>
        Shortcut for <code>get_property(PROPERTY_REQUIRED).set_value()</code>.
        
        Property opendma:Required: Boolean
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for Indicates if at least one value is required
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_read_only(self) -> bool:
        """
        Returns Indicates if this property can be updated.<br>
        Shortcut for <code>get_property(PROPERTY_READONLY).get_boolean()</code>.
        
        Property opendma:ReadOnly: Boolean
        [SingleValue] [Writable] [Required]
        
        :return: Indicates if this property can be updated
        """
        pass

    @abstractmethod
    def set_read_only(self, new_value: bool) -> None:
        """
        Sets Indicates if this property can be updated.<br>
        Shortcut for <code>get_property(PROPERTY_READONLY).set_value()</code>.
        
        Property opendma:ReadOnly: Boolean
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for Indicates if this property can be updated
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_hidden(self) -> bool:
        """
        Returns Indicates if this class should be hidden from end users and probably administrators.<br>
        Shortcut for <code>get_property(PROPERTY_HIDDEN).get_boolean()</code>.
        
        Property opendma:Hidden: Boolean
        [SingleValue] [Writable] [Required]
        
        :return: Indicates if this class should be hidden from end users and probably administrators
        """
        pass

    @abstractmethod
    def set_hidden(self, new_value: bool) -> None:
        """
        Sets Indicates if this class should be hidden from end users and probably administrators.<br>
        Shortcut for <code>get_property(PROPERTY_HIDDEN).set_value()</code>.
        
        Property opendma:Hidden: Boolean
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for Indicates if this class should be hidden from end users and probably administrators
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_system(self) -> bool:
        """
        Returns Indicates if instances of this property are owned and managed by the system.<br>
        Shortcut for <code>get_property(PROPERTY_SYSTEM).get_boolean()</code>.
        
        Property opendma:System: Boolean
        [SingleValue] [Writable] [Required]
        
        :return: Indicates if instances of this property are owned and managed by the system
        """
        pass

    @abstractmethod
    def set_system(self, new_value: bool) -> None:
        """
        Sets Indicates if instances of this property are owned and managed by the system.<br>
        Shortcut for <code>get_property(PROPERTY_SYSTEM).set_value()</code>.
        
        Property opendma:System: Boolean
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for Indicates if instances of this property are owned and managed by the system
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_choices(self) -> Iterable[TOdmaChoiceValue]:
        """
        Returns List of opendma:ChoiceValue instances each describing one valid value for this property.<br>
        Shortcut for <code>get_property(PROPERTY_CHOICES).get_reference_iterable()</code>.
        
        Property opendma:Choices: Reference to ChoiceValue (opendma)
        [MultiValue] [Writable] [Optional]
        OpenDMA can restrict values of a property to a predefined set of valid values. In this case, this set is not empty and each opendma:ChoiceValue describes one valid option. If this set is empty, any value is allowed.
        
        :return: List of opendma:ChoiceValue instances each describing one valid value for this property
        """
        pass

    @abstractmethod
    def get_qname(self) -> OdmaQName:
        """
        Returns the qualified name of this class.
        A convenience shortcut to getting the name and namespace separately
        
        :return: The qualified name of this class
        """
        pass

class OdmaChoiceValue(OdmaObject):
    """
    The ChoiceValue specific version of the OdmaObject interface
    offering short-cuts to all defined OpenDMA properties.

    Describes a possible value of a property
    """

    @abstractmethod
    def get_display_name(self) -> str:
        """
        Returns Text shown to end users to refer to this possible value option.<br>
        Shortcut for <code>get_property(PROPERTY_DISPLAYNAME).get_string()</code>.
        
        Property opendma:DisplayName: String
        [SingleValue] [Writable] [Required]
        This DisplayName indirections allows Administrators to define friendly descriptions for end users while storing internal numbers or abbreviation in the system
        
        :return: Text shown to end users to refer to this possible value option
        """
        pass

    @abstractmethod
    def set_display_name(self, new_value: str) -> None:
        """
        Sets Text shown to end users to refer to this possible value option.<br>
        Shortcut for <code>get_property(PROPERTY_DISPLAYNAME).set_value()</code>.
        
        Property opendma:DisplayName: String
        [SingleValue] [Writable] [Required]
        This DisplayName indirections allows Administrators to define friendly descriptions for end users while storing internal numbers or abbreviation in the system
        
        :param new_value: the new value for Text shown to end users to refer to this possible value option
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_string_value(self) -> Optional[str]:
        """
        Returns the String value of this choice or null, if the property info this choice is assigned to is not of data type String.<br>
        Shortcut for <code>get_property(PROPERTY_STRINGVALUE).get_string()</code>.
        
        Property opendma:StringValue: String
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the String value of this choice or null, if the property info this choice is assigned to is not of data type String
        """
        pass

    @abstractmethod
    def set_string_value(self, new_value: Optional[str]) -> None:
        """
        Sets the String value of this choice or null, if the property info this choice is assigned to is not of data type String.<br>
        Shortcut for <code>get_property(PROPERTY_STRINGVALUE).set_value()</code>.
        
        Property opendma:StringValue: String
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the String value of this choice or null, if the property info this choice is assigned to is not of data type String
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_integer_value(self) -> Optional[int]:
        """
        Returns the Integer value of this choice or null, if the property info this choice is assigned to is not of data type Integer.<br>
        Shortcut for <code>get_property(PROPERTY_INTEGERVALUE).get_integer()</code>.
        
        Property opendma:IntegerValue: Integer
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the Integer value of this choice or null, if the property info this choice is assigned to is not of data type Integer
        """
        pass

    @abstractmethod
    def set_integer_value(self, new_value: Optional[int]) -> None:
        """
        Sets the Integer value of this choice or null, if the property info this choice is assigned to is not of data type Integer.<br>
        Shortcut for <code>get_property(PROPERTY_INTEGERVALUE).set_value()</code>.
        
        Property opendma:IntegerValue: Integer
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the Integer value of this choice or null, if the property info this choice is assigned to is not of data type Integer
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_short_value(self) -> Optional[int]:
        """
        Returns the Short value of this choice or null, if the property info this choice is assigned to is not of data type Short.<br>
        Shortcut for <code>get_property(PROPERTY_SHORTVALUE).get_short()</code>.
        
        Property opendma:ShortValue: Short
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the Short value of this choice or null, if the property info this choice is assigned to is not of data type Short
        """
        pass

    @abstractmethod
    def set_short_value(self, new_value: Optional[int]) -> None:
        """
        Sets the Short value of this choice or null, if the property info this choice is assigned to is not of data type Short.<br>
        Shortcut for <code>get_property(PROPERTY_SHORTVALUE).set_value()</code>.
        
        Property opendma:ShortValue: Short
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the Short value of this choice or null, if the property info this choice is assigned to is not of data type Short
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_long_value(self) -> Optional[int]:
        """
        Returns the Long value of this choice or null, if the property info this choice is assigned to is not of data type Long.<br>
        Shortcut for <code>get_property(PROPERTY_LONGVALUE).get_long()</code>.
        
        Property opendma:LongValue: Long
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the Long value of this choice or null, if the property info this choice is assigned to is not of data type Long
        """
        pass

    @abstractmethod
    def set_long_value(self, new_value: Optional[int]) -> None:
        """
        Sets the Long value of this choice or null, if the property info this choice is assigned to is not of data type Long.<br>
        Shortcut for <code>get_property(PROPERTY_LONGVALUE).set_value()</code>.
        
        Property opendma:LongValue: Long
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the Long value of this choice or null, if the property info this choice is assigned to is not of data type Long
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_float_value(self) -> Optional[float]:
        """
        Returns the Float value of this choice or null, if the property info this choice is assigned to is not of data type Float.<br>
        Shortcut for <code>get_property(PROPERTY_FLOATVALUE).get_float()</code>.
        
        Property opendma:FloatValue: Float
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the Float value of this choice or null, if the property info this choice is assigned to is not of data type Float
        """
        pass

    @abstractmethod
    def set_float_value(self, new_value: Optional[float]) -> None:
        """
        Sets the Float value of this choice or null, if the property info this choice is assigned to is not of data type Float.<br>
        Shortcut for <code>get_property(PROPERTY_FLOATVALUE).set_value()</code>.
        
        Property opendma:FloatValue: Float
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the Float value of this choice or null, if the property info this choice is assigned to is not of data type Float
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_double_value(self) -> Optional[float]:
        """
        Returns the Double value of this choice or null, if the property info this choice is assigned to is not of data type Double.<br>
        Shortcut for <code>get_property(PROPERTY_DOUBLEVALUE).get_double()</code>.
        
        Property opendma:DoubleValue: Double
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the Double value of this choice or null, if the property info this choice is assigned to is not of data type Double
        """
        pass

    @abstractmethod
    def set_double_value(self, new_value: Optional[float]) -> None:
        """
        Sets the Double value of this choice or null, if the property info this choice is assigned to is not of data type Double.<br>
        Shortcut for <code>get_property(PROPERTY_DOUBLEVALUE).set_value()</code>.
        
        Property opendma:DoubleValue: Double
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the Double value of this choice or null, if the property info this choice is assigned to is not of data type Double
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_boolean_value(self) -> Optional[bool]:
        """
        Returns the Boolean value of this choice or null, if the property info this choice is assigned to is not of data type Boolean.<br>
        Shortcut for <code>get_property(PROPERTY_BOOLEANVALUE).get_boolean()</code>.
        
        Property opendma:BooleanValue: Boolean
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the Boolean value of this choice or null, if the property info this choice is assigned to is not of data type Boolean
        """
        pass

    @abstractmethod
    def set_boolean_value(self, new_value: Optional[bool]) -> None:
        """
        Sets the Boolean value of this choice or null, if the property info this choice is assigned to is not of data type Boolean.<br>
        Shortcut for <code>get_property(PROPERTY_BOOLEANVALUE).set_value()</code>.
        
        Property opendma:BooleanValue: Boolean
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the Boolean value of this choice or null, if the property info this choice is assigned to is not of data type Boolean
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_date_time_value(self) -> Optional[datetime]:
        """
        Returns the DateTime value of this choice or null, if the property info this choice is assigned to is not of data type DateTime.<br>
        Shortcut for <code>get_property(PROPERTY_DATETIMEVALUE).get_datetime()</code>.
        
        Property opendma:DateTimeValue: DateTime
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the DateTime value of this choice or null, if the property info this choice is assigned to is not of data type DateTime
        """
        pass

    @abstractmethod
    def set_date_time_value(self, new_value: Optional[datetime]) -> None:
        """
        Sets the DateTime value of this choice or null, if the property info this choice is assigned to is not of data type DateTime.<br>
        Shortcut for <code>get_property(PROPERTY_DATETIMEVALUE).set_value()</code>.
        
        Property opendma:DateTimeValue: DateTime
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the DateTime value of this choice or null, if the property info this choice is assigned to is not of data type DateTime
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_binary_value(self) -> Optional[bytes]:
        """
        Returns the Binary value of this choice or null, if the property info this choice is assigned to is not of data type Binary.<br>
        Shortcut for <code>get_property(PROPERTY_BINARYVALUE).get_binary()</code>.
        
        Property opendma:BinaryValue: Binary
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the Binary value of this choice or null, if the property info this choice is assigned to is not of data type Binary
        """
        pass

    @abstractmethod
    def set_binary_value(self, new_value: Optional[bytes]) -> None:
        """
        Sets the Binary value of this choice or null, if the property info this choice is assigned to is not of data type Binary.<br>
        Shortcut for <code>get_property(PROPERTY_BINARYVALUE).set_value()</code>.
        
        Property opendma:BinaryValue: Binary
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the Binary value of this choice or null, if the property info this choice is assigned to is not of data type Binary
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_reference_value(self) -> Optional["OdmaObject"]:
        """
        Returns the Reference value of this choice or null, if the property info this choice is assigned to is not of data type Reference.<br>
        Shortcut for <code>get_property(PROPERTY_REFERENCEVALUE).get_reference()</code>.
        
        Property opendma:ReferenceValue: Reference to Object (opendma)
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :return: the Reference value of this choice or null, if the property info this choice is assigned to is not of data type Reference
        """
        pass

    @abstractmethod
    def set_reference_value(self, new_value: Optional["OdmaObject"]) -> None:
        """
        Sets the Reference value of this choice or null, if the property info this choice is assigned to is not of data type Reference.<br>
        Shortcut for <code>get_property(PROPERTY_REFERENCEVALUE).set_value()</code>.
        
        Property opendma:ReferenceValue: Reference to Object (opendma)
        [SingleValue] [Writable] [Optional]
        Full description follows.
        
        :param new_value: the new value for the Reference value of this choice or null, if the property info this choice is assigned to is not of data type Reference
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

class OdmaRepository(OdmaObject):
    """
    The Repository specific version of the OdmaObject interface
    offering short-cuts to all defined OpenDMA properties.

    A Repository represents a place where all Objects are stored. It often constitues a data isolation boundary where objects with different management requirements or access restrictions are separated into different repositories. Qualified names of classes and properties as well as unique object identifiers are only unique within a repository. They can be reused across different repositories. Object references are limited in scope within a single repository.
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns the internal technical name of this repository.<br>
        Shortcut for <code>get_property(PROPERTY_NAME).get_string()</code>.
        
        Property opendma:Name: String
        [SingleValue] [Writable] [Required]
        The name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :return: the internal technical name of this repository
        """
        pass

    @abstractmethod
    def set_name(self, new_value: str) -> None:
        """
        Sets the internal technical name of this repository.<br>
        Shortcut for <code>get_property(PROPERTY_NAME).set_value()</code>.
        
        Property opendma:Name: String
        [SingleValue] [Writable] [Required]
        The name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :param new_value: the new value for the internal technical name of this repository
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_display_name(self) -> str:
        """
        Returns the text shown to end users to refer to this repository.<br>
        Shortcut for <code>get_property(PROPERTY_DISPLAYNAME).get_string()</code>.
        
        Property opendma:DisplayName: String
        [SingleValue] [Writable] [Required]
        The name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :return: the text shown to end users to refer to this repository
        """
        pass

    @abstractmethod
    def set_display_name(self, new_value: str) -> None:
        """
        Sets the text shown to end users to refer to this repository.<br>
        Shortcut for <code>get_property(PROPERTY_DISPLAYNAME).set_value()</code>.
        
        Property opendma:DisplayName: String
        [SingleValue] [Writable] [Required]
        The name is a technical identifier that typically has some restrictions, e.g. for database table names. The DisplayName in contrast is tailored for end users.
        
        :param new_value: the new value for the text shown to end users to refer to this repository
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_root_class(self) -> "OdmaClass":
        """
        Returns Valid class object describing the class hierarchy root.<br>
        Shortcut for <code>get_property(PROPERTY_ROOTCLASS).get_reference()</code>.
        
        Property opendma:RootClass: Reference to Class (opendma)
        [SingleValue] [ReadOnly] [Required]
        
        :return: Valid class object describing the class hierarchy root
        """
        pass

    @abstractmethod
    def get_root_aspects(self) -> Iterable[TOdmaClass]:
        """
        Returns set of valid aspect objects without a super class.<br>
        Shortcut for <code>get_property(PROPERTY_ROOTASPECTS).get_reference_iterable()</code>.
        
        Property opendma:RootAspects: Reference to Class (opendma)
        [MultiValue] [ReadOnly] [Optional]
        
        :return: set of valid aspect objects without a super class
        """
        pass

    @abstractmethod
    def get_root_folder(self) -> Optional["OdmaFolder"]:
        """
        Returns Object that has the opendma:Folder aspect representing the single root if this repository has a dedicated folder tree, null otherwise.<br>
        Shortcut for <code>get_property(PROPERTY_ROOTFOLDER).get_reference()</code>.
        
        Property opendma:RootFolder: Reference to Folder (opendma)
        [SingleValue] [ReadOnly] [Optional]
        Full description follows.
        
        :return: Object that has the opendma:Folder aspect representing the single root if this repository has a dedicated folder tree, null otherwise
        """
        pass

class OdmaAuditStamped(OdmaObject):
    """
    Objects with this aspect record information about their creation and their last modification.
    """

    @abstractmethod
    def get_created_at(self) -> Optional[datetime]:
        """
        Returns the timestamp when this object has been created.<br>
        Shortcut for <code>get_property(PROPERTY_CREATEDAT).get_datetime()</code>.
        
        Property opendma:CreatedAt: DateTime
        [SingleValue] [ReadOnly] [Optional]
        
        :return: the timestamp when this object has been created
        """
        pass

    @abstractmethod
    def get_created_by(self) -> Optional[str]:
        """
        Returns the User who created this object.<br>
        Shortcut for <code>get_property(PROPERTY_CREATEDBY).get_string()</code>.
        
        Property opendma:CreatedBy: String
        [SingleValue] [ReadOnly] [Optional]
        
        :return: the User who created this object
        """
        pass

    @abstractmethod
    def get_last_modified_at(self) -> Optional[datetime]:
        """
        Returns the timestamp when this object has been modified the last time.<br>
        Shortcut for <code>get_property(PROPERTY_LASTMODIFIEDAT).get_datetime()</code>.
        
        Property opendma:LastModifiedAt: DateTime
        [SingleValue] [ReadOnly] [Optional]
        
        :return: the timestamp when this object has been modified the last time
        """
        pass

    @abstractmethod
    def get_last_modified_by(self) -> Optional[str]:
        """
        Returns the user who modified this object the last time.<br>
        Shortcut for <code>get_property(PROPERTY_LASTMODIFIEDBY).get_string()</code>.
        
        Property opendma:LastModifiedBy: String
        [SingleValue] [ReadOnly] [Optional]
        
        :return: the user who modified this object the last time
        """
        pass

class OdmaDocument(OdmaObject):
    """
    A Document is the atomic element users work on in a content based environment. It can be compared to a file in a file system. Unlike files, it may consist of multiple octet streams. These content streams can for example contain images of the individual pages that make up the document. A Document is able to keep track of its changes (versioning) and manage the access to it (checkin and checkout).
    """

    @abstractmethod
    def get_title(self) -> Optional[str]:
        """
        Returns the title of this document.<br>
        Shortcut for <code>get_property(PROPERTY_TITLE).get_string()</code>.
        
        Property opendma:Title: String
        [SingleValue] [Writable] [Optional]
        Typically a human friendly readable description of this document. Does not need to be a file name, but can be the file name.
        
        :return: the title of this document
        """
        pass

    @abstractmethod
    def set_title(self, new_value: Optional[str]) -> None:
        """
        Sets the title of this document.<br>
        Shortcut for <code>get_property(PROPERTY_TITLE).set_value()</code>.
        
        Property opendma:Title: String
        [SingleValue] [Writable] [Optional]
        Typically a human friendly readable description of this document. Does not need to be a file name, but can be the file name.
        
        :param new_value: the new value for the title of this document
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_version(self) -> Optional[str]:
        """
        Returns Identifier of this version consisting of a set of numbers separated by a point (e.g. 1.2.3).<br>
        Shortcut for <code>get_property(PROPERTY_VERSION).get_string()</code>.
        
        Property opendma:Version: String
        [SingleValue] [ReadOnly] [Optional]
        This value is heavily vendor specific. You should not have any expectations of the format.
        
        :return: Identifier of this version consisting of a set of numbers separated by a point (e.g. 1.2.3)
        """
        pass

    @abstractmethod
    def get_version_collection(self) -> Optional["OdmaVersionCollection"]:
        """
        Returns reference to a opendma:VersionCollection object representing all versions of this document or null if versioning is not supported.<br>
        Shortcut for <code>get_property(PROPERTY_VERSIONCOLLECTION).get_reference()</code>.
        
        Property opendma:VersionCollection: Reference to VersionCollection (opendma)
        [SingleValue] [ReadOnly] [Optional]
        
        :return: reference to a opendma:VersionCollection object representing all versions of this document or null if versioning is not supported
        """
        pass

    @abstractmethod
    def get_version_independent_id(self) -> OdmaId:
        """
        Returns the unique object identifier identifying this logical document independent from the specific version inside its opendma:Repository.<br>
        Shortcut for <code>get_property(PROPERTY_VERSIONINDEPENDENTID).get_id()</code>.
        
        Property opendma:VersionIndependentId: String
        [SingleValue] [ReadOnly] [Required]
        Retrieving this Id from the Repository will result in the latest version
        
        :return: the unique object identifier identifying this logical document independent from the specific version inside its opendma:Repository
        """
        pass

    @abstractmethod
    def get_version_independent_guid(self) -> OdmaGuid:
        """
        Returns the global unique object identifier globally identifying this logical document independent from the specific version.<br>
        Shortcut for <code>get_property(PROPERTY_VERSIONINDEPENDENTGUID).get_guid()</code>.
        
        Property opendma:VersionIndependentGuid: String
        [SingleValue] [ReadOnly] [Required]
        
        :return: the global unique object identifier globally identifying this logical document independent from the specific version
        """
        pass

    @abstractmethod
    def get_content_elements(self) -> Iterable[TOdmaContentElement]:
        """
        Returns set of opendma:ContentElement objects representing the individual binary elements this document is made up of.<br>
        Shortcut for <code>get_property(PROPERTY_CONTENTELEMENTS).get_reference_iterable()</code>.
        
        Property opendma:ContentElements: Reference to ContentElement (opendma)
        [MultiValue] [Writable] [Optional]
        Typically has only one element. Can contain more then one element in rare cases, e.g. if individual pages of a document are scanned as separate images
        
        :return: set of opendma:ContentElement objects representing the individual binary elements this document is made up of
        """
        pass

    @abstractmethod
    def get_combined_content_type(self) -> Optional[str]:
        """
        Returns the combined conent type of the whole Document, calculated from the content types of each ContentElement.<br>
        Shortcut for <code>get_property(PROPERTY_COMBINEDCONTENTTYPE).get_string()</code>.
        
        Property opendma:CombinedContentType: String
        [SingleValue] [Writable] [Optional]
        
        :return: the combined conent type of the whole Document, calculated from the content types of each ContentElement
        """
        pass

    @abstractmethod
    def set_combined_content_type(self, new_value: Optional[str]) -> None:
        """
        Sets the combined conent type of the whole Document, calculated from the content types of each ContentElement.<br>
        Shortcut for <code>get_property(PROPERTY_COMBINEDCONTENTTYPE).set_value()</code>.
        
        Property opendma:CombinedContentType: String
        [SingleValue] [Writable] [Optional]
        
        :param new_value: the new value for the combined conent type of the whole Document, calculated from the content types of each ContentElement
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_primary_content_element(self) -> Optional["OdmaContentElement"]:
        """
        Returns the dedicated primary ContentElement. May only be null if ContentElements is empty..<br>
        Shortcut for <code>get_property(PROPERTY_PRIMARYCONTENTELEMENT).get_reference()</code>.
        
        Property opendma:PrimaryContentElement: Reference to ContentElement (opendma)
        [SingleValue] [Writable] [Optional]
        
        :return: the dedicated primary ContentElement. May only be null if ContentElements is empty.
        """
        pass

    @abstractmethod
    def set_primary_content_element(self, new_value: Optional["OdmaContentElement"]) -> None:
        """
        Sets the dedicated primary ContentElement. May only be null if ContentElements is empty..<br>
        Shortcut for <code>get_property(PROPERTY_PRIMARYCONTENTELEMENT).set_value()</code>.
        
        Property opendma:PrimaryContentElement: Reference to ContentElement (opendma)
        [SingleValue] [Writable] [Optional]
        
        :param new_value: the new value for the dedicated primary ContentElement. May only be null if ContentElements is empty.
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_checked_out(self) -> bool:
        """
        Returns indicates if this document is checked out.<br>
        Shortcut for <code>get_property(PROPERTY_CHECKEDOUT).get_boolean()</code>.
        
        Property opendma:CheckedOut: Boolean
        [SingleValue] [ReadOnly] [Required]
        
        :return: indicates if this document is checked out
        """
        pass

    @abstractmethod
    def get_checked_out_at(self) -> Optional[datetime]:
        """
        Returns the timestamp when this version of the document has been checked out, null if this document is not checked out.<br>
        Shortcut for <code>get_property(PROPERTY_CHECKEDOUTAT).get_datetime()</code>.
        
        Property opendma:CheckedOutAt: DateTime
        [SingleValue] [ReadOnly] [Optional]
        
        :return: the timestamp when this version of the document has been checked out, null if this document is not checked out
        """
        pass

    @abstractmethod
    def get_checked_out_by(self) -> Optional[str]:
        """
        Returns the user who checked out this version of this document, null if this document is not checked out.<br>
        Shortcut for <code>get_property(PROPERTY_CHECKEDOUTBY).get_string()</code>.
        
        Property opendma:CheckedOutBy: String
        [SingleValue] [ReadOnly] [Optional]
        Full description follows.
        
        :return: the user who checked out this version of this document, null if this document is not checked out
        """
        pass

class OdmaContentElement(OdmaObject):
    """
    A ContentElement represents one atomic content element the Documents are made of. This base class defines the type of content and the position of this element in the sequence of all content elements.
    """

    @abstractmethod
    def get_content_type(self) -> Optional[str]:
        """
        Returns the content type (aka MIME type) of the content represented by this element.<br>
        Shortcut for <code>get_property(PROPERTY_CONTENTTYPE).get_string()</code>.
        
        Property opendma:ContentType: String
        [SingleValue] [Writable] [Optional]
        
        :return: the content type (aka MIME type) of the content represented by this element
        """
        pass

    @abstractmethod
    def set_content_type(self, new_value: Optional[str]) -> None:
        """
        Sets the content type (aka MIME type) of the content represented by this element.<br>
        Shortcut for <code>get_property(PROPERTY_CONTENTTYPE).set_value()</code>.
        
        Property opendma:ContentType: String
        [SingleValue] [Writable] [Optional]
        
        :param new_value: the new value for the content type (aka MIME type) of the content represented by this element
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_position(self) -> Optional[int]:
        """
        Returns the position of this element in the list of all content elements of the containing document.<br>
        Shortcut for <code>get_property(PROPERTY_POSITION).get_integer()</code>.
        
        Property opendma:Position: Integer
        [SingleValue] [ReadOnly] [Optional]
        
        :return: the position of this element in the list of all content elements of the containing document
        """
        pass

class OdmaDataContentElement(OdmaContentElement):
    """
    The DataContentElement specific version of the OdmaContentElement interface
    offering short-cuts to all defined OpenDMA properties.

    A DataContentElement represents one atomic octet stream. The binary data is stored together with meta data like size and filename
    """

    @abstractmethod
    def get_content(self) -> Optional[OdmaContent]:
        """
        Returns the binary data of this content element.<br>
        Shortcut for <code>get_property(PROPERTY_CONTENT).get_content()</code>.
        
        Property opendma:Content: Content
        [SingleValue] [Writable] [Optional]
        
        :return: the binary data of this content element
        """
        pass

    @abstractmethod
    def set_content(self, new_value: Optional[OdmaContent]) -> None:
        """
        Sets the binary data of this content element.<br>
        Shortcut for <code>get_property(PROPERTY_CONTENT).set_value()</code>.
        
        Property opendma:Content: Content
        [SingleValue] [Writable] [Optional]
        
        :param new_value: the new value for the binary data of this content element
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_size(self) -> Optional[int]:
        """
        Returns the size of the data in number of octets.<br>
        Shortcut for <code>get_property(PROPERTY_SIZE).get_long()</code>.
        
        Property opendma:Size: Long
        [SingleValue] [ReadOnly] [Optional]
        
        :return: the size of the data in number of octets
        """
        pass

    @abstractmethod
    def get_file_name(self) -> Optional[str]:
        """
        Returns the optional file name of the data.<br>
        Shortcut for <code>get_property(PROPERTY_FILENAME).get_string()</code>.
        
        Property opendma:FileName: String
        [SingleValue] [Writable] [Optional]
        
        :return: the optional file name of the data
        """
        pass

    @abstractmethod
    def set_file_name(self, new_value: Optional[str]) -> None:
        """
        Sets the optional file name of the data.<br>
        Shortcut for <code>get_property(PROPERTY_FILENAME).set_value()</code>.
        
        Property opendma:FileName: String
        [SingleValue] [Writable] [Optional]
        
        :param new_value: the new value for the optional file name of the data
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

class OdmaReferenceContentElement(OdmaContentElement):
    """
    The ReferenceContentElement specific version of the OdmaContentElement interface
    offering short-cuts to all defined OpenDMA properties.

    A ReferenceContentElement represents a reference to external data. The reference is stored as URI to the content location.
    """

    @abstractmethod
    def get_location(self) -> Optional[str]:
        """
        Returns the URI where the content is stored.<br>
        Shortcut for <code>get_property(PROPERTY_LOCATION).get_string()</code>.
        
        Property opendma:Location: String
        [SingleValue] [Writable] [Optional]
        
        :return: the URI where the content is stored
        """
        pass

    @abstractmethod
    def set_location(self, new_value: Optional[str]) -> None:
        """
        Sets the URI where the content is stored.<br>
        Shortcut for <code>get_property(PROPERTY_LOCATION).set_value()</code>.
        
        Property opendma:Location: String
        [SingleValue] [Writable] [Optional]
        
        :param new_value: the new value for the URI where the content is stored
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

class OdmaVersionCollection(OdmaObject):
    """
    A VersionCollection represents the set of all versions of a Document. Based on the actual document management system, it can represent a single series of versions, a tree of version, or any other versioning concept.
    """

    @abstractmethod
    def get_versions(self) -> Iterable[TOdmaDocument]:
        """
        Returns Set of all versions of a document.<br>
        Shortcut for <code>get_property(PROPERTY_VERSIONS).get_reference_iterable()</code>.
        
        Property opendma:Versions: Reference to Document (opendma)
        [MultiValue] [ReadOnly] [Required]
        
        :return: Set of all versions of a document
        """
        pass

    @abstractmethod
    def get_latest(self) -> Optional["OdmaDocument"]:
        """
        Returns Latest version of a document.<br>
        Shortcut for <code>get_property(PROPERTY_LATEST).get_reference()</code>.
        
        Property opendma:Latest: Reference to Document (opendma)
        [SingleValue] [ReadOnly] [Optional]
        
        :return: Latest version of a document
        """
        pass

    @abstractmethod
    def get_released(self) -> Optional["OdmaDocument"]:
        """
        Returns Latest released version of a document if a version has been released.<br>
        Shortcut for <code>get_property(PROPERTY_RELEASED).get_reference()</code>.
        
        Property opendma:Released: Reference to Document (opendma)
        [SingleValue] [ReadOnly] [Optional]
        
        :return: Latest released version of a document if a version has been released
        """
        pass

    @abstractmethod
    def get_in_progress(self) -> Optional["OdmaDocument"]:
        """
        Returns Latest checked out working copy of a document.<br>
        Shortcut for <code>get_property(PROPERTY_INPROGRESS).get_reference()</code>.
        
        Property opendma:InProgress: Reference to Document (opendma)
        [SingleValue] [ReadOnly] [Optional]
        
        :return: Latest checked out working copy of a document
        """
        pass

class OdmaContainer(OdmaObject):
    """
    A Container holds a set of containable objects that are said to be contained in this Container. This list of containees is build up with Association objects based on references to the containmer and the containee. This allows an object to be contained in multiple Containers or in no Container at all. A Container does not enforce a loop-free single rooted tree. Use a folder instead for this requirement.
    """

    @abstractmethod
    def get_title(self) -> Optional[str]:
        """
        Returns the title of this container.<br>
        Shortcut for <code>get_property(PROPERTY_TITLE).get_string()</code>.
        
        Property opendma:Title: String
        [SingleValue] [Writable] [Optional]
        
        :return: the title of this container
        """
        pass

    @abstractmethod
    def set_title(self, new_value: Optional[str]) -> None:
        """
        Sets the title of this container.<br>
        Shortcut for <code>get_property(PROPERTY_TITLE).set_value()</code>.
        
        Property opendma:Title: String
        [SingleValue] [Writable] [Optional]
        
        :param new_value: the new value for the title of this container
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_containees(self) -> Iterable[TOdmaContainable]:
        """
        Returns the set of containable objects contained in this container.<br>
        Shortcut for <code>get_property(PROPERTY_CONTAINEES).get_reference_iterable()</code>.
        
        Property opendma:Containees: Reference to Containable (opendma)
        [MultiValue] [ReadOnly] [Optional]
        
        :return: the set of containable objects contained in this container
        """
        pass

    @abstractmethod
    def get_associations(self) -> Iterable[TOdmaAssociation]:
        """
        Returns the set of associations between this container and the contained objects.<br>
        Shortcut for <code>get_property(PROPERTY_ASSOCIATIONS).get_reference_iterable()</code>.
        
        Property opendma:Associations: Reference to Association (opendma)
        [MultiValue] [ReadOnly] [Optional]
        
        :return: the set of associations between this container and the contained objects
        """
        pass

class OdmaFolder(OdmaContainer):
    """
    The Folder specific version of the OdmaContainer interface
    offering short-cuts to all defined OpenDMA properties.

    A Folder is an extension of the Container forming one single rooted loop-free tree.
    """

    @abstractmethod
    def get_parent(self) -> Optional["OdmaFolder"]:
        """
        Returns the parent folder this folder is contained in.<br>
        Shortcut for <code>get_property(PROPERTY_PARENT).get_reference()</code>.
        
        Property opendma:Parent: Reference to Folder (opendma)
        [SingleValue] [Writable] [Optional]
        Following this property from folder object to folder object will ultimately lead to the single root folder of the Repository. This is the only folder having a null value for this property
        
        :return: the parent folder this folder is contained in
        """
        pass

    @abstractmethod
    def set_parent(self, new_value: Optional["OdmaFolder"]) -> None:
        """
        Sets the parent folder this folder is contained in.<br>
        Shortcut for <code>get_property(PROPERTY_PARENT).set_value()</code>.
        
        Property opendma:Parent: Reference to Folder (opendma)
        [SingleValue] [Writable] [Optional]
        Following this property from folder object to folder object will ultimately lead to the single root folder of the Repository. This is the only folder having a null value for this property
        
        :param new_value: the new value for the parent folder this folder is contained in
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_sub_folders(self) -> Iterable[TOdmaFolder]:
        """
        Returns the set of Folder objects that contain this folder in their opendma:Parent property.<br>
        Shortcut for <code>get_property(PROPERTY_SUBFOLDERS).get_reference_iterable()</code>.
        
        Property opendma:SubFolders: Reference to Folder (opendma)
        [MultiValue] [ReadOnly] [Optional]
        Using this property for a tree walk is safe. A folder is guaranteed to be loop free. It is neither defined if this set of objects is also part of the opendma:Containees property nor if there are corresponding association objects in opendma:Associations for each folder in this set.
        
        :return: the set of Folder objects that contain this folder in their opendma:Parent property
        """
        pass

class OdmaContainable(OdmaObject):
    """
    The Containable aspect is used by all classes and aspects that can be contained in a Container.
    """

    @abstractmethod
    def get_contained_in(self) -> Iterable[TOdmaContainer]:
        """
        Returns the set of container objects this Containable is contained in.<br>
        Shortcut for <code>get_property(PROPERTY_CONTAINEDIN).get_reference_iterable()</code>.
        
        Property opendma:ContainedIn: Reference to Container (opendma)
        [MultiValue] [ReadOnly] [Optional]
        
        :return: the set of container objects this Containable is contained in
        """
        pass

    @abstractmethod
    def get_contained_in_associations(self) -> Iterable[TOdmaAssociation]:
        """
        Returns the set of associations that bind this Containable in the opendma:Conatiner objects.<br>
        Shortcut for <code>get_property(PROPERTY_CONTAINEDINASSOCIATIONS).get_reference_iterable()</code>.
        
        Property opendma:ContainedInAssociations: Reference to Association (opendma)
        [MultiValue] [ReadOnly] [Optional]
        
        :return: the set of associations that bind this Containable in the opendma:Conatiner objects
        """
        pass

class OdmaAssociation(OdmaObject):
    """
    An Association represents the directed link between an opendma:Container and an opendma:Containable object.
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns the name of this association.<br>
        Shortcut for <code>get_property(PROPERTY_NAME).get_string()</code>.
        
        Property opendma:Name: String
        [SingleValue] [Writable] [Required]
        This name is used to refer to this specific association in the context of it's container and tell tem apart. Many systems pose additional constraints on this name.
        
        :return: the name of this association
        """
        pass

    @abstractmethod
    def set_name(self, new_value: str) -> None:
        """
        Sets the name of this association.<br>
        Shortcut for <code>get_property(PROPERTY_NAME).set_value()</code>.
        
        Property opendma:Name: String
        [SingleValue] [Writable] [Required]
        This name is used to refer to this specific association in the context of it's container and tell tem apart. Many systems pose additional constraints on this name.
        
        :param new_value: the new value for the name of this association
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_container(self) -> "OdmaContainer":
        """
        Returns the source of this directed link.<br>
        Shortcut for <code>get_property(PROPERTY_CONTAINER).get_reference()</code>.
        
        Property opendma:Container: Reference to Container (opendma)
        [SingleValue] [Writable] [Required]
        
        :return: the source of this directed link
        """
        pass

    @abstractmethod
    def set_container(self, new_value: "OdmaContainer") -> None:
        """
        Sets the source of this directed link.<br>
        Shortcut for <code>get_property(PROPERTY_CONTAINER).set_value()</code>.
        
        Property opendma:Container: Reference to Container (opendma)
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for the source of this directed link
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass

    @abstractmethod
    def get_containable(self) -> "OdmaContainable":
        """
        Returns the destination of this directed link.<br>
        Shortcut for <code>get_property(PROPERTY_CONTAINABLE).get_reference()</code>.
        
        Property opendma:Containable: Reference to Containable (opendma)
        [SingleValue] [Writable] [Required]
        
        :return: the destination of this directed link
        """
        pass

    @abstractmethod
    def set_containable(self, new_value: "OdmaContainable") -> None:
        """
        Sets the destination of this directed link.<br>
        Shortcut for <code>get_property(PROPERTY_CONTAINABLE).set_value()</code>.
        
        Property opendma:Containable: Reference to Containable (opendma)
        [SingleValue] [Writable] [Required]
        
        :param new_value: the new value for the destination of this directed link
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        pass


from typing import Any, Optional, Protocol
from datetime import datetime

class LazyPropertyValueProvider(Protocol):
    """
    Interface for lazy property resolution.
    """
    
    def has_reference_id(self) -> bool:
        """
        Indicates if the OdmaId of a referenced object is available without a round-trip to a back-end system.
        """
        ...

    def get_reference_id(self) -> Optional[OdmaId]:
        """
        Get the OdmaId of a referenced object, if available. Returns None otherwise.
        """
        ...
    
    def resolve_property_value(self) -> Any:
        """
        Resolves the value of the property when accessed.
        """
        ...

class OdmaPropertyImpl(OdmaProperty):
    """
    Standard implementation of the OdmaProperty interface.
    """

    def __init__(self, name: OdmaQName, value: Optional[Any], value_provider: Optional[LazyPropertyValueProvider], data_type: OdmaType, multi_value: bool, read_only: bool):
        self._name = name
        self._data_type = data_type
        self._multi_value = multi_value
        self._read_only = read_only
        if value_provider is not None:
            if value is not None:
                raise ValueError("If a value provider is given, the value must be None.")
            if not callable(getattr(value_provider, "resolve_property_value", None)):
                raise TypeError("value_provider must implement `resolve_property_value()`")
            self._value_provider = value_provider
        else:
            self._value_provider = None
            self._set_value_internal(value)
            self._dirty = False


    def get_name(self) -> OdmaQName:
        """
        Returns the qualified name of this property.

        :return: The qualified name of this property.
        """
        return self._name

    def get_type(self) -> OdmaType:
        """
        Returns the data type of this property.
        
        :return: The data type of this property.
        """
        return self._data_type

    def _enforce_value(self):
        if self._value_provider is not None:
            try:
                resolved_value = self._value_provider.resolve_property_value()
                self._set_value_internal(resolved_value)
                self._value_provider = None
                self._dirty = False
            except OdmaInvalidDataTypeException as e:
                raise OdmaServiceException("Lazy property resolution failed. Provider delivered wrong type or cardinality.") from e

    def get_value(self) -> Any:
        """
        Returns the value of this property. The concrete object returned
        by this method depends on the data type of this property.

        :return: The value of this property.
        """
        self._enforce_value()
        return self._value

    def is_multi_value(self) -> bool:
        """
        Checks if this property is a multi-value property.
        
        :return: `True` if and only if this property is a multi value property.
        """
        return self._multi_value

    def is_dirty(self) -> bool:
        """
        Checks if this property has unsaved changes.
        
        :return: `True` if and only if this property has unsaved changes.
        """
        return self._dirty

    def is_read_only(self) -> bool:
        """
        Checks if this property is read-only.
        
        :return: `True` if and only if this property is read-only.
        """
        return self._read_only

    def get_resolution_state(self) -> PropertyResolutionState:
        """
        Indicates if the value of this property is immediately available can be read without a round-trip to a back-end system.
        
        :return: the availability state of this property value.
        """
        if self._value_provider is None:
            return PropertyResolutionState.RESOLVED
        elif self._value_provider.has_reference_id():
            return PropertyResolutionState.IDRESOLVED
        else:
            return PropertyResolutionState.UNRESOLVED

    def set_value(self, new_value: Any) -> None:
        """
        Sets the value of this property. The type and classof the given
        new_value has to match the data type of this OdmaProperty.

        :param new_value: the new value to set this property to.
        :raises OdmaInvalidDataTypeException: Raised if the type of the assigned value does not match the data type of this OdmaProperty.
        :raises OdmaAccessDeniedException: Raised if this OdmaProperty is read-only or cannot be set by the current user.
        """
        if self._read_only:
            raise OdmaAccessDeniedException("Cannot modify a read-only property.")
        self._set_value_internal(new_value)
        self._value_provider = None

    def _set_value_internal(self, new_value: Any) -> None:
        if new_value is None:
            if self._multi_value:
                raise OdmaInvalidDataTypeException("Multi-valued properties must not be `null`. If a value is not required, the collection can be empty.");
            self._value = None
            self._dirty = True
            return
        if self._multi_value:
            match self._data_type:
                case OdmaType.STRING:
                    if isinstance(new_value, list) and all(isinstance(item, str) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued String data type. It can only be set to values assignable to `list[str]` but got "+type(new_value).__name__);
                case OdmaType.INTEGER:
                    if isinstance(new_value, list) and all(isinstance(item, int) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Integer data type. It can only be set to values assignable to `list[int]` but got "+type(new_value).__name__);
                case OdmaType.SHORT:
                    if isinstance(new_value, list) and all(isinstance(item, int) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Short data type. It can only be set to values assignable to `list[int]` but got "+type(new_value).__name__);
                case OdmaType.LONG:
                    if isinstance(new_value, list) and all(isinstance(item, int) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Long data type. It can only be set to values assignable to `list[int]` but got "+type(new_value).__name__);
                case OdmaType.FLOAT:
                    if isinstance(new_value, list) and all(isinstance(item, float) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Float data type. It can only be set to values assignable to `list[float]` but got "+type(new_value).__name__);
                case OdmaType.DOUBLE:
                    if isinstance(new_value, list) and all(isinstance(item, float) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Double data type. It can only be set to values assignable to `list[float]` but got "+type(new_value).__name__);
                case OdmaType.BOOLEAN:
                    if isinstance(new_value, list) and all(isinstance(item, bool) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Boolean data type. It can only be set to values assignable to `list[bool]` but got "+type(new_value).__name__);
                case OdmaType.DATETIME:
                    if isinstance(new_value, list) and all(isinstance(item, datetime) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued DateTime data type. It can only be set to values assignable to `list[datetime]` but got "+type(new_value).__name__);
                case OdmaType.BINARY:
                    if isinstance(new_value, list) and all(isinstance(item, bytes) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Binary data type. It can only be set to values assignable to `list[bytes]` but got "+type(new_value).__name__);
                case OdmaType.REFERENCE:
                    if isinstance(new_value, Iterable):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Reference data type. It can only be set to values assignable to `Iterable[TOdmaObject]` but got "+type(new_value).__name__);
                case OdmaType.CONTENT:
                    if isinstance(new_value, list) and all(isinstance(item, OdmaContent) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Content data type. It can only be set to values assignable to `list[OdmaContent]` but got "+type(new_value).__name__);
                case OdmaType.ID:
                    if isinstance(new_value, list) and all(isinstance(item, OdmaId) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Id data type. It can only be set to values assignable to `list[OdmaId]` but got "+type(new_value).__name__);
                case OdmaType.GUID:
                    if isinstance(new_value, list) and all(isinstance(item, OdmaGuid) for item in new_value):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a multi-valued Guid data type. It can only be set to values assignable to `list[OdmaGuid]` but got "+type(new_value).__name__);
                case _:
                    raise OdmaException("OdmaProperty initialized with unknown data type "+self.data_type);
        else:
            match self._data_type:
                case OdmaType.STRING:
                    if isinstance(new_value, str):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued String data type. It can only be set to values assignable to `Optional[str]` but got "+type(new_value).__name__);
                case OdmaType.INTEGER:
                    if isinstance(new_value, int):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Integer data type. It can only be set to values assignable to `Optional[int]` but got "+type(new_value).__name__);
                case OdmaType.SHORT:
                    if isinstance(new_value, int):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Short data type. It can only be set to values assignable to `Optional[int]` but got "+type(new_value).__name__);
                case OdmaType.LONG:
                    if isinstance(new_value, int):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Long data type. It can only be set to values assignable to `Optional[int]` but got "+type(new_value).__name__);
                case OdmaType.FLOAT:
                    if isinstance(new_value, float):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Float data type. It can only be set to values assignable to `Optional[float]` but got "+type(new_value).__name__);
                case OdmaType.DOUBLE:
                    if isinstance(new_value, float):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Double data type. It can only be set to values assignable to `Optional[float]` but got "+type(new_value).__name__);
                case OdmaType.BOOLEAN:
                    if isinstance(new_value, bool):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Boolean data type. It can only be set to values assignable to `Optional[bool]` but got "+type(new_value).__name__);
                case OdmaType.DATETIME:
                    if isinstance(new_value, datetime):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued DateTime data type. It can only be set to values assignable to `Optional[datetime]` but got "+type(new_value).__name__);
                case OdmaType.BINARY:
                    if isinstance(new_value, bytes):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Binary data type. It can only be set to values assignable to `Optional[bytes]` but got "+type(new_value).__name__);
                case OdmaType.REFERENCE:
                    if isinstance(new_value, OdmaObject):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Reference data type. It can only be set to values assignable to `OdmaObject` but got "+type(new_value).__name__);
                case OdmaType.CONTENT:
                    if isinstance(new_value, OdmaContent):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Content data type. It can only be set to values assignable to `Optional[OdmaContent]` but got "+type(new_value).__name__);
                case OdmaType.ID:
                    if isinstance(new_value, OdmaId):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Id data type. It can only be set to values assignable to `Optional[OdmaId]` but got "+type(new_value).__name__);
                case OdmaType.GUID:
                    if isinstance(new_value, OdmaGuid):
                        self._value = new_value
                    else:
                        raise OdmaInvalidDataTypeException("This property has a single-valued Guid data type. It can only be set to values assignable to `Optional[OdmaGuid]` but got "+type(new_value).__name__);
                case _:
                    raise OdmaException("OdmaProperty initialized with unknown data type "+self.data_type);
        self._dirty = True

    def get_string(self) -> Optional[str]:
        """ Retrieves the String value of this property if and only if
        the data type of this property is a single valued String.
        """
        if self._multi_value == False and self._data_type == OdmaType.STRING:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_string(self)`");

    def get_integer(self) -> Optional[int]:
        """ Retrieves the Integer value of this property if and only if
        the data type of this property is a single valued Integer.
        """
        if self._multi_value == False and self._data_type == OdmaType.INTEGER:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_integer(self)`");

    def get_short(self) -> Optional[int]:
        """ Retrieves the Short value of this property if and only if
        the data type of this property is a single valued Short.
        """
        if self._multi_value == False and self._data_type == OdmaType.SHORT:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_short(self)`");

    def get_long(self) -> Optional[int]:
        """ Retrieves the Long value of this property if and only if
        the data type of this property is a single valued Long.
        """
        if self._multi_value == False and self._data_type == OdmaType.LONG:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_long(self)`");

    def get_float(self) -> Optional[float]:
        """ Retrieves the Float value of this property if and only if
        the data type of this property is a single valued Float.
        """
        if self._multi_value == False and self._data_type == OdmaType.FLOAT:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_float(self)`");

    def get_double(self) -> Optional[float]:
        """ Retrieves the Double value of this property if and only if
        the data type of this property is a single valued Double.
        """
        if self._multi_value == False and self._data_type == OdmaType.DOUBLE:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_double(self)`");

    def get_boolean(self) -> Optional[bool]:
        """ Retrieves the Boolean value of this property if and only if
        the data type of this property is a single valued Boolean.
        """
        if self._multi_value == False and self._data_type == OdmaType.BOOLEAN:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_boolean(self)`");

    def get_datetime(self) -> Optional[datetime]:
        """ Retrieves the DateTime value of this property if and only if
        the data type of this property is a single valued DateTime.
        """
        if self._multi_value == False and self._data_type == OdmaType.DATETIME:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_datetime(self)`");

    def get_binary(self) -> Optional[bytes]:
        """ Retrieves the Binary value of this property if and only if
        the data type of this property is a single valued Binary.
        """
        if self._multi_value == False and self._data_type == OdmaType.BINARY:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_binary(self)`");

    def get_reference(self) -> Optional[TOdmaObject]:
        """ Retrieves the Reference value of this property if and only if
        the data type of this property is a single valued Reference.
        """
        if self._multi_value == False and self._data_type == OdmaType.REFERENCE:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_reference(self)`");

    def get_reference_id(self) -> Optional[OdmaId]:
        """ Retrieves the OdmaId of the Reference value of this property if and only if
        the data type of this property is a single valued Reference.
        
        Based on the PropertyResolutionState, it is possible that this OdmaId is immediately available
        while the OdmaObject requires an additional round-trip to the server.
        """
        if self._multi_value == False and self._data_type == OdmaType.REFERENCE:
            if self._value_provider is None:
                if self._value is not None:
                    if isinstance(self._value, OdmaObject):
                        return self._value.get_id()
                    else:
                        raise OdmaException("Internal error. Reference value is expected to be instance of OdmaObject")
                else:
                    return None
            elif self._value_provider.has_reference_id():
                return self._value_provider.get_reference_id()
            else:
                self._enforce_value()
                if self._value is not None:
                    if isinstance(self._value, OdmaObject):
                        return self._value.get_id()
                    else:
                        raise OdmaException("Internal error. Reference value is expected to be instance of OdmaObject")
                else:
                    return None
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_reference(self)`");

    def get_content(self) -> Optional[OdmaContent]:
        """ Retrieves the Content value of this property if and only if
        the data type of this property is a single valued Content.
        """
        if self._multi_value == False and self._data_type == OdmaType.CONTENT:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_content(self)`");

    def get_id(self) -> Optional[OdmaId]:
        """ Retrieves the Id value of this property if and only if
        the data type of this property is a single valued Id.
        """
        if self._multi_value == False and self._data_type == OdmaType.ID:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_id(self)`");

    def get_guid(self) -> Optional[OdmaGuid]:
        """ Retrieves the Guid value of this property if and only if
        the data type of this property is a single valued Guid.
        """
        if self._multi_value == False and self._data_type == OdmaType.GUID:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_guid(self)`");

    def get_string_list(self) -> list[str]:
        """ Retrieves the String value of this property if and only if
        the data type of this property is a multi valued String.
        """
        if self._multi_value == True and self._data_type == OdmaType.STRING:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_string_list(self)`");

    def get_integer_list(self) -> list[int]:
        """ Retrieves the Integer value of this property if and only if
        the data type of this property is a multi valued Integer.
        """
        if self._multi_value == True and self._data_type == OdmaType.INTEGER:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_integer_list(self)`");

    def get_short_list(self) -> list[int]:
        """ Retrieves the Short value of this property if and only if
        the data type of this property is a multi valued Short.
        """
        if self._multi_value == True and self._data_type == OdmaType.SHORT:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_short_list(self)`");

    def get_long_list(self) -> list[int]:
        """ Retrieves the Long value of this property if and only if
        the data type of this property is a multi valued Long.
        """
        if self._multi_value == True and self._data_type == OdmaType.LONG:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_long_list(self)`");

    def get_float_list(self) -> list[float]:
        """ Retrieves the Float value of this property if and only if
        the data type of this property is a multi valued Float.
        """
        if self._multi_value == True and self._data_type == OdmaType.FLOAT:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_float_list(self)`");

    def get_double_list(self) -> list[float]:
        """ Retrieves the Double value of this property if and only if
        the data type of this property is a multi valued Double.
        """
        if self._multi_value == True and self._data_type == OdmaType.DOUBLE:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_double_list(self)`");

    def get_boolean_list(self) -> list[bool]:
        """ Retrieves the Boolean value of this property if and only if
        the data type of this property is a multi valued Boolean.
        """
        if self._multi_value == True and self._data_type == OdmaType.BOOLEAN:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_boolean_list(self)`");

    def get_datetime_list(self) -> list[datetime]:
        """ Retrieves the DateTime value of this property if and only if
        the data type of this property is a multi valued DateTime.
        """
        if self._multi_value == True and self._data_type == OdmaType.DATETIME:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_datetime_list(self)`");

    def get_binary_list(self) -> list[bytes]:
        """ Retrieves the Binary value of this property if and only if
        the data type of this property is a multi valued Binary.
        """
        if self._multi_value == True and self._data_type == OdmaType.BINARY:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_binary_list(self)`");

    def get_reference_iterable(self) -> Iterable[TOdmaObject]:
        """ Retrieves the Reference value of this property if and only if
        the data type of this property is a multi valued Reference.
        """
        if self._multi_value == True and self._data_type == OdmaType.REFERENCE:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_reference_list(self)`");

    def get_content_list(self) -> list[OdmaContent]:
        """ Retrieves the Content value of this property if and only if
        the data type of this property is a multi valued Content.
        """
        if self._multi_value == True and self._data_type == OdmaType.CONTENT:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_content_list(self)`");

    def get_id_list(self) -> list[OdmaId]:
        """ Retrieves the Id value of this property if and only if
        the data type of this property is a multi valued Id.
        """
        if self._multi_value == True and self._data_type == OdmaType.ID:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_id_list(self)`");

    def get_guid_list(self) -> list[OdmaGuid]:
        """ Retrieves the Guid value of this property if and only if
        the data type of this property is a multi valued Guid.
        """
        if self._multi_value == True and self._data_type == OdmaType.GUID:
            self._enforce_value()
            return self._value  # type: ignore[return-value]
        raise OdmaInvalidDataTypeException("This property has a different data type and/or cardinality. It cannot return values with `get_guid_list(self)`");

from . import constants
from .helpers import OdmaServiceException
from typing import Type

def prune_inheritance_chain(classes: list[type]) -> list[type]:
    pruned = []
    for cls in classes:
        if not any(issubclass(other, cls) for other in classes if other is not cls):
            pruned.append(cls)
    return pruned

def odma_create_proxy(odma_interfaces: list[OdmaQName], core: OdmaCoreObject) -> OdmaObject:

    def get_property(self, property_name: OdmaQName) -> OdmaProperty:
        return core.get_property(property_name)

    def prepare_properties(self, property_names: Optional[list[OdmaQName]], refresh: bool) -> None:
        core.prepare_properties(property_names, refresh)

    def set_property(self, property_name: OdmaQName, new_value: Any) -> None:
        core.set_property(property_name, new_value)

    def is_dirty(self) -> bool:
        return core.is_dirty()

    def save(self) -> None:
        core.save()

    def instance_of(self, class_or_aspect_name: OdmaQName) -> bool:
        return core.instance_of(class_or_aspect_name)

    def get_qname(self) -> OdmaQName:
        return OdmaQName(self.get_namespace(), self.get_name())

    dict = {
        "get_property": get_property,
        "prepare_properties": prepare_properties,
        "set_property": set_property,
        "is_dirty": is_dirty,
        "save": save,
        "instance_of": instance_of,
        "get_qname": get_qname,
    }

    def get_odma_class(self) -> "OdmaClass":
        try:
            result = core.get_property(constants.PROPERTY_CLASS).get_reference()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Class is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Class")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Class")

    def get_aspects(self) -> Iterable[TOdmaClass]:
        try:
            return core.get_property(constants.PROPERTY_ASPECTS).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Aspects")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Aspects")

    def get_id(self) -> OdmaId:
        try:
            result = core.get_property(constants.PROPERTY_ID).get_id()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Id is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Id")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Id")

    def get_guid(self) -> OdmaGuid:
        try:
            result = core.get_property(constants.PROPERTY_GUID).get_guid()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Guid is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Guid")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Guid")

    def get_repository(self) -> "OdmaRepository":
        try:
            result = core.get_property(constants.PROPERTY_REPOSITORY).get_reference()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Repository is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Repository")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Repository")

    dict_odma_object = {
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_name(self) -> str:
        try:
            result = core.get_property(constants.PROPERTY_NAME).get_string()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Name is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Name")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Name")

    def set_name(self, new_value: str) -> None:
        try:
            core.get_property(constants.PROPERTY_NAME).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Name")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Name")

    def get_namespace(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_NAMESPACE).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Namespace")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Namespace")

    def set_namespace(self, new_value: Optional[str]) -> None:
        try:
            core.get_property(constants.PROPERTY_NAMESPACE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Namespace")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Namespace")

    def get_display_name(self) -> str:
        try:
            result = core.get_property(constants.PROPERTY_DISPLAYNAME).get_string()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:DisplayName is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DisplayName")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DisplayName")

    def set_display_name(self, new_value: str) -> None:
        try:
            core.get_property(constants.PROPERTY_DISPLAYNAME).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DisplayName")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DisplayName")

    def get_super_class(self) -> Optional["OdmaClass"]:
        try:
            return core.get_property(constants.PROPERTY_SUPERCLASS).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:SuperClass")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:SuperClass")

    def get_included_aspects(self) -> Iterable[TOdmaClass]:
        try:
            return core.get_property(constants.PROPERTY_INCLUDEDASPECTS).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:IncludedAspects")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:IncludedAspects")

    def set_included_aspects(self, new_value: Iterable[TOdmaClass]) -> None:
        try:
            core.get_property(constants.PROPERTY_INCLUDEDASPECTS).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:IncludedAspects")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:IncludedAspects")

    def get_declared_properties(self) -> Iterable[TOdmaPropertyInfo]:
        try:
            return core.get_property(constants.PROPERTY_DECLAREDPROPERTIES).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DeclaredProperties")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DeclaredProperties")

    def set_declared_properties(self, new_value: Iterable[TOdmaPropertyInfo]) -> None:
        try:
            core.get_property(constants.PROPERTY_DECLAREDPROPERTIES).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DeclaredProperties")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DeclaredProperties")

    def get_properties(self) -> Iterable[TOdmaPropertyInfo]:
        try:
            return core.get_property(constants.PROPERTY_PROPERTIES).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Properties")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Properties")

    def get_aspect(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_ASPECT).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Aspect is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Aspect")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Aspect")

    def get_hidden(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_HIDDEN).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Hidden is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Hidden")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Hidden")

    def set_hidden(self, new_value: bool) -> None:
        try:
            core.get_property(constants.PROPERTY_HIDDEN).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Hidden")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Hidden")

    def get_system(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_SYSTEM).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:System is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:System")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:System")

    def set_system(self, new_value: bool) -> None:
        try:
            core.get_property(constants.PROPERTY_SYSTEM).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:System")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:System")

    def get_retrievable(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_RETRIEVABLE).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Retrievable is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Retrievable")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Retrievable")

    def get_searchable(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_SEARCHABLE).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Searchable is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Searchable")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Searchable")

    def get_sub_classes(self) -> Iterable[TOdmaClass]:
        try:
            return core.get_property(constants.PROPERTY_SUBCLASSES).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:SubClasses")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:SubClasses")

    dict_odma_class = {
        "get_name": get_name,
        "set_name": set_name,
        "get_namespace": get_namespace,
        "set_namespace": set_namespace,
        "get_display_name": get_display_name,
        "set_display_name": set_display_name,
        "get_super_class": get_super_class,
        "get_included_aspects": get_included_aspects,
        "set_included_aspects": set_included_aspects,
        "get_declared_properties": get_declared_properties,
        "set_declared_properties": set_declared_properties,
        "get_properties": get_properties,
        "get_aspect": get_aspect,
        "get_hidden": get_hidden,
        "set_hidden": set_hidden,
        "get_system": get_system,
        "set_system": set_system,
        "get_retrievable": get_retrievable,
        "get_searchable": get_searchable,
        "get_sub_classes": get_sub_classes,
        "get_qname": lambda self: OdmaQName(self.get_namespace(), self.get_name()),
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    # Omit double definition of def get_name(self):

    # Omit double definition of def set_name(self):

    # Omit double definition of def get_namespace(self):

    # Omit double definition of def set_namespace(self):

    # Omit double definition of def get_display_name(self):

    # Omit double definition of def set_display_name(self):

    def get_data_type(self) -> int:
        try:
            result = core.get_property(constants.PROPERTY_DATATYPE).get_integer()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:DataType is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DataType")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DataType")

    def set_data_type(self, new_value: int) -> None:
        try:
            core.get_property(constants.PROPERTY_DATATYPE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DataType")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DataType")

    def get_reference_class(self) -> Optional["OdmaClass"]:
        try:
            return core.get_property(constants.PROPERTY_REFERENCECLASS).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ReferenceClass")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ReferenceClass")

    def set_reference_class(self, new_value: Optional["OdmaClass"]) -> None:
        try:
            core.get_property(constants.PROPERTY_REFERENCECLASS).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ReferenceClass")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ReferenceClass")

    def get_multi_value(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_MULTIVALUE).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:MultiValue is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:MultiValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:MultiValue")

    def set_multi_value(self, new_value: bool) -> None:
        try:
            core.get_property(constants.PROPERTY_MULTIVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:MultiValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:MultiValue")

    def get_required(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_REQUIRED).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Required is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Required")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Required")

    def set_required(self, new_value: bool) -> None:
        try:
            core.get_property(constants.PROPERTY_REQUIRED).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Required")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Required")

    def get_read_only(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_READONLY).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:ReadOnly is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ReadOnly")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ReadOnly")

    def set_read_only(self, new_value: bool) -> None:
        try:
            core.get_property(constants.PROPERTY_READONLY).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ReadOnly")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ReadOnly")

    # Omit double definition of def get_hidden(self):

    # Omit double definition of def set_hidden(self):

    # Omit double definition of def get_system(self):

    # Omit double definition of def set_system(self):

    def get_choices(self) -> Iterable[TOdmaChoiceValue]:
        try:
            return core.get_property(constants.PROPERTY_CHOICES).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Choices")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Choices")

    def set_choices(self, new_value: Iterable[TOdmaChoiceValue]) -> None:
        try:
            core.get_property(constants.PROPERTY_CHOICES).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Choices")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Choices")

    dict_odma_property_info = {
        "get_name": get_name,
        "set_name": set_name,
        "get_namespace": get_namespace,
        "set_namespace": set_namespace,
        "get_display_name": get_display_name,
        "set_display_name": set_display_name,
        "get_data_type": get_data_type,
        "set_data_type": set_data_type,
        "get_reference_class": get_reference_class,
        "set_reference_class": set_reference_class,
        "get_multi_value": get_multi_value,
        "set_multi_value": set_multi_value,
        "get_required": get_required,
        "set_required": set_required,
        "get_read_only": get_read_only,
        "set_read_only": set_read_only,
        "get_hidden": get_hidden,
        "set_hidden": set_hidden,
        "get_system": get_system,
        "set_system": set_system,
        "get_choices": get_choices,
        "set_choices": set_choices,
        "get_qname": lambda self: OdmaQName(self.get_namespace(), self.get_name()),
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    # Omit double definition of def get_display_name(self):

    # Omit double definition of def set_display_name(self):

    def get_string_value(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_STRINGVALUE).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:StringValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:StringValue")

    def set_string_value(self, new_value: Optional[str]) -> None:
        try:
            core.get_property(constants.PROPERTY_STRINGVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:StringValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:StringValue")

    def get_integer_value(self) -> Optional[int]:
        try:
            return core.get_property(constants.PROPERTY_INTEGERVALUE).get_integer()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:IntegerValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:IntegerValue")

    def set_integer_value(self, new_value: Optional[int]) -> None:
        try:
            core.get_property(constants.PROPERTY_INTEGERVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:IntegerValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:IntegerValue")

    def get_short_value(self) -> Optional[int]:
        try:
            return core.get_property(constants.PROPERTY_SHORTVALUE).get_short()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ShortValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ShortValue")

    def set_short_value(self, new_value: Optional[int]) -> None:
        try:
            core.get_property(constants.PROPERTY_SHORTVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ShortValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ShortValue")

    def get_long_value(self) -> Optional[int]:
        try:
            return core.get_property(constants.PROPERTY_LONGVALUE).get_long()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:LongValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:LongValue")

    def set_long_value(self, new_value: Optional[int]) -> None:
        try:
            core.get_property(constants.PROPERTY_LONGVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:LongValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:LongValue")

    def get_float_value(self) -> Optional[float]:
        try:
            return core.get_property(constants.PROPERTY_FLOATVALUE).get_float()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:FloatValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:FloatValue")

    def set_float_value(self, new_value: Optional[float]) -> None:
        try:
            core.get_property(constants.PROPERTY_FLOATVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:FloatValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:FloatValue")

    def get_double_value(self) -> Optional[float]:
        try:
            return core.get_property(constants.PROPERTY_DOUBLEVALUE).get_double()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DoubleValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DoubleValue")

    def set_double_value(self, new_value: Optional[float]) -> None:
        try:
            core.get_property(constants.PROPERTY_DOUBLEVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DoubleValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DoubleValue")

    def get_boolean_value(self) -> Optional[bool]:
        try:
            return core.get_property(constants.PROPERTY_BOOLEANVALUE).get_boolean()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:BooleanValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:BooleanValue")

    def set_boolean_value(self, new_value: Optional[bool]) -> None:
        try:
            core.get_property(constants.PROPERTY_BOOLEANVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:BooleanValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:BooleanValue")

    def get_date_time_value(self) -> Optional[datetime]:
        try:
            return core.get_property(constants.PROPERTY_DATETIMEVALUE).get_datetime()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DateTimeValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DateTimeValue")

    def set_date_time_value(self, new_value: Optional[datetime]) -> None:
        try:
            core.get_property(constants.PROPERTY_DATETIMEVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:DateTimeValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:DateTimeValue")

    def get_binary_value(self) -> Optional[bytes]:
        try:
            return core.get_property(constants.PROPERTY_BINARYVALUE).get_binary()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:BinaryValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:BinaryValue")

    def set_binary_value(self, new_value: Optional[bytes]) -> None:
        try:
            core.get_property(constants.PROPERTY_BINARYVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:BinaryValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:BinaryValue")

    def get_reference_value(self) -> Optional["OdmaObject"]:
        try:
            return core.get_property(constants.PROPERTY_REFERENCEVALUE).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ReferenceValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ReferenceValue")

    def set_reference_value(self, new_value: Optional["OdmaObject"]) -> None:
        try:
            core.get_property(constants.PROPERTY_REFERENCEVALUE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ReferenceValue")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ReferenceValue")

    dict_odma_choice_value = {
        "get_display_name": get_display_name,
        "set_display_name": set_display_name,
        "get_string_value": get_string_value,
        "set_string_value": set_string_value,
        "get_integer_value": get_integer_value,
        "set_integer_value": set_integer_value,
        "get_short_value": get_short_value,
        "set_short_value": set_short_value,
        "get_long_value": get_long_value,
        "set_long_value": set_long_value,
        "get_float_value": get_float_value,
        "set_float_value": set_float_value,
        "get_double_value": get_double_value,
        "set_double_value": set_double_value,
        "get_boolean_value": get_boolean_value,
        "set_boolean_value": set_boolean_value,
        "get_date_time_value": get_date_time_value,
        "set_date_time_value": set_date_time_value,
        "get_binary_value": get_binary_value,
        "set_binary_value": set_binary_value,
        "get_reference_value": get_reference_value,
        "set_reference_value": set_reference_value,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    # Omit double definition of def get_name(self):

    # Omit double definition of def set_name(self):

    # Omit double definition of def get_display_name(self):

    # Omit double definition of def set_display_name(self):

    def get_root_class(self) -> "OdmaClass":
        try:
            result = core.get_property(constants.PROPERTY_ROOTCLASS).get_reference()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:RootClass is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:RootClass")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:RootClass")

    def get_root_aspects(self) -> Iterable[TOdmaClass]:
        try:
            return core.get_property(constants.PROPERTY_ROOTASPECTS).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:RootAspects")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:RootAspects")

    def get_root_folder(self) -> Optional["OdmaFolder"]:
        try:
            return core.get_property(constants.PROPERTY_ROOTFOLDER).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:RootFolder")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:RootFolder")

    dict_odma_repository = {
        "get_name": get_name,
        "set_name": set_name,
        "get_display_name": get_display_name,
        "set_display_name": set_display_name,
        "get_root_class": get_root_class,
        "get_root_aspects": get_root_aspects,
        "get_root_folder": get_root_folder,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_created_at(self) -> Optional[datetime]:
        try:
            return core.get_property(constants.PROPERTY_CREATEDAT).get_datetime()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:CreatedAt")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:CreatedAt")

    def get_created_by(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_CREATEDBY).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:CreatedBy")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:CreatedBy")

    def get_last_modified_at(self) -> Optional[datetime]:
        try:
            return core.get_property(constants.PROPERTY_LASTMODIFIEDAT).get_datetime()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:LastModifiedAt")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:LastModifiedAt")

    def get_last_modified_by(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_LASTMODIFIEDBY).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:LastModifiedBy")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:LastModifiedBy")

    dict_odma_audit_stamped = {
        "get_created_at": get_created_at,
        "get_created_by": get_created_by,
        "get_last_modified_at": get_last_modified_at,
        "get_last_modified_by": get_last_modified_by,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_title(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_TITLE).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Title")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Title")

    def set_title(self, new_value: Optional[str]) -> None:
        try:
            core.get_property(constants.PROPERTY_TITLE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Title")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Title")

    def get_version(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_VERSION).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Version")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Version")

    def get_version_collection(self) -> Optional["OdmaVersionCollection"]:
        try:
            return core.get_property(constants.PROPERTY_VERSIONCOLLECTION).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:VersionCollection")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:VersionCollection")

    def get_version_independent_id(self) -> OdmaId:
        try:
            result = core.get_property(constants.PROPERTY_VERSIONINDEPENDENTID).get_id()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:VersionIndependentId is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:VersionIndependentId")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:VersionIndependentId")

    def get_version_independent_guid(self) -> OdmaGuid:
        try:
            result = core.get_property(constants.PROPERTY_VERSIONINDEPENDENTGUID).get_guid()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:VersionIndependentGuid is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:VersionIndependentGuid")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:VersionIndependentGuid")

    def get_content_elements(self) -> Iterable[TOdmaContentElement]:
        try:
            return core.get_property(constants.PROPERTY_CONTENTELEMENTS).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ContentElements")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ContentElements")

    def set_content_elements(self, new_value: Iterable[TOdmaContentElement]) -> None:
        try:
            core.get_property(constants.PROPERTY_CONTENTELEMENTS).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ContentElements")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ContentElements")

    def get_combined_content_type(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_COMBINEDCONTENTTYPE).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:CombinedContentType")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:CombinedContentType")

    def set_combined_content_type(self, new_value: Optional[str]) -> None:
        try:
            core.get_property(constants.PROPERTY_COMBINEDCONTENTTYPE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:CombinedContentType")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:CombinedContentType")

    def get_primary_content_element(self) -> Optional["OdmaContentElement"]:
        try:
            return core.get_property(constants.PROPERTY_PRIMARYCONTENTELEMENT).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:PrimaryContentElement")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:PrimaryContentElement")

    def set_primary_content_element(self, new_value: Optional["OdmaContentElement"]) -> None:
        try:
            core.get_property(constants.PROPERTY_PRIMARYCONTENTELEMENT).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:PrimaryContentElement")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:PrimaryContentElement")

    def get_checked_out(self) -> bool:
        try:
            result = core.get_property(constants.PROPERTY_CHECKEDOUT).get_boolean()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:CheckedOut is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:CheckedOut")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:CheckedOut")

    def get_checked_out_at(self) -> Optional[datetime]:
        try:
            return core.get_property(constants.PROPERTY_CHECKEDOUTAT).get_datetime()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:CheckedOutAt")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:CheckedOutAt")

    def get_checked_out_by(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_CHECKEDOUTBY).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:CheckedOutBy")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:CheckedOutBy")

    dict_odma_document = {
        "get_title": get_title,
        "set_title": set_title,
        "get_version": get_version,
        "get_version_collection": get_version_collection,
        "get_version_independent_id": get_version_independent_id,
        "get_version_independent_guid": get_version_independent_guid,
        "get_content_elements": get_content_elements,
        "set_content_elements": set_content_elements,
        "get_combined_content_type": get_combined_content_type,
        "set_combined_content_type": set_combined_content_type,
        "get_primary_content_element": get_primary_content_element,
        "set_primary_content_element": set_primary_content_element,
        "get_checked_out": get_checked_out,
        "get_checked_out_at": get_checked_out_at,
        "get_checked_out_by": get_checked_out_by,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_content_type(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_CONTENTTYPE).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ContentType")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ContentType")

    def set_content_type(self, new_value: Optional[str]) -> None:
        try:
            core.get_property(constants.PROPERTY_CONTENTTYPE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ContentType")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ContentType")

    def get_position(self) -> Optional[int]:
        try:
            return core.get_property(constants.PROPERTY_POSITION).get_integer()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Position")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Position")

    dict_odma_content_element = {
        "get_content_type": get_content_type,
        "set_content_type": set_content_type,
        "get_position": get_position,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_content(self) -> Optional[OdmaContent]:
        try:
            return core.get_property(constants.PROPERTY_CONTENT).get_content()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Content")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Content")

    def set_content(self, new_value: Optional[OdmaContent]) -> None:
        try:
            core.get_property(constants.PROPERTY_CONTENT).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Content")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Content")

    def get_size(self) -> Optional[int]:
        try:
            return core.get_property(constants.PROPERTY_SIZE).get_long()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Size")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Size")

    def get_file_name(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_FILENAME).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:FileName")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:FileName")

    def set_file_name(self, new_value: Optional[str]) -> None:
        try:
            core.get_property(constants.PROPERTY_FILENAME).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:FileName")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:FileName")

    dict_odma_data_content_element = {
        "get_content": get_content,
        "set_content": set_content,
        "get_size": get_size,
        "get_file_name": get_file_name,
        "set_file_name": set_file_name,
        "get_content_type": get_content_type,
        "set_content_type": set_content_type,
        "get_position": get_position,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_location(self) -> Optional[str]:
        try:
            return core.get_property(constants.PROPERTY_LOCATION).get_string()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Location")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Location")

    def set_location(self, new_value: Optional[str]) -> None:
        try:
            core.get_property(constants.PROPERTY_LOCATION).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Location")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Location")

    dict_odma_reference_content_element = {
        "get_location": get_location,
        "set_location": set_location,
        "get_content_type": get_content_type,
        "set_content_type": set_content_type,
        "get_position": get_position,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_versions(self) -> Iterable[TOdmaDocument]:
        try:
            result = core.get_property(constants.PROPERTY_VERSIONS).get_reference_iterable()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Versions is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Versions")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Versions")

    def get_latest(self) -> Optional["OdmaDocument"]:
        try:
            return core.get_property(constants.PROPERTY_LATEST).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Latest")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Latest")

    def get_released(self) -> Optional["OdmaDocument"]:
        try:
            return core.get_property(constants.PROPERTY_RELEASED).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Released")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Released")

    def get_in_progress(self) -> Optional["OdmaDocument"]:
        try:
            return core.get_property(constants.PROPERTY_INPROGRESS).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:InProgress")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:InProgress")

    dict_odma_version_collection = {
        "get_versions": get_versions,
        "get_latest": get_latest,
        "get_released": get_released,
        "get_in_progress": get_in_progress,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    # Omit double definition of def get_title(self):

    # Omit double definition of def set_title(self):

    def get_containees(self) -> Iterable[TOdmaContainable]:
        try:
            return core.get_property(constants.PROPERTY_CONTAINEES).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Containees")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Containees")

    def get_associations(self) -> Iterable[TOdmaAssociation]:
        try:
            return core.get_property(constants.PROPERTY_ASSOCIATIONS).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Associations")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Associations")

    dict_odma_container = {
        "get_title": get_title,
        "set_title": set_title,
        "get_containees": get_containees,
        "get_associations": get_associations,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_parent(self) -> Optional["OdmaFolder"]:
        try:
            return core.get_property(constants.PROPERTY_PARENT).get_reference()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Parent")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Parent")

    def set_parent(self, new_value: Optional["OdmaFolder"]) -> None:
        try:
            core.get_property(constants.PROPERTY_PARENT).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Parent")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Parent")

    def get_sub_folders(self) -> Iterable[TOdmaFolder]:
        try:
            return core.get_property(constants.PROPERTY_SUBFOLDERS).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:SubFolders")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:SubFolders")

    dict_odma_folder = {
        "get_parent": get_parent,
        "set_parent": set_parent,
        "get_sub_folders": get_sub_folders,
        "get_title": get_title,
        "set_title": set_title,
        "get_containees": get_containees,
        "get_associations": get_associations,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    def get_contained_in(self) -> Iterable[TOdmaContainer]:
        try:
            return core.get_property(constants.PROPERTY_CONTAINEDIN).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ContainedIn")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ContainedIn")

    def get_contained_in_associations(self) -> Iterable[TOdmaAssociation]:
        try:
            return core.get_property(constants.PROPERTY_CONTAINEDINASSOCIATIONS).get_reference_iterable()
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:ContainedInAssociations")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:ContainedInAssociations")

    dict_odma_containable = {
        "get_contained_in": get_contained_in,
        "get_contained_in_associations": get_contained_in_associations,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    # Omit double definition of def get_name(self):

    # Omit double definition of def set_name(self):

    def get_container(self) -> "OdmaContainer":
        try:
            result = core.get_property(constants.PROPERTY_CONTAINER).get_reference()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Container is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Container")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Container")

    def set_container(self, new_value: "OdmaContainer") -> None:
        try:
            core.get_property(constants.PROPERTY_CONTAINER).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Container")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Container")

    def get_containable(self) -> "OdmaContainable":
        try:
            result = core.get_property(constants.PROPERTY_CONTAINABLE).get_reference()
            if result is None:
                raise OdmaServiceException("Predefined OpenDMA property opendma:Containable is None")
            return result
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Containable")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Containable")

    def set_containable(self, new_value: "OdmaContainable") -> None:
        try:
            core.get_property(constants.PROPERTY_CONTAINABLE).set_value(new_value)
        except OdmaPropertyNotFoundException:
            raise OdmaServiceException("Predefined OpenDMA property missing: opendma:Containable")
        except OdmaInvalidDataTypeException:
            raise OdmaServiceException("Predefined OpenDMA property has wrong type or cardinality: opendma:Containable")

    dict_odma_association = {
        "get_name": get_name,
        "set_name": set_name,
        "get_container": get_container,
        "set_container": set_container,
        "get_containable": get_containable,
        "set_containable": set_containable,
        "get_odma_class": get_odma_class,
        "get_aspects": get_aspects,
        "get_id": get_id,
        "get_guid": get_guid,
        "get_repository": get_repository,
    }

    classes: list[Type] = []

    for intf in odma_interfaces:
        if intf == constants.CLASS_OBJECT:
            classes.append(OdmaObject)
            dict.update(dict_odma_object)
        elif intf == constants.CLASS_CLASS:
            classes.append(OdmaClass)
            dict.update(dict_odma_class)
        elif intf == constants.CLASS_PROPERTYINFO:
            classes.append(OdmaPropertyInfo)
            dict.update(dict_odma_property_info)
        elif intf == constants.CLASS_CHOICEVALUE:
            classes.append(OdmaChoiceValue)
            dict.update(dict_odma_choice_value)
        elif intf == constants.CLASS_REPOSITORY:
            classes.append(OdmaRepository)
            dict.update(dict_odma_repository)
        elif intf == constants.CLASS_AUDITSTAMPED:
            classes.append(OdmaAuditStamped)
            dict.update(dict_odma_audit_stamped)
        elif intf == constants.CLASS_DOCUMENT:
            classes.append(OdmaDocument)
            dict.update(dict_odma_document)
        elif intf == constants.CLASS_CONTENTELEMENT:
            classes.append(OdmaContentElement)
            dict.update(dict_odma_content_element)
        elif intf == constants.CLASS_DATACONTENTELEMENT:
            classes.append(OdmaDataContentElement)
            dict.update(dict_odma_data_content_element)
        elif intf == constants.CLASS_REFERENCECONTENTELEMENT:
            classes.append(OdmaReferenceContentElement)
            dict.update(dict_odma_reference_content_element)
        elif intf == constants.CLASS_VERSIONCOLLECTION:
            classes.append(OdmaVersionCollection)
            dict.update(dict_odma_version_collection)
        elif intf == constants.CLASS_CONTAINER:
            classes.append(OdmaContainer)
            dict.update(dict_odma_container)
        elif intf == constants.CLASS_FOLDER:
            classes.append(OdmaFolder)
            dict.update(dict_odma_folder)
        elif intf == constants.CLASS_CONTAINABLE:
            classes.append(OdmaContainable)
            dict.update(dict_odma_containable)
        elif intf == constants.CLASS_ASSOCIATION:
            classes.append(OdmaAssociation)
            dict.update(dict_odma_association)

    dynamic_class = type(
        "DynamicClass",
        tuple(prune_inheritance_chain(classes)),
        dict)
    return dynamic_class()  # type: ignore[return-value]