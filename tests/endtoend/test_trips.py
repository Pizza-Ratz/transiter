import uuid

import pytest
import requests
from google.transit import gtfs_realtime_pb2 as gtfs


@pytest.fixture
def system_id(request):
    return request.node.originalname + "__" + str(uuid.uuid4())


TRIP_ID = "trip_id"
ROUTE_ID = "A"
TRIP_INITIAL_TIMETABLE = {
    "1AS": 300,
    "1BS": 600,
    "1CS": 800,
    "1DS": 900,
    "1ES": 1800,
    "1FS": 2500,
}


@pytest.mark.parametrize("use_stop_sequences", [True, False])
@pytest.mark.parametrize("current_time", [0, 700, 4000])
@pytest.mark.parametrize(
    "stop_id_to_time_2",
    [
        # Basic case where the second update does nothing.
        TRIP_INITIAL_TIMETABLE,
        # Change the stop times
        {"1AS": 200, "1BS": 600, "1CS": 800, "1DS": 900, "1ES": 1800, "1FS": 2500},
        # Add a new stop
        {
            "1AS": 200,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1FS": 2500,
            "1GS": 2600,
        },
        # Delete a stop from the end
        {"1AS": 200, "1BS": 600, "1CS": 800, "1DS": 900, "1ES": 1800},
        # Swap the ordering of the stops
        {
            "1AS": 300,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1GS": 2500,
            "1FS": 3000,
        },
    ],
)
class TestTrip:
    def test_stop_view(
        self,
        install_system_1,
        system_id,
        transiter_host,
        source_server,
        stop_id_to_time_2,
        current_time,
        use_stop_sequences,
    ):
        __, realtime_feed_url = install_system_1(system_id)

        for stop_id_to_time, time_at_update in [
            (TRIP_INITIAL_TIMETABLE, 0),
            (stop_id_to_time_2, current_time),
        ]:
            source_server.put(
                realtime_feed_url,
                build_gtfs_rt_message(
                    current_time, stop_id_to_time, use_stop_sequences
                ).SerializeToString(),
            )
            requests.post(
                f"{transiter_host}/systems/{system_id}/feeds/GtfsRealtimeFeed?sync=true"
            )

        stop_id_to_stop_sequence = {
            stop_id: stop_sequence + 25
            for stop_sequence, stop_id in enumerate(stop_id_to_time_2.keys())
        }
        all_stop_ids = set(TRIP_INITIAL_TIMETABLE.keys()).union(
            stop_id_to_time_2.keys()
        )
        for stop_id in all_stop_ids:
            response = requests.get(
                f"{transiter_host}/systems/{system_id}/stops/{stop_id}"
            ).json()

            time = stop_id_to_time_2.get(stop_id)
            if time is None or time < current_time:
                assert [] == response["stop_times"]
                continue

            stop_time = response["stop_times"][0]

            assert stop_time["trip"]["id"] == TRIP_ID
            assert stop_time["trip"]["route"]["id"] == ROUTE_ID
            assert stop_time["arrival"]["time"] == time
            assert stop_time["departure"]["time"] == time + 15
            if use_stop_sequences:
                assert stop_time["stop_sequence"] == stop_id_to_stop_sequence[stop_id]

    def test_trip_view(
        self,
        install_system_1,
        system_id,
        transiter_host,
        source_server,
        stop_id_to_time_2,
        current_time,
        use_stop_sequences,
    ):
        __, realtime_feed_url = install_system_1(system_id)

        for stop_id_to_time, time_at_update in [
            (TRIP_INITIAL_TIMETABLE, 0),
            (stop_id_to_time_2, current_time),
        ]:
            source_server.put(
                realtime_feed_url,
                build_gtfs_rt_message(
                    current_time, stop_id_to_time, use_stop_sequences
                ).SerializeToString(),
            )
            requests.post(
                f"{transiter_host}/systems/{system_id}/feeds/GtfsRealtimeFeed?sync=true"
            )

        stop_id_to_stop_sequence = {
            stop_id: stop_sequence + 25
            for stop_sequence, stop_id in enumerate(stop_id_to_time_2.keys())
        }

        response = requests.get(
            f"{transiter_host}/systems/{system_id}/routes/{ROUTE_ID}/trips/{TRIP_ID}"
        ).json()

        pass


def build_gtfs_rt_message(current_time, stop_id_to_time, use_stop_sequences):
    return gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=current_time),
        entity=[
            gtfs.FeedEntity(
                id="1",
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(
                        trip_id=TRIP_ID, route_id=ROUTE_ID, direction_id=True
                    ),
                    stop_time_update=[
                        gtfs.TripUpdate.StopTimeUpdate(
                            arrival=gtfs.TripUpdate.StopTimeEvent(time=time),
                            departure=gtfs.TripUpdate.StopTimeEvent(time=time + 15),
                            stop_id=stop_id,
                            stop_sequence=stop_sequence + 25
                            if use_stop_sequences
                            else None,
                        )
                        for stop_sequence, (stop_id, time) in enumerate(
                            stop_id_to_time.items()
                        )
                        if time >= current_time
                    ],
                ),
            )
        ],
    )
