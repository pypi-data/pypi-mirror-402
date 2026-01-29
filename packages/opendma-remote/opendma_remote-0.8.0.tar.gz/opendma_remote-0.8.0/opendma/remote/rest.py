from typing import Any, Optional
from collections.abc import Iterable, Iterator
from io import BytesIO
from base64 import b64decode
from dateutil.parser import isoparse
from opendma.api import OdmaType, OdmaQName, OdmaGuid, OdmaId, OdmaContent, OdmaProperty, OdmaPropertyImpl
from opendma.api import OdmaCoreObject, OdmaObject, OdmaRepository, OdmaSession, OdmaSearchResult, OdmaClass
from opendma.api import OdmaServiceException, OdmaObjectNotFoundException, OdmaPropertyNotFoundException, OdmaAuthenticationException, OdmaQuerySyntaxException
from opendma.api import odma_create_proxy, PROPERTY_CLASS, PROPERTY_ASPECTS
from pydantic import BaseModel, Field, field_validator, ValidationError
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import quote


class ServerRootWireModel(BaseModel):
    model_config = { "arbitrary_types_allowed": True }

    opendmaVersion: str
    serviceVersion: str
    repositories: list[OdmaId] = Field(default_factory=list)
    supportedQueryLanguages: list[OdmaQName] = Field(default_factory=list)

    @field_validator("repositories", mode="before")
    @classmethod
    def parse_repositories(cls, v):
        return [OdmaId(item) for item in v]

    @field_validator("supportedQueryLanguages", mode="before")
    @classmethod
    def parse_supported_query_languages(cls, v):
        return [OdmaQName.from_string(item) for item in v]


class OdmaPropertyWireModel(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    name: OdmaQName
    type: OdmaType
    multiValue: bool
    readOnly: bool
    resolved: bool
    value: Optional[Any] = None

    @field_validator("name", mode="before")
    @classmethod
    def parse_name(cls, v):
        return OdmaQName.from_string(v)

    @field_validator("type", mode="before")
    @classmethod
    def parse_type(cls, v):
        return OdmaType.from_string(v)


class OdmaObjectWireModel(BaseModel):
    model_config = { "arbitrary_types_allowed": True }

    id: OdmaId
    rootOdmaClassName: Optional[OdmaQName] = None
    aspectRootOdmaNames: list[OdmaQName] = Field(default_factory=list)
    properties: list[OdmaPropertyWireModel] = Field(default_factory=list)
    complete: Optional[bool] = None

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v):
        return OdmaId(v)

    @field_validator("rootOdmaClassName", mode="before")
    @classmethod
    def parse_root_odma_class_name(cls, v):
        return OdmaQName.from_string(v)

    @field_validator("aspectRootOdmaNames", mode="before")
    @classmethod
    def parse_aspect_root_qnames(cls, v):
        return [OdmaQName.from_string(item) for item in v]


class ReferenceEnumerationWireModel(BaseModel):
    model_config = { "arbitrary_types_allowed": True }

    next: Optional[str]
    items: list[OdmaObjectWireModel] = Field(default_factory=list)


class OdmaSearchWireModel(BaseModel):
    model_config = { "arbitrary_types_allowed": True }

    items: list[OdmaObjectWireModel] = Field(default_factory=list)


