from typing import Tuple, List
from geodesic.utils import DeferredImport
from geodesic.client import raise_on_error
from geodesic.bases import _APIObject
from geodesic.service import RequestsServiceClient
from geodesic.entanglement.object import Object, Connection, Predicate
from geodesic.entanglement.graph import Graph

from rich.table import Table
from rich.console import Console

graphql_client = RequestsServiceClient("entanglement", api="graphql", version=1)

nx = DeferredImport("networkx")

QUALIFIERS = """
    class
    domain
    category
    type
    name
"""

OBJECT_FRAGMENT = f"""
fragment objectParts on Object {{
    uid
    {QUALIFIERS}
    project
    alias
    description
    xid
    item
    geometry
}}
"""

PROJECT_FRAGMENT = """
fragment projectParts on Project {
    uid
    name
    alias
    description
    owner
    keywords
}
"""

CONNECTION_FRAGMENT = """
fragment connectionParts on Connection {
    subject {
        ...objectParts
    }
    predicate
    object {
        ...objectParts
    }
    attributes
}
"""

VERSION_FRAGMENT = """
fragment versionParts on Version {
    uid
    versionTag
    validFrom
    validTo
    latest
    deleted
}
"""

OBJECT_REF_FRAGMENT = """
fragment objectRefParts on Object {
    uid
    name
    class
    project
}
"""

CONNECTION_REF_FRAGMENT = """
fragment connectionRefParts on Connection {
    subject {
        ...objectRefParts
    }
    predicate
    object {
        ...objectRefParts
    }
    attributes
}
"""

OBJECT_DESC_FRAGMENT = f"""
fragment objectDescParts on Object {{
    uid
    {QUALIFIERS}
    description
    project
}}
"""

CONNECTION_DESC_FRAGMENT = """
fragment connectionDescParts on Connection {
    subject {
        ...objectDescParts
    }
    predicate
    object {
        ...objectDescParts
    }
    attributes
}
"""

FRAGMENTS = {
    "objectParts": OBJECT_FRAGMENT,
    "projectParts": PROJECT_FRAGMENT,
    "connectionParts": CONNECTION_FRAGMENT,
    "versionParts": VERSION_FRAGMENT,
    "objectRefParts": OBJECT_REF_FRAGMENT,
    "connectionRefParts": CONNECTION_REF_FRAGMENT,
    "objectDescParts": OBJECT_DESC_FRAGMENT,
    "connectionDescParts": CONNECTION_DESC_FRAGMENT,
}


def _get_error_table(errors: List[dict]) -> Table:
    messages_and_counts = {}
    for err in errors:
        if "message" in err:
            messages_and_counts[err["message"]] = messages_and_counts.get(err["message"], 0) + 1

    table = Table(title="GraphQL Query Errors")
    table.add_column("Error Message", style="orange1")
    table.add_column("Count", style="yellow")
    for message, count in messages_and_counts.items():
        table.add_row(message, str(count))
    return table


