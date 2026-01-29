# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.

import logging
from collections.abc import Sequence

import lima2.client.services as l2s
import numpy as np
from blissdata.exceptions import (
    EmptyViewException,
    EndOfStream,
    IndexNoMoreThereError,
    IndexNotYetThereError,
    IndexWontBeThereError,
)
from blissdata.h5api import dynamic_hdf5
from blissdata.lima.image_utils import ImageData
from blissdata.streams import (
    BaseStream,
    BaseView,
    EventRange,
    StreamDefinition,
)
from blissdata.streams.default import Stream
from blissdata.streams.encoding.numeric import NumericStreamEncoder
from blissdata.streams.event_stream import EventStream
from blissdata.streams.lima.stream import LimaDirectAccess
from lima2.common.devencoded.sparse_frame import SparseFrame
from numpy.typing import DTypeLike

_logger = logging.getLogger(__name__)


def get_frame(
    services: l2s.ConductorServices,
    acq_uuid: str,
    source: str,
    frame_idx: int,
) -> ImageData:
    frm = services.pipeline.get_frame(frame_idx=frame_idx, source=source, uuid=acq_uuid)

    if isinstance(frm, SparseFrame):
        frm = frm.densify()

    return ImageData(array=frm.data, frame_id=frm.idx, acq_tag=None)


class Lima2View(BaseView):
    def __init__(
        self,
        services: l2s.ConductorServices,
        acq_uuid: str,
        source: str,
        start: int,
        stop: int,
    ) -> None:
        self._services = services
        """Lima2 client services."""
        self._acq_uuid = acq_uuid
        """Lima2 acquisition id."""
        self._source = source
        """Frame source name."""
        self._idx_range = range(start, stop)
        """Range of absolute frame indices accessible via this view."""

    @property
    def index(self) -> int:
        return self._idx_range.start

    def __len__(self) -> int:
        return len(self._idx_range)

    def get_data(self, start: int | None = None, stop: int | None = None) -> np.ndarray:
        frames = []
        for idx in self._idx_range[start:stop]:
            try:
                frames.append(
                    get_frame(
                        services=self._services,
                        acq_uuid=self._acq_uuid,
                        source=self._source,
                        frame_idx=idx,
                    ).array
                )
            except RuntimeError as e:
                # Raise if any frame can't be accessed
                raise IndexNoMoreThereError(
                    f"Can't fetch {self._source} {self._idx_range[start:stop]}: {e}"
                ) from e
            except ValueError as e:
                # Frame source has no associated memory buffer (raw_frame)
                raise IndexNoMoreThereError(
                    f"Can't fetch {self._source}: no associated live data"
                ) from e

        return np.asarray(frames)


