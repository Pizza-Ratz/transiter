import typing
from transiter.services import views
from transiter import models
from transiter.data.queries import alertqueries


_model_type_to_alert_query = {
    models.Route: alertqueries.get_route_pk_to_active_alerts,
    models.Stop: alertqueries.get_stop_pk_to_active_alerts,
}


def add_alerts_to_views(
    built_views: typing.List[views.View],
    db_models: typing.List[models.Base],
    alerts_detail: views.AlertDetail,
):
    if alerts_detail == views.AlertDetail.NONE:
        return
    if len(db_models) == 0:
        return
    query = _model_type_to_alert_query[type(db_models[0])]
    entity_id_to_pk = {entity.id: entity.pk for entity in db_models}
    entity_pk_to_alerts = query(
        entity_id_to_pk.values(), load_messages=alerts_detail.value.need_messages
    )
    for view in built_views:
        view.alerts = [
            alerts_detail.value.clazz.from_models(active_period, alert)
            for active_period, alert in entity_pk_to_alerts.get(
                entity_id_to_pk.get(view.id), []
            )
        ]
