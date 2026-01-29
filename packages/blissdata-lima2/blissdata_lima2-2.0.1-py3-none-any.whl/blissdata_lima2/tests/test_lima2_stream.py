# -*- coding: utf-8 -*-
#
# This file is part of the bliss project
#
# Copyright (c) Beamline Control Unit, ESRF
# Distributed under the GNU LGPLv3. See LICENSE for more info.

"""Unit test suite for Lima2 stream and view (streams/lima2.py)."""

from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, call
from uuid import uuid1

import numpy as np
import pytest
from blissdata.exceptions import (
    EmptyViewException,
    IndexNoMoreThereError,
    IndexNotYetThereError,
    IndexWontBeThereError,
)
from blissdata.lima.image_utils import ImageData
from blissdata.streams import EventRange, EventStream
from lima2.common.devencoded.sparse_frame import SparseFrame

from blissdata_lima2 import Lima2Stream, Lima2View
from blissdata_lima2.stream import get_frame


def test_lima2_get_frame():
    services = Mock()
    uuid = str(uuid1())
    frm = get_frame(services=services, acq_uuid=uuid, source="cafe", frame_idx=123)
    services.pipeline.get_frame.assert_called_with(
        frame_idx=123, source="cafe", uuid=uuid
    )
    assert type(frm) is ImageData


def test_lima2_get_sparse_frame():
    mock_frame = Mock(spec=SparseFrame)

    def mock_pipeline_get_frame(frame_idx, source, uuid):
        return mock_frame

    mock_services = SimpleNamespace(
        pipeline=SimpleNamespace(get_frame=mock_pipeline_get_frame)
    )

    uuid = str(uuid1())
    img_data = get_frame(
        services=mock_services, acq_uuid=uuid, source="cafe", frame_idx=123
    )
    mock_frame.densify.assert_called_once()
    assert type(img_data) is ImageData


def test_lima2_view(monkeypatch):
    services = Mock()
    uuid = str(uuid1())
    view = Lima2View(
        services=services,
        acq_uuid=uuid,
        source="cafe",
        start=0,
        stop=42,
    )
    assert len(view) == 42
    assert view.index == 0

    frames = view.get_data()
    assert len(frames) == len(view)

    services.pipeline.get_frame.assert_has_calls(
        [call(uuid=uuid, source="cafe", frame_idx=i) for i in range(42)]
    )

    # RuntimeError
    def mock_get_frame_runtime_error(services, acq_uuid, source, frame_idx):
        raise RuntimeError("frame has left the buffer")

    monkeypatch.setattr(
        "blissdata_lima2.stream.get_frame", mock_get_frame_runtime_error
    )

    with pytest.raises(IndexNoMoreThereError):
        frames = view.get_data()

    # ValueError
    def mock_get_frame_value_error(services, acq_uuid, source, frame_idx):
        raise ValueError("no such frame buffer")

    monkeypatch.setattr("blissdata_lima2.stream.get_frame", mock_get_frame_value_error)

    with pytest.raises(IndexNoMoreThereError):
        frames = view.get_data()


def test_lima2_protocol(data_store):
    uuid = str(uuid1())

    stream_def = Lima2Stream.make_definition(
        name="device:cafe",
        source_name="cafe",
        conductor_hostname="www.lima2.org",
        conductor_port=12345,
        acq_uuid=uuid,
        master_file=None,
        dtype=np.float128,  # fat pixels >:)
        shape=(4, 1024, 512),
    )
    model = data_store._stream_model(
        encoding=stream_def.encoder.info(), info=stream_def.info
    )
    model.info["protocol_version"] = 1  # hack the protocol number
    event_stream = EventStream.create(data_store, stream_def.name, model)

    with pytest.raises(RuntimeError):
        _ = Lima2Stream(event_stream=event_stream)


@pytest.fixture
def lima2_stream(data_store):
    uuid = str(uuid1())

    stream_def = Lima2Stream.make_definition(
        name="device:cafe",
        source_name="cafe",
        conductor_hostname="www.lima2.org",
        conductor_port=12345,
        acq_uuid=uuid,
        master_file=None,
        dtype=np.float128,  # fat pixels >:)
        shape=(4, 1024, 512),
    )
    model = data_store._stream_model(
        encoding=stream_def.encoder.info(), info=stream_def.info
    )

    event_stream = EventStream.create(data_store, stream_def.name, model)
    stream = Lima2Stream(event_stream=event_stream)

    return (stream_def, event_stream, stream)