class RemoteConnection:
    _endpoint: str
    _session: requests.Session
    _trace_requests: int = 0

    def __init__(self, session: requests.Session, endpoint: str, trace_requests: int = 0):
        self._endpoint = endpoint.rstrip("/")
        self._session = session
        self._trace_requests = trace_requests

    def get_service_wire_data(self) -> ServerRootWireModel:
        try:
            url = f"{self._endpoint}/"
            if self._trace_requests > 0:
                print(f">>>> {url}")
            response = self._session.get(url)
            if self._trace_requests > 1:
                print(f"<<<< Duration: {response.elapsed.total_seconds() * 1000:.0f}ms")

            if response.status_code == 401:
                raise OdmaAuthenticationException()

            response.raise_for_status()
            data = response.json()
            if self._trace_requests > 2:
                print(f"<<<< {data}")
            return ServerRootWireModel.model_validate(data)

        except requests.RequestException as e:
            raise OdmaServiceException(f"HTTP request failed: {e}") from e

        except (ValidationError, ValueError, TypeError, KeyError) as e:
            raise OdmaServiceException(f"Invalid JSON in response: {e}") from e

    def get_object_wire_data(self, repository_id: OdmaId, object_id: Optional[OdmaId] = None, include: Optional[str] = None) -> OdmaObjectWireModel:
        encoded_repoid = quote(str(repository_id), safe="")
        encoded_objid = quote(str(object_id), safe="") if object_id is not None else None
        encoded_include = quote(include, safe="") if include is not None else None

        if object_id is None:
            url = f"{self._endpoint}/obj/{encoded_repoid}"
        else:
            url = f"{self._endpoint}/obj/{encoded_repoid}/{encoded_objid}"

        if include is not None:
            url += f"?include={encoded_include}"

        try:
            if self._trace_requests > 0:
                print(f">>>> {url}")
            response = self._session.get(url)
            if self._trace_requests > 1:
                print(f"<<<< Duration: {response.elapsed.total_seconds() * 1000:.0f}ms")

            if response.status_code == 401:
                raise OdmaAuthenticationException()
            if response.status_code == 404:
                raise OdmaObjectNotFoundException(repositoryId=repository_id, objectId=object_id)

            response.raise_for_status()
            data = response.json()
            if self._trace_requests > 2:
                print(f"<<<< {data}")
            return OdmaObjectWireModel.model_validate(data)

        except requests.RequestException as e:
            raise OdmaServiceException(f"HTTP request failed: {e}") from e

        except (ValidationError, ValueError, TypeError, KeyError) as e:
            raise OdmaServiceException(f"Failed to deserialize OdmaObject: {e}") from e

    def post_search_wire_data(self, repository_id: OdmaId, language: OdmaQName, query: str) -> OdmaSearchWireModel:
        encoded_repoid = quote(str(repository_id), safe="")
        url = f"{self._endpoint}/search/{encoded_repoid}"
        payload = {"language": str(language), "query": query}

        try:
            if self._trace_requests > 0:
                print(f">>>> {url}")
                print(f">>>> Payload: {payload}")
            response = self._session.post(url, json=payload)
            if self._trace_requests > 1:
                print(f"<<<< Duration: {response.elapsed.total_seconds() * 1000:.0f}ms")

            if response.status_code == 400:
                raise OdmaQuerySyntaxException(response.text)
            if response.status_code == 401:
                raise OdmaAuthenticationException()
            if response.status_code == 404:
                raise OdmaObjectNotFoundException(repositoryId=repository_id)

            response.raise_for_status()
            data = response.json()
            if self._trace_requests > 2:
                print(f"<<<< {data}")
            return OdmaSearchWireModel.model_validate(data)

        except requests.RequestException as e:
            raise OdmaServiceException(f"HTTP request failed: {e}") from e

        except (ValidationError, ValueError, TypeError, KeyError) as e:
            raise OdmaServiceException(f"Invalid JSON in response: {e}") from e

    def access_stream(self, repository_id: str, content_id: str) -> BytesIO:
        encoded_repoid = quote(str(repository_id), safe="")
        encoded_contentid = quote(str(content_id), safe="")
        url = f"{self._endpoint}/bin/{encoded_repoid}/{encoded_contentid}"
        try:
            if self._trace_requests > 0:
                print(f">>>> {url}")
            response = self._session.get(url)
            response.raise_for_status()
            return BytesIO(response.content)
        except requests.RequestException as e:
            raise OdmaServiceException(f"HTTP request failed: {e}") from e

    def close(self) -> None:
        self._session.close()


class ObjectData:
    id: OdmaId
    rootOdmaClassName: Optional[OdmaQName]
    aspectRootOdmaNames: list[OdmaQName]
    properties: dict[OdmaQName, OdmaProperty]
    complete: bool


class OdmaRemoteContent(OdmaContent):
    """
    OdmaContent implementation for rest-ful OpenDMA remote services.
    """
    def __init__(self, repository_id: str, content_id: str, size: int, connection: RemoteConnection):
        self._repository_id = repository_id
        self._content_id = content_id
        self._size = size
        self._connection = connection

    def get_stream(self) -> BytesIO:
        return self._connection.access_stream(self._repository_id, self._content_id)

    def get_size(self) -> int:
        return self._size


class OdmaRemoteSearchResult(OdmaSearchResult):
    _items: list[OdmaObject]

    def __init__(self, items: list[OdmaObject]):
        self._items = items

    def get_objects(self) -> Iterable[OdmaObject]:
        return iter(self._items)

    def get_size(self) -> int:
        return self._items.__len__()