class GraphResponse(_APIObject):
    """The response from a `graph` query on the Entanglement GraphQL API."""

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    def as_networkx_graph(self) -> Graph:
        """Returns the response as a networkx graph."""
        nodes, edges = self.as_objects_and_connections()
        return Graph(nodes=nodes, edges=edges)

    def as_objects_and_connections(self) -> Tuple[List[Object], List[Connection]]:
        """Returns the response as a dictionary of objects and connections.

        This method requires minimal fields to be present:
        - Objects need: uid, name, class
        - Connections need: subject (with uid, name, class), predicate,
          object (with uid, name, class)

        The objectParts and connectionParts fragments will work, but custom
        fragments with at least these minimal fields are also supported.
        """
        # Validate that the graph response has the minimal required fields
        if not self.get("graph"):
            return {}, []

        # Check first object for required fields
        graph_items = self["graph"]
        if len(graph_items) > 0:
            first_obj = graph_items[0]
            required_obj_fields = ["uid", "name", "class"]
            missing_fields = [f for f in required_obj_fields if f not in first_obj]
            if missing_fields:
                raise ValueError(
                    f"Query must include minimal object fields: uid, name, class. "
                    f"Missing: {', '.join(missing_fields)}. "
                    "Use the objectParts fragment or include these fields "
                    "in your custom fragment."
                )

            # Check if connections exist, validate connection fields
            if "connections" in first_obj and len(first_obj["connections"]) > 0:
                first_conn = first_obj["connections"][0]
                required_conn_fields = ["subject", "predicate", "object"]
                missing_conn_fields = [f for f in required_conn_fields if f not in first_conn]
                if missing_conn_fields:
                    raise ValueError(
                        "Query must include minimal connection fields: "
                        f"subject, predicate, object. "
                        f"Missing: {', '.join(missing_conn_fields)}. "
                        "Use the connectionParts fragment or include these "
                        "fields in your custom fragment."
                    )

                # Check nested object fields in connections
                for conn_obj_key in ["subject", "object"]:
                    if conn_obj_key in first_conn:
                        conn_obj = first_conn[conn_obj_key]
                        missing_nested = [f for f in required_obj_fields if f not in conn_obj]
                        if missing_nested:
                            raise ValueError(
                                f"Connection {conn_obj_key} must include "
                                f"minimal fields: uid, name, class. "
                                f"Missing: {', '.join(missing_nested)}. "
                                "Use the connectionParts fragment or include "
                                "these fields in your custom fragment."
                            )

        objects = {}
        connections = []
        for obj in self["graph"]:
            if "connections" in obj:
                objs, conns = _parse_connections(obj)
                connections.extend(conns)
                for o in objs.values():
                    if o["uid"] in objects or o.get("name", "") == "":
                        continue
                    objects[o["uid"]] = Object(**o)
                obj.pop("connections")
            objects[obj["uid"]] = Object(**obj)

        return objects, connections

    def raw_response(self) -> dict:
        """Returns the 'data' from the raw graphql response."""
        return dict(**self)

    def error_summary(self) -> None:
        """Prints a summary of errors from the GraphQL response, if any."""
        if "errors" in self and self["errors"]:
            table = _get_error_table(self["errors"])
            console = Console()
            console.print(table)

    def _repr_mimebundle_(self, include=None, exclude=None) -> str:
        from prettytable import PrettyTable, TableStyle

        if "errors" in self and self["errors"]:
            table = PrettyTable()
            table.set_style(TableStyle.MARKDOWN)
            table.field_names = ["Error Message", "Count"]
            messages_and_counts = {}
            for err in self["errors"]:
                if "message" in err:
                    messages_and_counts[err["message"]] = (
                        messages_and_counts.get(err["message"], 0) + 1
                    )
            for message, count in messages_and_counts.items():
                table.add_row([message, str(count)])
            # return {"text/html": str(table)}
            return {"text/html": table._repr_html_()}


