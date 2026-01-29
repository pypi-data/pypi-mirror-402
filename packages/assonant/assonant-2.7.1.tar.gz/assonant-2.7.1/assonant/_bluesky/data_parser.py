import json
from typing import Any, Dict, List, Tuple, Union

from event_model import DocumentRouter

from .exceptions import BlueskyDataParserError


class DocumentsDataParser(DocumentRouter):
    def __init__(self, bluesky_documents_list: List[List[Union[str, Dict[str, Any]]]], *args, **kwargs):
        """Constructor to instantiate a Bluesky Documents DataParser.

        Args:
            bluesky_documents_list (List[List[Union[str, Dict[str, Any]]]]): List of bluesky documents data
            presented also as a list. The list with the document data has 2 positions, the 1st is the bluesky
            identification for the document (start, event, stop, descriptor, ...) and the 2nd position the
            dict containing the document data.
        Raises:
            BlueskyDataParserError: Failure to read bluesky documents.
        """
        super().__init__(*args, **kwargs)

        self._start_document = None
        self._descriptor_documents = {}

        # Stream name --> Subdevice configurations
        self._configurations = {}
        # Stream name --> Device data keys
        self._data_keys = {}
        # Stream name --> Device data key --> (Device data reading, Reading timestamp)
        self._event_data = {}

        try:
            # print("Init DocumentsDataParser")
            # Iterate over json data correctly parse data based on event type
            for event_name, document_data_dict in bluesky_documents_list:
                # print(event_name, document_data_dict)
                self(event_name, document_data_dict)
        except Exception as e:
            raise BlueskyDataParserError(
                f"Failed to read bluesky documents from structure: {bluesky_documents_list}"
            ) from e

    def start(self, doc: Dict):
        """DocumentRouter method related to processing bluesky START documments

        Args:
            doc (Dict): Dictionary containing bluesky documment data.
        """
        # print("========== START ==========")
        # print(doc)
        # print("===========================\n")
        self._start_document = doc

    def descriptor(self, doc: Dict):
        """DocumentRouter method related to processing bluesky DESCRIPTOR documments

        Args:
            doc (Dict): Dictionary containing bluesky documment data.
        """
        # print("========== DESC ==========")
        # print(doc)
        # print("===========================\n")
        self._descriptor_documents[doc["uid"]] = doc

        self._configurations[doc["name"]] = doc["configuration"]
        self._data_keys[doc["name"]] = doc["data_keys"]
        # print("DESC DOCS")
        # print(self._descriptor_documents)

    def event(self, doc: Dict):
        """DocumentRouter method related to processing bluesky EVENT documments

        Args:
            doc (Dict): Dictionary containing bluesky documment data.
        """
        # print("========== EVENT ==========")
        # print(doc)
        # print("===========================\n")
        stream_name = self._descriptor_documents[doc["descriptor"]]["name"]

        if stream_name not in self._event_data:
            self._event_data[stream_name] = {}

        for dev_name, val in doc["data"].items():
            if dev_name not in self._event_data[stream_name]:
                self._event_data[stream_name][dev_name] = []

            self._event_data[stream_name][dev_name].append((val, doc["timestamps"][dev_name]))

    def get_stream_names(self) -> List[str]:
        """Return a List of streams names within parsed documents.

        Returns:
            List[str]: List of stream names found on parsed documents.
        """
        return [stream_name for stream_name in self._data_keys]

    def all_data_keys(self) -> Dict[str, List]:
        """Return all dictionary keys to access data fields from each stream into the data dictionary.

        Returns:
            Dict[str, List]: Dictionary containing the stream name and a List with its respetive data_keys
        """
        data_keys = {}
        for stream, devices in self._data_keys.items():
            for device_data_key, device_values in devices.items():
                if stream not in data_keys:
                    data_keys[stream] = []
                data_keys[stream].append(device_data_key)
        return data_keys

    def data_key_to_pv_name(self, data_key: str) -> str:
        """Convert data_key to the respective PV name related to it.

        Args:
            data_key (str): data key from data dictionary that will be converted

        Returns:
            str: PV Name respective to passed data_key
        """
        pv_names = {}
        for stream, devices in self._data_keys.items():
            for device_data_key, device_values in devices.items():
                if device_data_key == data_key:
                    pv_names[stream] = ":".join(device_values["source"].split(":")[1:])
                    break
        return pv_names

    def config_data_key_to_pv_name(self, data_key: str) -> str:
        """Convert a configuration data_key to the respective PV name related to it.

        Args:
            data_key (str): data key from configuration dictionary from descriptor event
            that will be converted

        Returns:
            str: PV Name respective to passed configuration data_key
        """
        pv_names = {}
        for stream, devices in self._configurations.items():
            for device_name in devices:
                for config_data_key, config_values in devices[device_name]["data_keys"].items():
                    if config_data_key == data_key:
                        pv_names[stream] = ":".join(config_values["source"].split(":")[1:])
                        break
        return pv_names

    def pv_name_to_data_key(self, pv_name: str) -> str:
        """Convert PV name to the respective data_key related to it.

        Args:
            pv_name (str): PV Name that will be converted

        Returns:
            str: Data key respective to passed PV Name
        """
        data_keys = {}
        formatted_pv_name = f"PV:{pv_name}"
        for stream, devices in self._data_keys.items():
            for device_data_key, device_values in devices.items():
                if formatted_pv_name in device_values["source"]:
                    data_keys[stream] = device_data_key
                    break

        return data_keys

    def pv_name_to_config_data_key(self, pv_name: str) -> str:
        """Convert PV name to the respective configuration data_key related to it.

        Args:
            pv_name (str): PV Name that will be converted

        Returns:
            str: Configuration Data key respective to passed PV Name
        """
        data_keys = {}
        formatted_pv_name = f"PV:{pv_name}"
        for stream, devices in self._configurations.items():
            for device_name in devices:
                for config_data_key, config_values in devices[device_name]["data_keys"].items():
                    if formatted_pv_name in config_values["source"]:
                        data_keys[stream] = config_data_key
                        break

        return data_keys

    def query_data_by_stream_name(
        self, event_stream_name: str, with_config: bool
    ) -> Dict[str, List[Tuple[Any, float]]]:
        """Return all information from bluesky docs from a specific event stream organized as PV name -> Value.

        The organization structure returned is the following:
        {
            PV_NAME_1: [(PV_VALUE_1, PV_VALUE_1_TIMESTAMP), (PV_VALUE_2, PV_VALUE_2_TIMESTAMP) ...],
            PV_NAME_2: [(PV_VALUE_1, PV_VALUE_1_TIMESTAMP)],
            ...
        }

        PS: PV values are ALWAYS inside a List, even if it is a single value. It is also ALWAYS
        returned in a Tuple where the first position is the acquired value and the second the
        acquisition timestamp.

        Args:
            event_stream_name (str): Query's target event stream name.
            with_config (bool): Flag to control if data will add configuration
            information or not.

        Returns:
            Dict[str, Dict[str, List]]: Dictionary with data following structure described above. If
            no data is found it returns an empty dict.
        """
        # Stream name --> PV prefix --> Collected data
        data = {}

        data_keys = self.all_data_keys()
        if len(data_keys) == 0 or event_stream_name not in data_keys.keys():
            return data

        data_keys = data_keys[event_stream_name]

        for data_key in data_keys:
            pv_name = self.data_key_to_pv_name(data_key)[event_stream_name]

            if with_config:
                if data_key in self._configurations[event_stream_name]:
                    for subsignal_name, subsignal_metadata in self._configurations[event_stream_name][data_key][
                        "data_keys"
                    ].items():
                        config_pv_name = self.config_data_key_to_pv_name(subsignal_name)[event_stream_name]
                        data[config_pv_name] = [
                            (
                                self._configurations[event_stream_name][data_key]["data"][subsignal_name],
                                self._configurations[event_stream_name][data_key]["timestamps"][subsignal_name],
                            )
                        ]

            device_data = self._event_data.get(event_stream_name, {})
            data[pv_name] = device_data.get(data_key, {})

        return data

    def query_all_data(self, with_config: bool) -> Dict[str, Dict[str, List[Tuple[Any, float]]]]:
        """Return all information from bluesky docs organized as Stream -> PV name -> Value.

        The organization structure returned is the following:
        {
            STREAM_NAME_1: <Structure from query_data_by_stream_name() method>,
            STREAM_NAME_2: <Structure from query_data_by_stream_name() method>,
            ...
        }

        PS: PV values are ALWAYS inside a List, even if it is a single value. It is also ALWAYS
        returned in a Tuple where the first position is the acquired value and the second the
        acquisition timestamp.

        Args:
            with_config (bool): Flag to control if data will add configuration
            information or not.

        Returns:
            Dict[str, Dict[str, List]]: Dictionary with data following structure described above. If
            no data is found it returns an empty dict.
        """
        # Stream name --> PV prefix --> Collected data
        data = {}

        data_keys = self.all_data_keys()
        if len(data_keys) == 0:
            return data

        for stream in data_keys.keys():
            # print(f"Stream '{stream}':")
            data[stream] = {}
            stream_data = self.query_data_by_stream_name(stream, with_config=with_config)
            data[stream] = stream_data
        return data

    def load_json(self, path: str) -> Dict[str, Any]:
        """Load data from passed json file

        Args:
            path (str): File path to json file containing data collect from bluesky.

        Returns:
            Dict[str, Any]: Dictionary containing retrieved data from json file.
        """
        contents = None
        with open(path, "r") as _f:
            contents = json.load(_f)

        return contents
