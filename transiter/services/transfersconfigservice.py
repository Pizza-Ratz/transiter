import itertools
import typing

from transiter import exceptions
from transiter.db import dbconnection, models
from transiter.db.queries import stopqueries, systemqueries, transfersconfigqueries
from transiter.services import geography, views


# TODO: for cross system transfers, show the system in the stop
@dbconnection.unit_of_work
def list_all() -> typing.List[views.TransfersConfig]:
    # TODO: href
    return list(
        map(views.TransfersConfig.from_model, transfersconfigqueries.list_all())
    )


@dbconnection.unit_of_work
def preview(system_ids, distance) -> typing.List[views.Transfer]:
    systems = _list_systems(system_ids)
    return _convert_db_transfers_to_view_transfers(_build_transfers(systems, distance))


@dbconnection.unit_of_work
def create(system_ids, distance) -> str:
    # TODO: check if it's easy to perf improce
    systems = _list_systems(system_ids)
    transfers_config = models.TransfersConfig(distance=distance, systems=systems)
    _build_and_add_transfers(transfers_config)
    session = dbconnection.get_session()
    session.add(transfers_config)
    session.flush()
    return transfers_config.id


@dbconnection.unit_of_work
def get_by_id(config_id) -> views.TransfersConfig:
    config = _get_transfer_config(config_id)
    view = views.TransfersConfigBig.from_model(config)
    view.transfers = _convert_db_transfers_to_view_transfers(config.transfers)
    return view


@dbconnection.unit_of_work
def update(config_id, system_ids, distance) -> None:
    config = _get_transfer_config(config_id)
    if system_ids is not None:
        config.systems = _list_systems(system_ids)
    if distance is not None:
        config.distance = distance
    _build_and_add_transfers(config)


@dbconnection.unit_of_work
def delete(config_id) -> None:
    config = _get_transfer_config(config_id)
    dbconnection.get_session().delete(config)


def _get_transfer_config(config_id):
    config = transfersconfigqueries.get(config_id)
    if config is None:
        raise exceptions.IdNotFoundError(
            entity_type=models.TransfersConfig, id=config_id
        )
    return config


def _list_systems(system_ids):
    system_ids = set(system_ids)
    if len(system_ids) <= 1:
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


def _build_and_add_transfers(transfers_config):
    transfers_config.transfers = list(
        _build_transfers(transfers_config.systems, transfers_config.distance)
    )


def _build_transfers(systems, distance) -> typing.Iterable[models.Transfer]:
    # TODO: instead of just looking at the root node, we should inspect all nodes.
    #  If two nodes match, link their root nodes

    system_id_to_stops = {
        system.id: stopqueries.list_all_in_system_with_no_parent(system.id)
        for system in systems
    }
    pairs = []
    for system_1_id, stops_1 in system_id_to_stops.items():
        for stop_1 in stops_1:
            for system_2_id, stops_2 in system_id_to_stops.items():
                if system_1_id == system_2_id:
                    continue
                for stop_2 in stops_2:
                    stops_distance = geography.distance(
                        stop_1.latitude,
                        stop_1.longitude,
                        stop_2.latitude,
                        stop_2.longitude,
                    )
                    if stops_distance > distance:
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
            distance=geography.distance(
                stop_1.latitude, stop_1.longitude, stop_2.latitude, stop_2.longitude
            ),
        )


def _convert_db_transfers_to_view_transfers(db_transfers):
    return [
        views.Transfer.from_model(
            transfer,
            views.Stop.from_model(transfer.from_stop, show_system=True),
            views.Stop.from_model(transfer.to_stop, show_system=True),
        )
        for transfer in db_transfers
    ]