class PagingReferenceIterable(Iterable[OdmaObject]):
    _page: list[OdmaObjectWireModel]
    _next: Optional[str]
    _connection: RemoteConnection
    _repository_id: OdmaId
    _object_id: OdmaId
    _prop_name: OdmaQName
    def __init__(self, page: list[OdmaObjectWireModel], next: Optional[str], connection: RemoteConnection, repository_id: OdmaId, object_id: OdmaId, prop_name: OdmaQName):
        self._page = page
        self._next = next
        self._connection = connection
        self._repository_id = repository_id
        self._object_id = object_id
        self._prop_name = prop_name

    def _fetch_next_page(self):
        include = escape_include(self._prop_name, self._next)
        wire = self._connection.get_object_wire_data(repository_id=self._repository_id, object_id=self._object_id, include=include)
        prop = None
        for wire_prop in wire.properties:
            if wire_prop.name == self._prop_name:
                prop = wire_prop
                break
        if not prop:
            raise OdmaServiceException(f"Failed fetching next page of property {self._prop_name}")
        wire = ReferenceEnumerationWireModel.model_validate(prop.value)
        self._page = wire.items
        self._next = wire.next

    def __iter__(self) -> Iterator[OdmaObject]:
        while True:
            for wire in self._page:
                object_data = object_data_from_wire(wire=wire, connection=self._connection, repository_id=self._repository_id)
                if object_data.rootOdmaClassName is None:
                    wire = self._connection.get_object_wire_data(repository_id=self._repository_id, object_id=object_data.id, include=None)
                    referenced_object_data = object_data_from_wire(wire=wire, connection=self._connection, repository_id=self._repository_id)
                    object = odma_object_from_object_data(referenced_object_data, self._connection, self._repository_id)
                    if not isinstance(object, OdmaObject):
                        raise OdmaServiceException(f"Failed resolving objects on page of property {self._prop_name}")
                    yield object
                else:
                    yield odma_object_from_object_data(object_data, self._connection, self._repository_id)
            if not self._next:
                break
            self._fetch_next_page()
            if not self._page:
                break


class LazyRemotePropertyValueProvider:
    def __init__(self, name: OdmaQName, connection: RemoteConnection, repository_id: OdmaId, object_id: OdmaId):
        self._name = name
        self._connection = connection
        self._repository_id = repository_id
        self._object_id = object_id

    def has_reference_id(self) -> bool:
        return False

    def get_reference_id(self) -> Optional[OdmaId]:
        return None

    def resolve_property_value(self) -> Any:
        include = escape_include(self._name)
        wire = self._connection.get_object_wire_data(repository_id=self._repository_id, object_id=self._object_id, include=include)
        object_data = object_data_from_wire(wire=wire, connection=self._connection, repository_id=self._repository_id)
        prop = object_data.properties[self._name]
        # ----------------------------------------------------------------------------------------------------------- TODO
        if prop == None: # or not prop.is_resolved():
            raise OdmaServiceException(f"Failed resolving property {self._name} lazily")
        return prop.get_value()


class LazyRemotePropertyObjectValueProvider:
    def __init__(self, connection: RemoteConnection, repository_id: OdmaId, object_id: OdmaId):
        self._connection = connection
        self._repository_id = repository_id
        self._object_id = object_id

    def has_reference_id(self) -> bool:
        return True

    def get_reference_id(self) -> Optional[OdmaId]:
        return self._object_id
    
    def resolve_property_value(self) -> Any:
        wire = self._connection.get_object_wire_data(repository_id=self._repository_id, object_id=self._object_id)
        object_data = object_data_from_wire(wire=wire, connection=self._connection, repository_id=self._repository_id)
        object = odma_object_from_object_data(object_data, self._connection, self._repository_id)
        if isinstance(object, OdmaObject):
            return object
        raise OdmaServiceException("Endpoint did not return valid OdmaObject object")


