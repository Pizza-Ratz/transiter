import dataclasses
import inspect
from transiter.http.flaskapp import app


@dataclasses.dataclass
class Group:
    name: str
    module: str
    endpoints: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Endpoint:
    title: str
    rule: str
    method: str
    doc: str


groups = [
    Group("Transit system", "transiter.http.endpoints.systemendpoints"),
    Group("Stop", "transiter.http.endpoints.stopendpoints"),
    Group("Route", "transiter.http.endpoints.routeendpoints"),
    Group("Trip", "transiter.http.endpoints.tripendpoints"),
    Group("Feed", "transiter.http.endpoints.feedendpoints"),
    Group("Admin", "transiter.http.endpoints.adminendpoints"),
]


def match_group(endpoint):
    for group in groups:
        if group.module == endpoint[: len(group.module)]:
            return group
    return None


def populate_endpoints():
    for rule in app.url_map.iter_rules():
        if rule.rule[-1] == "/":
            continue
        group = match_group(rule.endpoint)
        if group is None:
            continue
        # print(type(rule.endpoint))
        # print(rule.endpoint)
        function = app.view_functions[rule.endpoint]
        doc = function.__doc__
        if doc is None:
            print(f"Warning: no documentation for {rule.endpoint}, skipping")
            continue

        doc = inspect.cleandoc(doc)
        doc = doc.strip()
        first_new_line = doc.find("\n")
        if first_new_line >= 0:
            title = doc[:first_new_line].strip()
            body = doc[first_new_line + 1 :]
        else:
            title = doc
            body = ""

        if title[-1] == ".":
            print(
                f"Warning: first line of documentation for {rule.endpoint} ends with a period, skipping."
            )
            continue

        group.endpoints.append(
            Endpoint(
                title=title,
                rule=rule.rule,
                method=calculate_method(rule.methods),
                doc=body,
            )
        )


def calculate_method(methods):
    for method in ["GET", "POST", "PUT", "DELETE"]:
        if method in methods:
            return method


a = ""


def build_quick_reference_row(endpoint: Endpoint):
    internal_url = endpoint.title.replace(" ", "-").lower()
    return f"[{endpoint.title}](#{internal_url}) | `{endpoint.method} {endpoint.rule}`"


populate_endpoints()

base = """
# HTTP API reference


This page details the HTTP endpoints exposed by Transiter.

Endpoints mostly return JSON data; exceptions are specifically noted.
In order to avoid stale documentation,
the structure of the JSON data returned by each endpoint
 is not described here, but can be inspected on the
[demo site](https://demo.transiter.io) or
by clicking any of the example links below.

"""
with open("docs/docs/api.md", "w") as f:

    print(base, file=f)
    print("## Quick reference", file=f)
    print("Operation | API endpoint", file=f)
    print("----------|-------------", file=f)
    for group in groups:
        print(f"**{group.name} endpoints**", file=f)
        for endpoint in group.endpoints:
            print(build_quick_reference_row(endpoint), file=f)

    for group in groups:
        print("", file=f)
        print(f"## {group.name} endpoints", file=f)
        for endpoint in group.endpoints:
            print("", file=f)
            print(f"### {endpoint.title}", file=f)
            print("", file=f)
            print(f"`{endpoint.method} {endpoint.rule}`", file=f)
            print("", file=f)
            print(endpoint.doc, file=f)