def test_lima2_stream_attributes(lima2_stream):
    stream_def, event_stream, stream = lima2_stream

    assert stream.plugin == "lima2"
    assert stream.shape == stream_def.info["shape"]
    assert stream.kind == "array"
    assert stream.dtype == stream._dtype
    assert stream._need_last_only(last_only=True)
    assert stream._need_last_only(last_only=False)


def test_lima2_stream_indexing(lima2_stream, monkeypatch):
    stream_def, event_stream, stream = lima2_stream

    # Feed the event stream
    event_stream.send(np.uint32(42))
    event_stream.join()
    assert len(stream) == 42

    event_stream.send(np.uint32(123))
    event_stream.join()
    assert len(stream) == 123

    mock_get_frame = Mock()
    monkeypatch.setattr("blissdata_lima2.stream.get_frame", mock_get_frame)

    # Indexing
    _ = stream[0]
    mock_get_frame.assert_called_with(
        services=stream._services,
        acq_uuid=stream._acq_uuid,
        source="cafe",
        frame_idx=0,
    )

    with pytest.raises(IndexNotYetThereError):
        _ = stream[-1]

    with pytest.raises(IndexNotYetThereError):
        _ = stream[123123]  # wayyy out of bounds, but we're not sealed yet

    with monkeypatch.context() as mpc:
        mpc.setattr(stream, "is_sealed", lambda: True)

        with pytest.raises(IndexWontBeThereError):
            _ = stream[123123]  # wayyy out of bounds and we're sealed

    event_stream.seal()
    event_stream.join()

    _ = stream[-3]
    assert mock_get_frame.mock_calls[-1] == call(
        services=stream._services,
        acq_uuid=stream._acq_uuid,
        source="cafe",
        frame_idx=123 - 3,
    )


def test_lima2_stream_slicing(lima2_stream, monkeypatch):
    stream_def, event_stream, stream = lima2_stream

    # Feed the event stream
    event_stream.send(np.uint32(42))
    event_stream.join()
    assert len(stream) == 42

    event_stream.send(np.uint32(123))
    event_stream.join()
    assert len(stream) == 123

    mock_get_frame = Mock()
    monkeypatch.setattr("blissdata_lima2.stream.get_frame", mock_get_frame)

    # Slicing
    _ = stream[:3]
    assert mock_get_frame.mock_calls[-3:] == [
        call(
            services=stream._services,
            acq_uuid=stream._acq_uuid,
            source="cafe",
            frame_idx=0,
        ),
        call(
            services=stream._services,
            acq_uuid=stream._acq_uuid,
            source="cafe",
            frame_idx=1,
        ),
        call(
            services=stream._services,
            acq_uuid=stream._acq_uuid,
            source="cafe",
            frame_idx=2,
        ),
    ]

    with pytest.raises(IndexNotYetThereError):
        _ = stream[-2:]

    with pytest.raises(IndexNotYetThereError):
        _ = stream[:-2]

    with pytest.raises(TypeError):
        _ = stream["hi :)"]

    event_stream.seal()
    event_stream.join()

    # Now slicing/indexing from end is ok
    _ = stream[-2:]
    assert mock_get_frame.mock_calls[-2:] == [
        call(
            services=stream._services,
            acq_uuid=stream._acq_uuid,
            source="cafe",
            frame_idx=123 - 2,
        ),
        call(
            services=stream._services,
            acq_uuid=stream._acq_uuid,
            source="cafe",
            frame_idx=123 - 1,
        ),
    ]

    _ = stream[:]
    assert mock_get_frame.mock_calls[-123:] == [
        call(
            services=stream._services,
            acq_uuid=stream._acq_uuid,
            source="cafe",
            frame_idx=i,
        )
        for i in range(123)
    ]

    _ = stream.get_last_live_image()
    mock_get_frame.assert_called_with(
        services=stream._services,
        acq_uuid=stream._acq_uuid,
        source="cafe",
        frame_idx=-1,
    )


