import datetime
import time
import pytest
import requests
from google.transit import gtfs_realtime_pb2 as gtfs

ONE_DAY_IN_SECONDS = 60 * 60 * 24
TIME_1 = datetime.datetime.utcfromtimestamp(time.time() - ONE_DAY_IN_SECONDS)
TIME_2 = datetime.datetime.utcfromtimestamp(time.time() + ONE_DAY_IN_SECONDS)

ALERT_SMALL_JSON = [{"id": "alert_id", "cause": "STRIKE", "effect": "MODIFIED_SERVICE"}]

ALERT_LARGE_JSON = [
    dict(
        **ALERT_SMALL_JSON[0],
        **{
            "active_period": {
                "starts_at": int(TIME_1.timestamp()),
                "ends_at": int(TIME_2.timestamp()),
            },
            "messages": [
                {
                    "header": "Advertencia",
                    "description": "",
                    "url": None,
                    "language": "es",
                }
            ],
        }
    )
]
# TODO: 3 more end to end tests: stops, agencies and trips


def setup_test(
    system_id, informed_entity, install_system_1, transiter_host, source_server
):

    __, realtime_feed_url = install_system_1(system_id)

    message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=int(time.time())),
        entity=[
            gtfs.FeedEntity(
                id="alert_id",
                alert=gtfs.Alert(
                    active_period=[
                        gtfs.TimeRange(
                            start=int(TIME_1.timestamp()), end=int(TIME_2.timestamp()),
                        )
                    ],
                    header_text=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text="Advertencia", language="es"
                            )
                        ],
                    ),
                    informed_entity=[informed_entity],
                    cause=gtfs.Alert.Cause.STRIKE,
                    effect=gtfs.Alert.Effect.MODIFIED_SERVICE,
                ),
            )
        ],
    )

    source_server.put(realtime_feed_url, message.SerializeToString())
    requests.post(
        "{}/systems/{}/feeds/GtfsRealtimeFeed?sync=true".format(
            transiter_host, system_id
        )
    )


@pytest.mark.parametrize(
    "path,entity_id,entity_selector,expected_json",
    [["routes", "A", gtfs.EntitySelector(route_id="A"), ALERT_SMALL_JSON]],
)
def test_alerts_list_entities(
    install_system_1,
    transiter_host,
    source_server,
    path,
    entity_id,
    entity_selector,
    expected_json,
):
    system_id = "test_alerts__get_entity_" + str(hash(path))
    setup_test(
        system_id=system_id,
        informed_entity=entity_selector,
        install_system_1=install_system_1,
        transiter_host=transiter_host,
        source_server=source_server,
    )

    actual_data = requests.get(
        "{}/systems/{}/{}".format(transiter_host, system_id, path)
    ).json()

    entity_id_to_response = {response["id"]: response for response in actual_data}

    assert expected_json == entity_id_to_response[entity_id]["alerts"]


@pytest.mark.parametrize(
    "path,entity_selector,expected_json",
    [
        ["routes/A", gtfs.EntitySelector(route_id="A"), ALERT_LARGE_JSON],
        ["stops/1A", gtfs.EntitySelector(stop_id="1A"), ALERT_SMALL_JSON],
    ],
)
def test_alerts__get_entity(
    install_system_1,
    transiter_host,
    source_server,
    path,
    entity_selector,
    expected_json,
):
    system_id = "test_alerts__get_entity_" + str(hash(path))
    setup_test(
        system_id=system_id,
        informed_entity=entity_selector,
        install_system_1=install_system_1,
        transiter_host=transiter_host,
        source_server=source_server,
    )

    actual_data = requests.get(
        "{}/systems/{}/{}".format(transiter_host, system_id, path)
    ).json()

    assert expected_json == actual_data["alerts"]