def _parse_odma_value(wire_prop: OdmaPropertyWireModel, connection: RemoteConnection, repository_id: OdmaId, object_id: OdmaId) -> Any:
    def parse_single(val: Any):
        if val is None:
            return None
        match wire_prop.type:
            case OdmaType.STRING:
                if not isinstance(val, str):
                    raise OdmaServiceException(f"Invalid JSON data type for {wire_prop.type}. Expected string.")
                return val
            case OdmaType.INTEGER | OdmaType.SHORT | OdmaType.LONG:
                if not isinstance(val, str):
                    raise OdmaServiceException(f"Invalid JSON data type for {wire_prop.type}. Expected string.")
                try:
                    return int(val)
                except Exception as e:
                    raise OdmaServiceException(f"Invalid integer value: {val!r}") from e
            case OdmaType.FLOAT | OdmaType.DOUBLE:
                if not isinstance(val, str):
                    raise OdmaServiceException(f"Invalid JSON data type for {wire_prop.type}. Expected string.")
                try:
                    return float(val)
                except Exception as e:
                    raise OdmaServiceException(f"Invalid float value: {val!r}") from e
            case OdmaType.BOOLEAN:
                if isinstance(val, str):
                    val_lower = val.lower()
                    if val_lower == "true":
                        return True
                    elif val_lower == "false":
                        return False
                raise OdmaServiceException(f"Invalid boolean string: '{val!r}'")
            case OdmaType.DATETIME:
                if not isinstance(val, str):
                    raise OdmaServiceException(f"Invalid JSON data type for {wire_prop.type}. Expected string.")
                try:
                    return isoparse(val)
                except Exception as e:
                    raise OdmaServiceException(f"Invalid datetime format: '{val!r}'") from e
            case OdmaType.BINARY:
                if not isinstance(val, str):
                    raise OdmaServiceException(f"Invalid JSON data type for {wire_prop.type}. Expected string.")
                try:
                    return b64decode(val)
                except Exception as e:
                    raise OdmaServiceException(f"Invalid base64 binary") from e
            case OdmaType.REFERENCE:
                if isinstance(val, dict):
                    object_data = object_data_from_json(data=val, connection=connection, repository_id=repository_id)
                    if object_data.rootOdmaClassName is None:
                        return OdmaId(val["id"])
                    else:
                        return odma_object_from_object_data(object_data, connection, repository_id)
                else:
                    raise OdmaServiceException(f"Invalid JSON data type for {wire_prop.type}. Expected object.")
            case OdmaType.CONTENT:
                try:
                    return OdmaRemoteContent(repository_id=str(repository_id), content_id=val["id"], size=int(val["size"]), connection=connection)
                except Exception as e:
                    raise OdmaServiceException(f"Invalid content object.") from e
            case OdmaType.ID:
                if not isinstance(val, str):
                    raise OdmaServiceException(f"Invalid JSON data type for {wire_prop.type}. Expected string.")
                try:
                    return OdmaId(val)
                except Exception as e:
                    raise OdmaServiceException(f"Invalid ID format: '{val!r}'") from e
            case OdmaType.GUID:
                try:
                    return OdmaGuid(
                        object_id=OdmaId(val["objectId"]),
                        repository_id=OdmaId(val["repositoryId"])
                    )
                except Exception as e:
                    raise OdmaServiceException(f"Invalid GUID object.") from e
            case _:
                raise OdmaServiceException(f"Unsupported OdmaType: {wire_prop.type}")
    if wire_prop.multiValue:
        if wire_prop.type == OdmaType.REFERENCE:
            if not isinstance(wire_prop.value, dict):
                raise OdmaServiceException(f"Expected object for multi-value reference, got: {type(wire_prop.value).__name__}")
            wire = ReferenceEnumerationWireModel.model_validate(wire_prop.value)
            return PagingReferenceIterable(page=wire.items, next=wire.next, connection=connection, repository_id=repository_id, object_id=object_id, prop_name=wire_prop.name)
        if not isinstance(wire_prop.value, list):
            raise OdmaServiceException(f"Expected list for multi-valued scalar, got: {type(wire_prop.value).__name__}")
        return [parse_single(v) for v in wire_prop.value]
    else:
        return parse_single(wire_prop.value)


def object_data_from_json(data: dict, connection: RemoteConnection, repository_id: OdmaId) -> ObjectData:
    try:
        wire = OdmaObjectWireModel.model_validate(data)
        return object_data_from_wire(wire=wire, connection=connection, repository_id=repository_id)
    except (ValidationError, ValueError, TypeError, KeyError) as e:
        raise OdmaServiceException(f"Failed to deserialize OdmaObject: {e}") from e