def test_lima2_stream_build_view(lima2_stream, monkeypatch):
    stream_def, event_stream, stream = lima2_stream

    mock_get_frame = Mock()
    monkeypatch.setattr("blissdata_lima2.stream.get_frame", mock_get_frame)

    view = stream._build_view_from_events(
        index=0,
        events=EventRange(
            index=0,
            nb_expired=0,
            data=[np.uint32(5), np.uint32(24), np.uint32(42)],
            end_of_stream=False,
        ),
        last_only=False,
    )
    assert view._idx_range == range(0, 42)

    view = stream._build_view_from_events(
        index=0,
        events=EventRange(
            index=0,
            nb_expired=0,
            data=[np.uint32(5), np.uint32(24), np.uint32(42)],
            end_of_stream=False,
        ),
        last_only=True,
    )
    assert view._idx_range == range(41, 42)

    with pytest.raises(EmptyViewException):
        # index >= data[-1]
        view = stream._build_view_from_events(
            index=42,
            events=EventRange(
                index=0,
                nb_expired=0,
                data=[np.uint32(5), np.uint32(24), np.uint32(42)],
                end_of_stream=False,
            ),
            last_only=False,
        )


def test_lima2_stream_fetch_frames(lima2_stream, monkeypatch):
    stream_def, event_stream, stream = lima2_stream

    mock_get_frame = Mock()
    monkeypatch.setattr("blissdata_lima2.stream.get_frame", mock_get_frame)

    with monkeypatch.context() as mpc:
        # Stream sealed, has master file
        mock_fetch = Mock()
        mpc.setattr(stream, "_fetch_from_disk", mock_fetch)
        mpc.setattr(stream, "is_sealed", lambda: True)
        mpc.setattr(
            stream,
            "_master_file",
            ("/path/to/master.h5", "entry/instrument/detector/dataset"),
        )

        stream._fetch_frames(start=0, stop=42, step=3)

        mock_fetch.assert_called_once_with(
            filepath="/path/to/master.h5",
            datapath="entry/instrument/detector/dataset",
            start=0,
            stop=42,
            step=3,
        )

    with monkeypatch.context() as mpc:
        # Stream sealed, no master file
        mock_fetch = Mock()
        mpc.setattr(stream, "_fetch_online", mock_fetch)
        mpc.setattr(stream, "is_sealed", lambda: True)
        mpc.setattr(stream, "_master_file", None)

        stream._fetch_frames(start=0, stop=42, step=3)

        mock_fetch.assert_called_once_with(
            start=0,
            stop=42,
            step=3,
        )

    with monkeypatch.context() as mpc:
        # Stream not sealed
        mock_fetch = Mock()
        mpc.setattr(stream, "_fetch_online", mock_fetch)
        mpc.setattr(stream, "is_sealed", lambda: False)

        stream._fetch_frames(start=0, stop=42, step=3)

        mock_fetch.assert_called_once_with(
            start=0,
            stop=42,
            step=3,
        )


def test_lima2_stream_fetch_online(lima2_stream, monkeypatch):
    stream_def, event_stream, stream = lima2_stream

    mock_get_frame = Mock()
    monkeypatch.setattr("blissdata_lima2.stream.get_frame", mock_get_frame)

    stream._fetch_online(start=0, stop=42, step=3)

    mock_get_frame.assert_has_calls(
        [
            call(
                services=stream._services,
                acq_uuid=stream._acq_uuid,
                source=stream._source,
                frame_idx=idx,
            )
            for idx in range(0, 42, 3)
        ]
    )

    # RuntimeError
    def mock_get_frame_runtime_error(services, acq_uuid, source, frame_idx):
        raise RuntimeError("oh no :(")

    monkeypatch.setattr(
        "blissdata_lima2.stream.get_frame", mock_get_frame_runtime_error
    )

    with pytest.raises(IndexNoMoreThereError):
        _ = stream._fetch_online(start=0, stop=1, step=1)

    # ValueError
    def mock_get_frame_value_error(services, acq_uuid, source, frame_idx):
        raise ValueError("oh no :(")

    monkeypatch.setattr("blissdata_lima2.stream.get_frame", mock_get_frame_value_error)

    with pytest.raises(IndexNoMoreThereError):
        _ = stream._fetch_online(start=0, stop=1, step=1)


def test_lima2_stream_fetch_offline(lima2_stream, monkeypatch):
    stream_def, event_stream, stream = lima2_stream

    mock_dynamic_hdf5 = MagicMock()
    monkeypatch.setattr("blissdata_lima2.stream.dynamic_hdf5", mock_dynamic_hdf5)

    stream._fetch_from_disk(
        filepath="/path/to/master.h5",
        datapath="entry/instrument/detector/dataset",
        start=0,
        stop=42,
        step=3,
    )

    mock_dynamic_hdf5.File.assert_called_once()
