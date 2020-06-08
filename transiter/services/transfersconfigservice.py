from transiter.db.queries import stopqueries, systemqueries
from transiter import exceptions
from transiter.services import geography, views
from transiter.db import dbconnection, models
import typing


def list_all():
    return "list all"


@dbconnection.unit_of_work
def preview(system_ids, distance):
    systems = _list_systems(system_ids)
    return _convert_db_transfers_to_view_transfers(_build_transfers(systems, distance))


def create(system_ids, distance):
    return f"create {system_ids} {distance}"


def get_by_id(config_id):
    return f"get {config_id}"


def update(config_id, system_ids, distance):
    return f"create {config_id} {system_ids} {distance}"


def delete(config_id):
    return f"delete {config_id}"


def _list_systems(system_ids):
    if len(system_ids) == 1:
        raise exceptions.InvalidInput(
            "At least two systems must be provided for a transfers config."
        )
    systems = systemqueries.list_all(system_ids)
    if len(system_ids) == len(systems):
        return systems
    missing_system_ids = set(system_ids)
    for system in systems:
        missing_system_ids.remove(system.id)
    raise exceptions.InvalidInput(
        f"The following system IDs are invalid: {', '.join(system_ids)}"
    )


def _build_transfers(systems, distance) -> typing.Iterable[models.Transfer]:
    # TODO: instead of just looking at the root node, we should inspect all nodes.
    #  If two nodes match, link their root nodes
    system_id_to_stops = {
        system.id: stopqueries.list_all_in_system_with_no_parent(system.id)
        for system in systems
    }
    all_stops = sum(system_id_to_stops.values(), start=[])
    pairs = []
    for system_id, stops in system_id_to_stops.items():
        for stop_1 in stops:
            for stop_2 in all_stops:
                if stop_2.system.id == system_id:
                    continue
                if (
                    geography.distance(
                        stop_1.latitude,
                        stop_1.longitude,
                        stop_2.latitude,
                        stop_2.longitude,
                    )
                    > distance
                ):
                    continue
                pairs.append((stop_1, stop_2))
    pairs.sort(
        key=lambda pair: geography.distance(
            float(pair[0].latitude),
            float(pair[0].longitude),
            float(pair[1].latitude),
            float(pair[1].longitude),
        )
    )
    for stop_1, stop_2 in pairs:
        yield models.Transfer(
            from_stop=stop_1,
            to_stop=stop_2,
            type=models.Transfer.Type.GEOGRAPHIC,
            distance=int(
                geography.distance(
                    stop_1.latitude, stop_1.longitude, stop_2.latitude, stop_2.longitude
                )
            ),
        )


def _convert_db_transfers_to_view_transfers(db_transfers):
    view_transfers = []
    for db_transfer in db_transfers:
        from_stop = views.Stop.from_model(db_transfer.from_stop)
        from_stop.system = views.System.from_model(db_transfer.from_stop.system)
        to_stop = views.Stop.from_model(db_transfer.to_stop)
        to_stop.system = views.System.from_model(db_transfer.to_stop.system)
        view_transfers.append(
            views.Transfer(
                from_stop=from_stop,
                to_stop=to_stop,
                type=db_transfer.type,
                distance=db_transfer.distance,
            )
        )
    return view_transfers
