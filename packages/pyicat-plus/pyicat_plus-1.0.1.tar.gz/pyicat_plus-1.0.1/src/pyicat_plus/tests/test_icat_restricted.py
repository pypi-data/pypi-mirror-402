from datetime import date

import pytest
from requests.exceptions import HTTPError

from .utils import generate
from .utils.xmlns import strip_xmlns


def test_login(icatplus_restricted_client):
    client, messages = icatplus_restricted_client

    with pytest.raises(RuntimeError, match="Login is required."):
        _ = client.session_id

    with pytest.raises(HTTPError, match="403 Client Error: Authentication failed"):
        _ = client.login("wrong")

    result = client.login("correct")

    assert result["sessionId"] == client.session_id

    assert messages.empty()


def test_login_with_username_plugin(icatplus_restricted_client):
    client, messages = icatplus_restricted_client

    result = client.login(password="correct", username="john", plugin="db")

    assert result["sessionId"] == client.session_id
    assert messages.empty()


def test_get_investigations_by(icatplus_restricted_client, icat_metadata_client):
    client, messages = icatplus_restricted_client
    mclient, mmessages = icat_metadata_client

    with pytest.raises(RuntimeError, match="Login is required."):
        _ = client.get_investigations_by()

    assert client.login("correct")

    investigations = client.get_investigations_by()
    assert isinstance(investigations, list)

    mclient.start_investigation(proposal="hg123", beamline="id00")
    message = mmessages.get(timeout=10)

    investigations = client.get_investigations_by()
    expected = [
        {
            "experiment": "hg123",
            "id": 0,
            "instrument": {
                "name": "id00",
            },
            "proposal": "hg123",
            "startDate": message["investigation"]["startDate"],
        }
    ]
    assert strip_xmlns(investigations) == expected

    assert messages.empty()
    assert mmessages.empty()


def test_get_parcels_by(icatplus_restricted_client):
    client, messages = icatplus_restricted_client

    investigation_id = generate.investigation_id()

    with pytest.raises(RuntimeError, match="Login is required."):
        _ = client.get_parcels_by(investigation_id)

    assert client.login("correct")

    parcels = client.get_parcels_by(investigation_id)

    assert parcels == []
    assert messages.empty()


@pytest.mark.parametrize(
    "session_start_date, expected_ids",
    [
        (None, ["sa", "sb"]),
        (date(2020, 2, 1), ["sa"]),
    ],
)
def test_get_sample_metadata_by(
    icatplus_restricted_client, session_start_date, expected_ids
):
    client, messages = icatplus_restricted_client
    proposal = "hg237"
    beamline = "id13"

    with pytest.raises(RuntimeError, match="Login is required."):
        _ = client.get_sample_metadata_by(proposal, beamline, session_start_date)

    assert client.login("correct")

    samples = client.get_sample_metadata_by(proposal, beamline, session_start_date)

    returned_ids = [s["id"] for s in samples]
    assert returned_ids == expected_ids

    assert messages.empty()


def test_get_samples_by(icatplus_restricted_client):
    client, messages = icatplus_restricted_client

    investigation_id = generate.investigation_id()

    with pytest.raises(RuntimeError, match="Login is required."):
        _ = client.get_samples_by(investigation_id)

    assert client.login("correct")

    samples = client.get_samples_by(investigation_id)

    assert samples == []
    assert messages.empty()


@pytest.mark.parametrize(
    "params, expected_ids",
    [
        ({"investigation_id": "mx415"}, ["sa", "sb"]),
        ({"investigation_id": "mx2012"}, ["sc"]),
        ({"sample_ids": "sc"}, ["sc"]),
        ({"investigation_id": "mx415", "sample_ids": "sa"}, ["sa"]),
        ({"investigation_id": "mx100"}, []),
        ({"sample_ids": "sd"}, []),
    ],
)
def test_get_samples_by_returns_expected_data(
    icatplus_restricted_client, params, expected_ids
):
    client, messages = icatplus_restricted_client
    client.login("correct")

    samples = client.get_samples_by(**params)
    returned_ids = [s["id"] for s in samples]

    assert returned_ids == expected_ids
    assert messages.empty()


def test_get_sample_files_information_by(icatplus_restricted_client):
    client, messages = icatplus_restricted_client

    sample_id = generate.icat_id()

    with pytest.raises(RuntimeError, match="Login is required."):
        _ = client.get_sample_files_information_by(sample_id)

    assert client.login("correct")

    sample_files = client.get_sample_files_information_by(sample_id)

    assert sample_files == []
    assert messages.empty()


@pytest.mark.parametrize(
    "use_chunks, chunk_size",
    [
        (False, None),
        (True, 1024),
    ],
)
def test_download_file_by_sample_parametrized(
    icatplus_restricted_client, use_chunks, chunk_size
):
    client, messages = icatplus_restricted_client

    sample_id = generate.icat_id()
    resource_id = generate.icat_id()

    if use_chunks:
        with pytest.raises(RuntimeError, match="Login is required."):
            _ = client.download_file_by(
                sample_id, resource_id, use_chunks=use_chunks, chunk_size=chunk_size
            )
    else:
        with pytest.raises(RuntimeError, match="Login is required."):
            _ = client.download_file_by(sample_id, resource_id)

    assert client.login("correct")

    result = client.download_file_by(
        sample_id, resource_id, use_chunks=use_chunks, chunk_size=chunk_size
    )

    assert isinstance(result, bytes)
    assert result == b"fake file content"
    assert messages.empty()
