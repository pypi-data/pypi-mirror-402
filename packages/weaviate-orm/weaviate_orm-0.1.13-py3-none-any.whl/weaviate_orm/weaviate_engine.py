import os
import warnings
from typing import Callable, Optional, Any, Union
import datetime as _dt

from weaviate.classes.config import Property, DataType, ReferenceProperty, Configure
from weaviate import WeaviateClient
import weaviate
import urllib.request
import json


from .weaviate_utility import validate_method_params
from .weaviate_decorators import syncify

class Weaviate_Engine:
    """
    Encapsulates Weaviate connection parameters and manages:
      - A shared (lazy) Weaviate client
      - Registration of model classes for schema creation
      - A 'create_all_schemas()' method to ensure all schemas are created once
    """

    MIN_SERVER_VERSION = (1, 27, 0)

    def _parse_version_tuple(self, ver: str) -> tuple[int, int, int]:
        # Normalize versions like '1.27.3' or '1.27.0-rc.1'
        core = ver.split("-")[0]
        parts = core.split(".")
        nums = []
        for i in range(3):
            try:
                nums.append(int(parts[i]))
            except (IndexError, ValueError):
                nums.append(0)
        return tuple(nums)  # type: ignore[return-value]

    def _get_server_version_http(self) -> Optional[str]:
        # Best-effort HTTP call to /v1/meta using known host/port
        host = None
        port = None
        scheme = os.getenv("WEAVIATE_SCHEME", "http")
        if hasattr(self, "_connection_params"):
            host = self._connection_params.get("host")
            port = self._connection_params.get("port")
        if not host or not port:
            return None
        url = f"{scheme}://{host}:{port}/v1/meta"
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Try common keys
                return data.get("version") or data.get("weaviate_version") or data.get("weaviateVersion")
        except Exception:
            return None

    def _ensure_min_server_version(self, client: WeaviateClient) -> None:
        # Try client internals first if available
        version_str: Optional[str] = None
        conn = getattr(client, "_connection", None)
        if conn is not None:
            # Try common internal attributes/methods across client versions
            for attr in ("server_version", "_server_version"):
                v = getattr(conn, attr, None)
                if isinstance(v, str):
                    version_str = v
                    break
            if version_str is None:
                get_fn = getattr(conn, "get", None)
                if callable(get_fn):
                    try:
                        res = get_fn("/v1/meta")
                        if isinstance(res, dict):
                            version_str = res.get("version") or res.get("weaviate_version") or res.get("weaviateVersion")
                    except Exception:
                        pass
        # Fallback to direct HTTP using known host/port
        if version_str is None:
            version_str = self._get_server_version_http()

        if version_str is None:
            # If we can't determine, proceed but warn (don’t block unknown environments)
            warnings.warn("Could not determine Weaviate server version; ensure it is >= 1.27.0.")
            return

        if self._parse_version_tuple(version_str) < self.MIN_SERVER_VERSION:
            raise RuntimeError(
                f"Weaviate server version {version_str} is not supported. "
                f"Please use Weaviate >= 1.27.0 to match the client requirements."
            )

    def __init__(self, connection_method=None, timezone_offset:Optional[Union[_dt.tzinfo, _dt.timedelta]]=None, **connection_params):
        """
        Initialize the Weaviate_Engine with connection parameters and timezone offset.

        Args:
            connection_method (Optional[Callable]): The method to use to connect to Weaviate.
            timezone_offset (Optional[_dt.tzinfo]): The timezone offset to use for writing naive datetimes.
            **connection_params: The parameters to pass to the connection method. Keys are parameter names.
        """

        self._set_connection_method(connection_method, **connection_params)

        self._client = None
        self._models = set()

        self._set_timezone_offset(timezone_offset)


    def _set_connection_method(self, connection_method: Optional[Callable] = None, **connection_params):
        """
        Set the connection method for the WeaviateEngine to connect to Weaviate.
        
        Args:
            connection_method (Optional[Callable]): The method to use to connect to Weaviate.
            **connection_params: The parameters to pass to the connection method. Keys are parameter names.
        
        Raises:
            TypeError: If the connection method does not return a weaviate.WeaviateClient.
        """

        #Default to connect_to_local() if no connection_method is provided
        if connection_method == None:
            connection_method = weaviate.connect_to_local

        if connection_params == {} and connection_method == weaviate.connect_to_local:

            #Try to get default connection parameters from environment variables
            host = os.getenv("WEAVIATE_HOST", "vdatabase")
            port = os.getenv("WEAVIATE_PORT", "8080")
            grpc_port = os.getenv("WEAVIATE_GRPC_PORT", "50051")

            connection_params = {
                "host": host,
                "port": port,
                "grpc_port": grpc_port
            }

        # Validate connection parameters and return type
        return_type = validate_method_params(connection_method, connection_params)
        if return_type is not weaviate.WeaviateClient and return_type is not None:
            raise TypeError(f"Expected method to return weaviate.Client, got {return_type}")
        elif return_type is None:
            warnings.warn("Connection method does not specify return type - make sure it returns a weaviate.WeaviateClient")
        else:
            self._connection_params : dict[str, Any] = connection_params
            self._connection_method : Callable = connection_method

    def _set_timezone_offset(self, timezone_offset=None):
        """
        Store tzinfo used for writing naive datetimes.
        Accepts:
          - None  -> use local system offset now
          - datetime.tzinfo
          - datetime.timedelta
        """
        if timezone_offset is None:
            offset = _dt.datetime.now().astimezone().utcoffset() or _dt.timedelta(0)
            tz = _dt.timezone(offset)
        elif isinstance(timezone_offset, _dt.tzinfo):
            tz = timezone_offset
        else:
            # assume timedelta-like
            tz = _dt.timezone(timezone_offset)
        self._timezone = tz

    @property
    def client(self):
        """
        Lazy-load the Weaviate client if None or not ready.
        """

        #Check connection
        if self._client is None or not self._client.is_connected():
            self._client = self._connection_method(**self._connection_params)

        #Check if the client is ready
        if not self._client.is_ready():
            self._client = self._connection_method(**self._connection_params)

        return self._client

    def _register_model(self, model_cls):
        """
        Called by model_cls.bind_engine(self).
        We store it so that when create_all_schemas() is called,
        we can create the schema for each registered model.
        """
        if hasattr(model_cls, "_weaviate_schema"):
            self._models.add(model_cls)
            #model_cls.bind_engine(self)
        else:
            raise ValueError("Model class does not have a _weaviate_schema attribute. Make sure the class inherits from Base_Model.")

    def register_all_models(self, *model_classes):
        """
        Register multiple model classes at once.
        """
        for model_cls in model_classes:
            model_cls.bind_engine(self)

    def create_all_schemas(self, delete_existing=False, update_existing=False): #TODO
        """
        Iterate over registered models and create the schema in Weaviate
        (only for those classes that are not yet defined in Weaviate).
        """
        
        with self.client as client:

            # Enforce minimum supported server version
            self._ensure_min_server_version(client)

            #Optionally delete all existing classes
            if delete_existing:
                client.collections.delete_all()

            #Get existing classes
            existing_collections = client.collections.list_all(simple=False)
            existing_classes = [k for k, c in existing_collections.items()]
            new_classes = []

            #Iterate over all models
            for model_cls in self._models:

                #Check if the model class is abstract
                if model_cls._abstract:
                    continue

                #Check if the class is already defined in Weaviate
                if model_cls.get_collection_name() in existing_classes:
                    if update_existing:
                        raise NotImplementedError("Updating existing classes is not yet implemented.") #TODO: Implement updating existing classes
                    else:
                        continue
                else:
                    new_classes.append(model_cls)

            # Create the classes in Weaviate #TODO!!!
            for model_cls in new_classes:

                references = model_cls._weaviate_schema["references"]
                base_shema = model_cls._weaviate_schema.copy()
                base_shema.pop("references")
                
                # Pass vector_config through; client accepts list of vector configs
                client.collections.create(**base_shema)

            # Add all cross-references
            for model_cls in new_classes:
                if model_cls._weaviate_schema["references"]:
                    collection = client.collections.get(model_cls.get_collection_name())

                    for reference in model_cls._weaviate_schema["references"]:
                        collection.config.add_reference(reference)

    def clear_engine(self, remove_collections=False):
        """
        Clear the engine and all registered models.
        """
        for model_cls in self._models:
            # Remove the collection from Weaviate if requested
            if remove_collections:
                self.client.collections.delete(model_cls.get_collection_name())
            
            # Remove the engine from the model class
            model_cls._engine = None

        self._models = set()