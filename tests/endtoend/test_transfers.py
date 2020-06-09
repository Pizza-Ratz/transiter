import pytest
import io
import zipfile
import dataclasses
import csv
import typing
import requests

SYSTEM_CONFIG = """

name: Test System for transfers

feeds:

  gtfsstatic:
    http:
      url: "{static_feed_url}"
    parser:
      built_in: GTFS_STATIC
    required_for_install: true

"""


@pytest.fixture
def install_system_with_stops(
    install_system, source_server, source_server_host_within_transiter
):
    def build_zip(stops: typing.List[Stop]):
        stops_file = io.StringIO()
        writer = csv.writer(stops_file)
        writer.writerow(["stop_id", "stop_name", "stop_lat", "stop_lon"])
        for stop in stops:
            writer.writerow([stop.id, stop.id, stop.latitude, stop.longitude])

        output_bytes = io.BytesIO()
        with zipfile.ZipFile(output_bytes, "w") as zip_file:
            zip_file.writestr("stops.txt", stops_file.getvalue())
        return output_bytes.getvalue()

    def install(system_id, stops):
        static_feed_url = source_server.create("", "/" + system_id + "/gtfs-static.zip")
        source_server.put(static_feed_url, build_zip(stops))

        install_system(
            system_id,
            SYSTEM_CONFIG.format(
                static_feed_url=source_server_host_within_transiter
                + "/"
                + static_feed_url
            ),
        )

    return install


@dataclasses.dataclass
class Stop:
    id: str
    latitude: float
    longitude: float


STOP_1_1 = "1_1"
STOP_1_2 = "1_2"
STOP_1_3 = "1_3"
STOP_2_1 = "2_1"
STOP_2_2 = "2_2"
STOP_2_3 = "2_3"
STOPS_1 = [Stop(STOP_1_1, 1.0, 1), Stop(STOP_1_2, 2.0, 2), Stop(STOP_1_3, 4.0, 4)]
STOPS_2 = [Stop(STOP_2_1, 1.4, 1), Stop(STOP_2_2, 2.8, 2), Stop(STOP_2_3, 5.2, 4)]


@pytest.mark.parametrize(
    "distance,expected_tuples",
    [
        [300, set()],
        [50000, {(STOP_1_1, STOP_2_1), (STOP_2_1, STOP_1_1)}],
        [
            100000,
            {
                (STOP_1_1, STOP_2_1),
                (STOP_2_1, STOP_1_1),
                (STOP_1_2, STOP_2_2),
                (STOP_2_2, STOP_1_2),
            },
        ],
    ],
)
def test_preview(
    install_system_with_stops, transiter_host, system_id, distance, expected_tuples
):
    system_1_id = system_id + "_1"
    system_2_id = system_id + "_2"

    install_system_with_stops(system_1_id, STOPS_1)
    install_system_with_stops(system_2_id, STOPS_2)

    preview_response = requests.post(
        transiter_host + "/admin/transfers-config/preview",
        params={"system_id": [system_1_id, system_2_id], "distance": distance},
    ).json()

    transfer_tuples = {
        (transfer["from_stop"]["id"], transfer["to_stop"]["id"])
        for transfer in preview_response
    }

    assert expected_tuples == transfer_tuples


# Two systems just with stops

# - preview
# - create. Verify visible in the stop's endpoint
# - update. Verify update visible in the stop's endpoint
# - delete. Verify transfers not visibile
# - list all (tricky to enable this to run in parallel)
# get
