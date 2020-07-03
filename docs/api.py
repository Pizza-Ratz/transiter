import dataclasses
import inspect
import typing
from transiter.http import endpoints, flaskapp
from transiter.http import httpmanager
from transiter.http.flaskapp import app


@dataclasses.dataclass
class Group:
    name: str
    module: typing.Any
    extra_modules: list = dataclasses.field(default_factory=list)
    endpoints: list = dataclasses.field(default_factory=list)
    extra_endpoints: list = dataclasses.field(default_factory=list)

    def page(self):
        return f"api/{self.name}.md".replace(" ", "-").lower()

    def all_modules(self):
        return [self.module] + self.extra_modules

    def all_endpoints(self):
        return self.endpoints + self.extra_endpoints


@dataclasses.dataclass
class Endpoint:
    title: str
    rule: str
    method: str
    doc: str
    module: str


groups = [
    Group("Entrypoint", flaskapp, [endpoints.docsendpoints]),
    Group("Systems", endpoints.systemendpoints),
    Group("Stops", endpoints.stopendpoints),
    Group("Routes", endpoints.routeendpoints),
    Group("Trips", endpoints.tripendpoints),
    Group("Agencies", endpoints.agencyendpoints),
    Group("Feeds", endpoints.feedendpoints),
    Group("Inter-system transfers", endpoints.transfersconfigendpoints),
    Group("Admin", endpoints.adminendpoints),
]


def match_group(endpoint, endpoint_module):
    for group in groups:
        if endpoint_module in group.all_modules():
            return group
    return None


def clean_doc(raw_doc):
    if raw_doc is None:
        return "Title unknown", "No doc provided!"
    doc = inspect.cleandoc(raw_doc).strip()
    first_new_line = doc.find("\n")
    if first_new_line >= 0:
        title = doc[:first_new_line].strip()
        body = doc[first_new_line + 1 :]
    else:
        title = doc
        body = ""
    return title, body


def populate_endpoints():
    func_to_rule = {}
    for rule in app.url_map.iter_rules():
        if rule.rule[-1] == "/" and rule.rule != "/" and rule.rule[:5] != "/docs":
            continue
        func_to_rule[app.view_functions[rule.endpoint]] = rule

    for endpoint in httpmanager.get_documented_endpoints():
        rule = func_to_rule.get(endpoint.func)
        if rule is None:
            print("Skipping")
            continue
        del func_to_rule[endpoint.func]
        group = match_group(rule.endpoint, inspect.getmodule(endpoint.func))
        if group is None:
            print(f"Warning: no group for {rule.endpoint}, skipping ")
            continue
        # print(type(rule.endpoint))
        # print(rule.endpoint)
        function = app.view_functions[rule.endpoint]
        doc = function.__doc__
        if doc is None:
            print(f"Warning: no documentation for {rule.endpoint}, skipping")
            continue

        title, body = clean_doc(doc)

        if title[-1] == ".":
            print(
                f"Warning: first line of documentation for {rule.endpoint} ends with a period, skipping."
            )
            continue

        if group.module is inspect.getmodule(endpoint.func):
            add_to = group.endpoints
        else:
            add_to = group.extra_endpoints
        add_to.append(
            Endpoint(
                title=title,
                rule=rule.rule,
                method=calculate_method(rule.methods),
                doc=body,
                module=group.module,
            )
        )

    for func, rule in func_to_rule.items():
        print(
            f"The function {func} is registered as a flask route but has no documentation"
        )


def calculate_method(methods):
    for method in ["GET", "POST", "PUT", "DELETE"]:
        if method in methods:
            return method


a = ""


def build_quick_reference_row(endpoint: Endpoint, page: str):
    internal_url = endpoint.title.replace(" ", "-").lower()
    return f"[{endpoint.title}]({page}#{internal_url}) | `{endpoint.method} {endpoint.rule}`"


populate_endpoints()

base = """
# Quick reference

Endpoints mostly return JSON data; exceptions are specifically noted.
In order to avoid stale documentation,
the structure of the JSON data returned by each endpoint
 is not described here, but can be inspected on the
[demo site](https://demo.transiter.io) or
by clicking any of the example links below.

"""

pages = ["api.md"]
with open("docs/docs/api/index.md", "w") as f:

    print(base, file=f)
    print("Operation | API endpoint", file=f)
    print("----------|-------------", file=f)
    for group in groups:
        print(f"**{group.name} endpoints**", file=f)
        for endpoint in group.all_endpoints():
            print(build_quick_reference_row(endpoint, group.page()[4:]), file=f)

for group in groups:
    pages.append(group.page())
    with open(f"docs/docs/{group.page()}", "w") as f:
        print("", file=f)

        if not isinstance(group.module, str):
            title, doc = clean_doc(group.module.__doc__)
            print(f"# {title}", file=f)
            print("", file=f)
            print(doc, file=f)
        else:
            print("Warning: module refered to as string")
            print(f"# {group.name}", file=f)
        for endpoint in group.all_endpoints():
            print("", file=f)
            print(f"## {endpoint.title}", file=f)
            print("", file=f)
            print(f"`{endpoint.method} {endpoint.rule}`", file=f)
            print("", file=f)
            print(endpoint.doc, file=f)


for page in pages:
    print(f"  - {page}")
