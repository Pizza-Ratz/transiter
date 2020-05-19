import datetime
import time

import requests
from google.transit import gtfs_realtime_pb2 as gtfs

ONE_DAY_IN_SECONDS = 60 * 60 * 24
TIME_1 = datetime.datetime.utcfromtimestamp(time.time() - ONE_DAY_IN_SECONDS)
TIME_2 = datetime.datetime.utcfromtimestamp(time.time() + ONE_DAY_IN_SECONDS)


def test_alerts(install_system_1, transiter_host, source_server):
    __, realtime_feed_url = install_system_1("test_alerts")

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
                    informed_entity=[gtfs.EntitySelector(route_id="A")],
                    cause=gtfs.Alert.Cause.STRIKE,
                    effect=gtfs.Alert.Effect.MODIFIED_SERVICE,
                ),
            )
        ],
    )

    source_server.put(realtime_feed_url, message.SerializeToString())
    requests.post(
        transiter_host + "/systems/test_alerts/feeds/GtfsRealtimeFeed?sync=true"
    )

    actual_data = requests.get(transiter_host + "/systems/test_alerts/routes/A").json()

    assert actual_data["alerts"] == [
        {
            "id": "alert_id",
            "cause": "STRIKE",
            "effect": "MODIFIED_SERVICE",
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
    ]
