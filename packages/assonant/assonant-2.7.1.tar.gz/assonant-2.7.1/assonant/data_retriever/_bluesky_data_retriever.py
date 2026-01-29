from typing import Any, Dict, List, Union

from assonant._bluesky import DataParserFactory
from assonant.naming_standards import AcquisitionMoment

from .assonant_data_retriever_interface import IAssonantDataRetriever
from .exceptions import AssonantDataRetrieverError


class BlueskyDataRetriever(IAssonantDataRetriever):
    """Bluesky Data Retriever."""

    def __init__(self, bluesky_data_source: Union[List[List[Union[str, Dict[str, Any]]]], str]):
        """Instantiates BlueskyDataRetriever to retrieve data from given data source.

        Args:
            bluesky_data_source (Union[List[List[Union[str, Dict[str, Any]]]], str]): DataSource containing
            the bluesky data. Currently, supported formats are: JSON file containing bluesky events or a
            List of bluesky documents data presented also as  a list. The list with the document data has
            2 positions, the 1st is the bluesky identification for the document
            (start, event, stop, descriptor, ...) and the 2nd position the dict containing the document
            data.

        Raises:
            AssonantDataRetrieverError: Failed to create the suitable Bluesky Data Parser for given data source.
        """
        try:
            self.bluesky_data_parser = DataParserFactory.create_data_parser(bluesky_data_source=bluesky_data_source)
        except Exception as e:
            raise AssonantDataRetrieverError(
                "BlueskyDataRetriever failed to create Bluesky DataParser for given data source."
            ) from e

    def _convert_acquisition_moment_into_event_stream_name(self, acquisition_moment: AcquisitionMoment) -> List[str]:
        """Convert AcquisitionMoment value to its equivalent EventStreamName objects.

        PS: On Bluesky, the existing DataStreams can be mapped to a respective AcquisitionMoment. Current mapping is:
            * During -> 'primary', monitor and flyscan streams
            * Start/End -> 'baseline'

            Due to the ambiguity created by primary, monitor and flyscan streams, this method return value is a List of
            EventStreamName objects.

        Args:
            acquisition_moment (AcquisitionMoment): AcquisitionMoment Enum object to be converted

        Raises:
            AssonantDataRetrieverError: Raised if there is no valid convertion for the passed AcquisitionMoment object.

        Returns:
            List[str]: List of stream names related to the passed Acquisition Moment Enum object.
        """
        if acquisition_moment == AcquisitionMoment.START or acquisition_moment == AcquisitionMoment.END:
            return ["baseline"]
        elif acquisition_moment == AcquisitionMoment.DURING:
            stream_names = self.bluesky_data_parser.get_stream_names()
            if "baseline" in stream_names:
                stream_names.remove("baseline")
            return stream_names  # Except baseline stream, all other streams fits During AcquisitionMoment.
        else:
            raise AssonantDataRetrieverError(
                f"There is no valid EventStream convertion value for '{acquisition_moment.value}' AcquisitionMoment"
            )

    def get_pv_data_by_acquisition_moment(
        self, acquisition_moment: AcquisitionMoment
    ) -> Dict[str, Union[Any, List[Any]]]:
        """Return collected PV data related to specified AcquisitionMoment.

        The returned value is a dictionary as follow:

        {
            PV_NAME_1: [PV_VALUE_1, PV_VALUE_2, ...],
            PV_NAME_2: PV_VALUE_1,
            ...
        }

        PS: PV values may be a List/array of value or a single value

        Args:
            acquisition_moment (AcquisitionMoment): Target Acquisition Moment used to select
            data from which Acquisition Moment will be retrieved.

        Returns:
            Dict[str, Union[Any, List[Any]]]: Dictionary containing retrieved PV data.
        """
        event_stream_names = self._convert_acquisition_moment_into_event_stream_name(acquisition_moment)
        all_retrieved_data = {}

        # Retrieve data from all streams related to passed acquisition moment
        for event_stream_name in event_stream_names:
            retrieved_stream_data = self.bluesky_data_parser.query_data_by_stream_name(
                event_stream_name, with_config=True
            )
            all_retrieved_data = all_retrieved_data | retrieved_stream_data

        # Convert data representation to fit the expected return structure
        formatted_retrieved_data = {}

        for pv_name, pv_data_list in all_retrieved_data.items():
            # Each position of pv_data_list is a tuple -> 1st position is the acquired value and 2nd the timestamp
            formatted_retrieved_data[pv_name] = [pv_data[0] for pv_data in pv_data_list]

        if acquisition_moment == AcquisitionMoment.START:
            for pv_name in formatted_retrieved_data:
                # Experiment Start snapshot is returned in the first position of the list for
                formatted_retrieved_data[pv_name] = formatted_retrieved_data[pv_name][0]
        elif acquisition_moment == AcquisitionMoment.END:
            for pv_name in formatted_retrieved_data:
                # Experiment End snapshot is returned in the last position of the list
                formatted_retrieved_data[pv_name] = formatted_retrieved_data[pv_name][-1]

        return formatted_retrieved_data
