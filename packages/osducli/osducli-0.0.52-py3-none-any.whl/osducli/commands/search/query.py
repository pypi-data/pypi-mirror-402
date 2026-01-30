#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Search service query command"""

import collections

import click
from jmespath import Options
from jmespath import compile as compile_jmespath
from osdu_api.model.search.query_request import QueryRequest

from osducli.click_cli import CustomClickCommand, State, command_with_output
from osducli.cliclient import CliOsduClient, handle_cli_exceptions

QUERY_JMESPATH_EXPRESSION = compile_jmespath("results[*].{Id:id,Kind:kind,CreateTime:createTime}")
AGGREGATE_JMESPATH_EXPRESSION = compile_jmespath("sort_by(aggregations,&key)[*].{Key:key,Count:count}")

# click entry point
@click.command(cls=CustomClickCommand)
@click.option("-k", "--kind", "kind", help="kind to search for")
@click.option("-id", "--id", "_id", help="id to search for")
@click.option("-q", "--query", "_query", help="custom search query")
@click.option(
    "-l",
    "--limit",
    "limit",
    default=10,
    show_default=True,
    help="maximum number of records to return.",
)
@click.option("-a", "--aggregate", "_aggr", help="Aggregate by element", required=False)
@handle_cli_exceptions
@command_with_output(None)
def _click_command(state: State, kind: str, _id: str, _query: str, limit: int, _aggr: str):
    """Search using more advanced query terms"""
    return query(state, kind, _id, _query, limit, _aggr)


def query(state: State, kind: str, identifier: str, custom_query: str, limit: int, aggregate: str = None):
    """Query search service

    Args:
        state (State): Global state
        kind (str): kind to search for
        identifier (str): id to search for
        custom_query (str): custom search query
        limit (int): maximum number of records to return.
        aggregate (str): aggregate by element
    """
    client = CliOsduClient(state.config)
    search_client = client.get_search_client()

    if identifier is not None and custom_query is not None:
        raise ValueError("You can't specify both identifier and query")

    if kind is None:
        kind = "*:*:*:*"

    query_val = f'id:("{identifier}")' if identifier is not None else custom_query
    request_data = QueryRequest(kind=kind, query=query_val, limit=limit, aggregate_by=aggregate)

    response = search_client.query_records(query_request=request_data)
    client.check_status_code(response)
    response_data = response.json()

    if aggregate is not None:
        return AGGREGATE_JMESPATH_EXPRESSION.search(response_data, Options(collections.OrderedDict))

    return QUERY_JMESPATH_EXPRESSION.search(response_data, Options(collections.OrderedDict))