class Lima2Stream(BaseStream, LimaDirectAccess):
    """Stream of Lima2 frames.

    Frames don't actually transit inside the stream. The stream length can be
    queried to determine the number of accessible frames.

    Indexing or slicing the stream attempts to fetch frames directly from the
    Lima2 backend.
    """

    PROTOCOL_VERSION = 2

    def __init__(self, event_stream: EventStream) -> None:
        BaseStream.__init__(self, event_stream)

        _logger.debug(f"Instantiate Lima2Stream with {event_stream.info=}")

        if event_stream.info["protocol_version"] != Lima2Stream.PROTOCOL_VERSION:
            raise RuntimeError(
                f"Lima2 protocol version mismatch "
                f"(expected {Lima2Stream.PROTOCOL_VERSION}, "
                f"got {event_stream.info['protocol_version']})"
            )

        self._dtype = np.dtype(event_stream.info["dtype"])
        self._shape = tuple(event_stream.info["shape"])
        self._acq_uuid = str(event_stream.info["acq_uuid"])
        self._source = str(event_stream.info["source_name"])
        self._master_file: tuple[str, str] | None = event_stream.info["master_file"]

        self._services = l2s.init(
            hostname=str(event_stream.info["conductor_hostname"]),
            port=int(event_stream.info["conductor_port"]),
        )
        """Lima2 client session."""

        self._length = 0
        """Current number of accessible frames."""

        self._cursor = Stream(event_stream).cursor()

    ####################################################################################
    # BaseStream
    ####################################################################################

    @property
    def kind(self) -> str:
        return "array"

    @staticmethod
    def make_definition(
        name: str,
        source_name: str,
        conductor_hostname: str,
        conductor_port: int,
        acq_uuid: str,
        master_file: tuple[str, str] | None,
        dtype: DTypeLike,
        shape: Sequence[int],
    ) -> StreamDefinition:
        info = {
            "plugin": "lima2",
            "dtype": np.dtype(dtype).name,
            "shape": shape,
            "protocol_version": Lima2Stream.PROTOCOL_VERSION,
            "acq_uuid": acq_uuid,
            "source_name": source_name,
            "conductor_hostname": conductor_hostname,
            "conductor_port": conductor_port,
            "master_file": master_file,
        }

        return StreamDefinition(name, info, NumericStreamEncoder(np.uint32))

    @property
    def plugin(self) -> str:
        return "lima2"

    @property
    def dtype(self) -> np.dtype:
        return self._dtype

    @property
    def shape(self) -> tuple[int, ...]:
        return self._shape

    def __len__(self) -> int:
        try:
            view = self._cursor.read(block=False, last_only=True)
        except EndOfStream:
            view = None

        if view is not None:
            last_status = view.get_data()[0]
            self._length = int(last_status)
        return self._length

    def __getitem__(self, key: int | slice) -> np.ndarray:
        sealed = self.is_sealed()
        if isinstance(key, int):
            size = len(self)
            if key < 0:
                if not sealed:
                    raise IndexNotYetThereError(
                        "Can't index from end of stream until it is sealed"
                    )
                else:
                    key += size

            if not 0 <= key < size:
                # Fail early if we're out of bounds
                if sealed:
                    raise IndexWontBeThereError(
                        f"Frame {key} is out of range (0..{size-1})"
                    )
                else:
                    raise IndexNotYetThereError(
                        f"Frame {key} is out of range (0..{size-1})"
                    )

            return self._fetch_frames(start=key, stop=key + 1, step=1)[0]

        elif isinstance(key, slice):
            if (key.start or 0) < 0 or (key.stop or 0) < 0:
                if not sealed:
                    raise IndexNotYetThereError(
                        "Can't slice from end of stream until it is sealed"
                    )

            # Resolve the slice in the standard way
            start, stop, step = key.indices(len(self))

            return self._fetch_frames(start=start, stop=stop, step=step)

        else:
            raise TypeError(f"{type(key)}")

    def _need_last_only(self, last_only: bool) -> bool:
        # Lima2 event stream represents current progress
        # -> only the latest one is relevant.
        return True

    def _build_view_from_events(
        self, index: int, events: EventRange, last_only: bool
    ) -> Lima2View:
        """
        Build a Lima2View to access a slice of frames which starts at `index`,
        and ends at the most recent frame according to `events`.
        """
        _logger.debug(f"{self.name}: {index=} -> {events=}")

        # events.data[-1] corresponds to the current number of contiguous frames
        # accessible from the lima2 backend.
        stop_idx = events.data[-1]

        if stop_idx <= index:
            # no new image despite new events
            raise EmptyViewException

        return Lima2View(
            services=self._services,
            acq_uuid=self._acq_uuid,
            source=self._source,
            start=stop_idx - 1 if last_only else index,
            stop=stop_idx,
        )

    ####################################################################################
    # LimaDirectAccess
    ####################################################################################

    def get_last_live_image(self) -> ImageData:
        return get_frame(
            services=self._services,
            acq_uuid=self._acq_uuid,
            source=self._source,
            frame_idx=-1,
        )

    ####################################################################################
    # Private API
    ####################################################################################

    def _fetch_frames(self, start: int, stop: int, step: int) -> np.ndarray:
        """Get frame data online or offline, depending on the current state."""
        if self.is_sealed():
            if self._master_file is not None:
                # Default to an offline lookup
                filepath, datapath = self._master_file
                return self._fetch_from_disk(
                    filepath=filepath,
                    datapath=datapath,
                    start=start,
                    stop=stop,
                    step=step,
                )
            else:
                # Try online, in case backends still have the frames we want
                _logger.warning(
                    f"Requesting frames {start}:{stop}:{step} after stream is sealed, "
                    f"but this frame source ({self._source}) isn't persistent."
                )
                return self._fetch_online(start=start, stop=stop, step=step)

        else:
            return self._fetch_online(start=start, stop=stop, step=step)

    def _fetch_online(self, start: int, stop: int, step: int) -> np.ndarray:
        """Get frame data directly from the Lima2 devices."""
        _logger.info(
            f"Fetching {self._source} {start}:{stop}:{step} from lima2 backend"
        )

        frames = []
        for idx in range(start, stop, step):
            try:
                frames.append(
                    get_frame(
                        services=self._services,
                        acq_uuid=self._acq_uuid,
                        source=self._source,
                        frame_idx=idx,
                    ).array
                )
            except RuntimeError as e:
                # Raise if any frame can't be accessed
                raise IndexNoMoreThereError(
                    f"Can't fetch {self._source} {range(start, stop, step)}: {e}"
                ) from e
            except ValueError as e:
                # Frame source has no associated memory buffer (raw_frame)
                raise IndexNoMoreThereError(
                    f"Can't fetch {self._source}: no associated live data"
                ) from e

        return np.asarray(frames)

    def _fetch_from_disk(
        self, filepath: str, datapath: str, start: int, stop: int, step: int
    ) -> np.ndarray:
        """Get frame data from a file (i.e. "offline")."""
        _logger.info(
            f"Fetching {self._source} {start}:{stop}:{step} from disk via {filepath}"
        )

        with dynamic_hdf5.File(filepath, retry_timeout=10, retry_period=1) as file:
            return file[datapath][start:stop:step]