def graph(query: str, return_errors: bool = False) -> GraphResponse:
    """Runs a `graph` query to the GraphQL API for Entanglement.

    This function executes a GraphQL query to the `graph` top level query in
    `Entanglement`. This enables your queries to return arbitrary subgraphs, by
    providing a single GraphQL query.

    Any query from the API can be specified and custom fragments can be added
    as well. The structure of the response depends on how the request is built.
    If you want to use `as_objects_and_connections()` or `as_networkx_graph()`,
    use one of the built-in fragments:

    - objectParts: Full object fields (uid, name, class, domain, category, type,
      project, alias, description, xid, geometry, item)
    - objectRefParts: Minimal object fields (uid, name, class, domain, category,
      type, project)
    - objectDescParts: Object fields with description (uid, name, class, domain,
      category, type, description, project)
    - connectionParts: Full connections with objectParts for subject/object
    - connectionRefParts: Minimal connections with objectRefParts for
      subject/object
    - connectionDescParts: Connections with objectDescParts for subject/object

    Custom fragments with at least uid, name, and class are also supported.

    When querying with GraphQL, the projects argument must be a list of project
    UIDs. The UID for a project can be found in the `uid` property of a project
    object.

    Args:
        query: a GraphQL query string
        return_errors: if True, will not print or raise on errors, but return
            them in the GraphResponse object instead. The user can then call
            `error_summary()` on the response to print a summary of the errors
            or access the "errors" key directly. Default is False.

    Returns:
        a GraphResponse object that can access the raw response, a list of
        objects/connections, or a networkx graph.

    Examples:
        >>> # Using full fragments
        >>> res = graph('''
        {
            graph(projects: ["abc123"], search: "sentinel") {
                ...objectParts
                connections(predicate: "can-observe") {
                    ...connectionParts
                }
            }
        }
        ''')

        >>> # Using minimal ref fragments for better performance
        >>> res = graph('''
        {
            graph(projects: ["abc123"], search: "sentinel") {
                ...objectRefParts
                connections(predicate: "can-observe") {
                    ...connectionRefParts
                }
            }
        }
        ''')
    """
    if "graph(" not in query:
        raise ValueError("All calls to this function must include a request to the `graph` query")

    # Define fragment dependencies for automatic inclusion
    FRAGMENT_DEPENDENCIES = {
        "connectionParts": "objectParts",
        "connectionRefParts": "objectRefParts",
    }

    # Track which fragments need to be added and set compatibility flags
    fragments_to_add = set()

    # Find fragments used in query but not already defined
    for key in FRAGMENTS.keys():
        if f"...{key}" in query and f"fragment {key} on" not in query:
            fragments_to_add.add(key)

            # Add any dependencies this fragment requires
            if key in FRAGMENT_DEPENDENCIES:
                dependency = FRAGMENT_DEPENDENCIES[key]
                if f"fragment {dependency} on" not in query:
                    fragments_to_add.add(dependency)

    # Append fragment definitions to query
    if fragments_to_add:
        query += "\n"
        for key in fragments_to_add:
            query += f"\n{FRAGMENTS[key]}"

    res = raise_on_error(graphql_client.post("query", json=dict(query=query)))
    if "errors" in res.json() and not return_errors:
        # Only print out the errors table if we are not returning them to the user
        errors = res.json()["errors"]
        table = _get_error_table(errors)
        console = Console()
        console.print(table)

        raise ValueError("Error querying Entanglement GraphQL API. See table for details.")

    data_resp = res.json().get("data", {})
    graph_data = None
    if data_resp:
        graph_data = data_resp.get("graph", [])

    errors_resp = res.json().get("errors", [])
    return GraphResponse(
        **(
            {
                "graph": graph_data,
                "errors": errors_resp,
            }
        ),
    )


def _parse_connections(root: dict) -> List[Connection]:
    connections = []
    objects = {}

    conn_dicts = root.get("connections", [])
    for conn_dict in conn_dicts:
        sub = conn_dict["subject"]
        pred = conn_dict["predicate"]
        obj = conn_dict["object"]
        attrs = conn_dict["attributes"]

        objects[sub["uid"]] = sub
        objects[obj["uid"]] = obj
        if "connections" in sub:
            objs, conns = _parse_connections(sub)
            connections.extend(conns)
            objects.update(objs)
        if "connections" in obj:
            objs, conns = _parse_connections(obj)
            connections.extend(conns)
            objects.update(objs)

        if sub["uid"] == root["uid"]:
            sub = dict(**root)
            sub.pop("connections", None)
        if obj["uid"] == root["uid"]:
            obj = dict(**root)
            obj.pop("connections", None)

        conn = Connection(
            subject=_conn_object_parts(sub),
            predicate=Predicate(name=pred, **_conn_attrs_to_dict(attrs)),
            object=_conn_object_parts(obj),
        )

        connections.append(conn)

    return objects, connections


def _conn_attrs_to_dict(attrs: list) -> dict:
    attrs_dict = {}
    edge_attributes = {}
    for attr in attrs:
        if attr["key"] in ("domain", "category", "type"):
            attrs_dict[attr["key"]] = attr["value"]
        else:
            edge_attributes[attr["key"]] = attr["value"]
    attrs_dict["edge_attributes"] = edge_attributes
    return attrs_dict


def _conn_object_parts(o: dict) -> dict:
    """Extract minimal object fields required for creating an Object from connection data.

    Requires: uid, name, class
    Optional: domain, category, type, and any other fields present
    """
    # Required fields
    obj = dict(
        uid=o["uid"],
        name=o["name"],
        object_class=o["class"],
    )

    # Optional taxonomic fields
    domain = o.get("domain")
    category = o.get("category")
    type_ = o.get("type")

    if domain is not None:
        obj["domain"] = domain
    if category is not None:
        obj["category"] = category
    if type_ is not None:
        obj["type"] = type_

    # Include any other fields that might be present (like project, alias, description, etc.)
    for key in o:
        if key not in ("uid", "name", "class", "domain", "category", "type", "connections"):
            obj[key] = o[key]

    return obj