def object_data_from_wire(wire: OdmaObjectWireModel, connection: RemoteConnection, repository_id: OdmaId) -> ObjectData:
    try:
        properties: list[OdmaProperty] = []
        for wire_prop in wire.properties:
            if wire_prop.resolved:
                value = _parse_odma_value(wire_prop, connection, repository_id, wire.id)
                if wire_prop.type == OdmaType.REFERENCE and isinstance(value, OdmaId):
                    provider = LazyRemotePropertyObjectValueProvider(connection, repository_id, value)
                    prop = OdmaPropertyImpl(
                        name=wire_prop.name,
                        value=None,
                        value_provider=provider,
                        data_type=wire_prop.type,
                        multi_value=wire_prop.multiValue,
                        read_only=wire_prop.readOnly
                    )
                    properties.append(prop)
                else:
                    prop = OdmaPropertyImpl(
                        name=wire_prop.name,
                        value=value,
                        value_provider=None,
                        data_type=wire_prop.type,
                        multi_value=wire_prop.multiValue,
                        read_only=wire_prop.readOnly
                    )
                    properties.append(prop)
            else:
                provider = LazyRemotePropertyValueProvider(wire_prop.name, connection, repository_id, wire.id)
                prop = OdmaPropertyImpl(
                    name=wire_prop.name,
                    value=None,
                    value_provider=provider,
                    data_type=wire_prop.type,
                    multi_value=wire_prop.multiValue,
                    read_only=wire_prop.readOnly
                )
                properties.append(prop)
        result = ObjectData()
        result.id = wire.id
        result.rootOdmaClassName = wire.rootOdmaClassName
        result.aspectRootOdmaNames = wire.aspectRootOdmaNames
        result.properties = {prop.get_name(): prop for prop in properties}
        result.complete = wire.complete if wire.complete is not None else False
        return result
    except (ValidationError, ValueError, TypeError, KeyError) as e:
        raise OdmaServiceException(f"Failed to deserialize OdmaObject: {e}") from e


def escape_include(prop_name: OdmaQName, next: Optional[str] = None) -> str:
    prop_escaped = str(prop_name).replace("\\", "\\\\").replace("@", "\\@").replace(";", "\\;")
    if next is None:
        return prop_escaped
    next_escaped = next.replace("\\", "\\\\").replace("@", "\\@").replace(";", "\\;")
    return f"{next_escaped}@{prop_escaped}"


def odma_object_from_object_data(object_data: ObjectData, connection: RemoteConnection, repository_id: OdmaId) -> OdmaObject:
    if object_data.rootOdmaClassName is None:
        raise OdmaServiceException(f"Incomplete ID-only object where full object has been expected")
    odma_class_qnames = [object_data.rootOdmaClassName] + object_data.aspectRootOdmaNames
    core = OdmaRemoteCoreObject(properties=object_data.properties,
                                complete=object_data.complete,
                                connection=connection,
                                repository_id=repository_id,
                                object_id=object_data.id)
    return odma_create_proxy(odma_class_qnames, core)


class OdmaRemoteCoreObject(OdmaCoreObject):
    properties: dict[OdmaQName, OdmaProperty]
    complete: bool
    connection: RemoteConnection
    repository_id: OdmaId
    object_id: OdmaId
    odmaSession: OdmaSession

    def __init__(self, properties: dict[OdmaQName, OdmaProperty], complete: bool, connection: RemoteConnection, repository_id: OdmaId, object_id: OdmaId) -> None:
        if not isinstance(properties, dict):
            raise OdmaServiceException("Incorrect type of properties. expected dict")
        self.properties = properties
        self.complete = complete
        self.connection = connection
        self.repository_id = repository_id
        self.object_id = object_id

    def get_property(self, property_name: OdmaQName) -> OdmaProperty:
        try:
            return self.properties[property_name]
        except KeyError:
            if self.complete:
                raise OdmaPropertyNotFoundException(propertyName=property_name)
            else:
                self.prepare_properties([property_name], False)
                try:
                    return self.properties[property_name]
                except KeyError:
                    raise OdmaPropertyNotFoundException(propertyName=property_name)

    def prepare_properties(self, property_names: Optional[list[OdmaQName]], refresh: bool) -> None:
        include = None
        if property_names is None:
            include = "*:*"
        else:
            include_parts = []
            for prop_name in property_names:
                include_parts.append(escape_include(prop_name))
            include = ";".join(include_parts)
            if not include:
                return
        wire = self.connection.get_object_wire_data(repository_id=self.repository_id, object_id=self.object_id, include=include)
        object_data = object_data_from_wire(wire=wire, connection=self.connection, repository_id=self.repository_id)
        for prop_name, prop_value in object_data.properties.items():
            if refresh or prop_name not in self.properties:
                self.properties[prop_name] = prop_value

    def set_property(self, property_name: OdmaQName, new_value: Any) -> None:
        prop = self.get_property(property_name)
        prop.set_value(new_value)

    def is_dirty(self) -> bool:
        return any(p.is_dirty() for p in self.properties.values())

    def save(self) -> None:
        # No-op for now: everything is already local
        pass

    def instance_of(self, class_or_aspect_name: OdmaQName) -> bool:
        test = self._internal_get_odma_class()
        while test is not None:
            if test.get_qname() == class_or_aspect_name:
                return True
            aspects = test.get_included_aspects()
            if aspects is not None:
                for aspect in aspects:
                    if aspect.get_qname() == class_or_aspect_name:
                        return True
            test = test.get_super_class()
        for aspect in self._internal_get_odma_aspects():
            while aspect is not None:
                if aspect.get_qname() == class_or_aspect_name:
                    return True
                aspect = aspect.get_super_class()
        return False
    
    def _internal_get_odma_class(self) -> OdmaClass:
        clazz = self.get_property(PROPERTY_CLASS).get_reference()
        if isinstance(clazz, OdmaClass):
            return clazz
        raise OdmaServiceException("Invalid class of object")
    
    def _internal_get_odma_aspects(self) -> Iterable[OdmaClass]:
        return self.get_property(PROPERTY_ASPECTS).get_reference_iterable()


