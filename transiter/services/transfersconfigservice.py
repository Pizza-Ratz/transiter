def list_all():
    return "list all"


def preview(system_ids, distance):
    return f"preview {system_ids} {distance}"


def create(system_ids, distance):
    return f"create {system_ids} {distance}"


def get_by_id(config_id):
    return f"get {config_id}"


def update(config_id, system_ids, distance):
    return f"create {config_id} {system_ids} {distance}"


def delete(config_id):
    return f"delete {config_id}"