class OdmaRemoteSession(OdmaSession):
    def __init__(self, connection: RemoteConnection, odmaVersion: str, serviceVersion: str, repositories: list[OdmaId], supported_query_languages: list[OdmaQName]):
        self._connection = connection
        self._odmaVersion = odmaVersion
        self._serviceVersion = serviceVersion
        self._repositories = repositories
        self._supported_query_languages = supported_query_languages

    def get_repository_ids(self) -> list[OdmaId]:
        return self._repositories

    def get_repository(self, repository_id: OdmaId) -> OdmaRepository:
        wire = self._connection.get_object_wire_data(repository_id=repository_id)
        object_data = object_data_from_wire(wire=wire, connection=self._connection, repository_id=repository_id)
        object = odma_object_from_object_data(object_data, self._connection, repository_id)
        if isinstance(object, OdmaRepository):
            return object
        raise OdmaServiceException("Endpoint did not return valid OdmaRepository object")

    def get_object(self, repository_id: OdmaId, object_id: OdmaId, property_names: Optional[list[OdmaQName]]) -> OdmaObject:
        include = None
        if property_names is not None:
            include_parts = []
            for prop_name in property_names:
                include_parts.append(escape_include(prop_name))
            include_parts.append("default")
            include = ";".join(include_parts)
        wire = self._connection.get_object_wire_data(repository_id=repository_id, object_id=object_id, include=include)
        object_data = object_data_from_wire(wire=wire, connection=self._connection, repository_id=repository_id)
        object = odma_object_from_object_data(object_data, self._connection, repository_id)
        if isinstance(object, OdmaObject):
            return object
        raise OdmaServiceException("Endpoint did not return valid OdmaObject object")

    def search(self, repository_id: OdmaId, query_language: OdmaQName, query: str) -> OdmaSearchResult:
        wire = self._connection.post_search_wire_data(repository_id=repository_id, language=query_language, query=query)
        items: list[OdmaObject] = []
        for wire_item in wire.items:
            object_data = object_data_from_wire(wire=wire_item, connection=self._connection, repository_id=repository_id)
            object = odma_object_from_object_data(object_data, self._connection, repository_id)
            if isinstance(object, OdmaObject):
                items.append(object)
        return OdmaRemoteSearchResult(items=items)

    def get_supported_query_languages(self) -> list[OdmaQName]:
        return self._supported_query_languages

    def close(self) -> None:
        self._connection.close()



def connect(endpoint: str, username: Optional[str] = None, password: Optional[str] = None, requestTraceLevel: int = 0) -> OdmaRemoteSession:
    session = requests.Session()
    if username and password:
        session.auth = HTTPBasicAuth(username, password)
    conn = RemoteConnection(session, endpoint, requestTraceLevel)
    wire = conn.get_service_wire_data()
    return OdmaRemoteSession(connection=conn, odmaVersion=wire.opendmaVersion, serviceVersion=wire.serviceVersion, repositories=wire.repositories, supported_query_languages=wire.supportedQueryLanguages)
