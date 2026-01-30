import click
from loguru import logger

from api_sos.commands import generate_checks, has_failures, run_checks
from api_sos.utils import coro


@click.group()
def api_sos():
    """API SOS - API testing tool"""
    pass


@click.command()
@click.option("-v", "--verbose", is_flag=True, show_default=True, default=False, help="Enable debug mode")
@click.option("--concurrent", default=1, help="Run the script concurrently")
@click.option(
    "-i",
    "--interactive",
    default=False,
    is_flag=True,
    show_default=True,
    help="Run the script, if the result is different to aspected, interactively edit the input file",
)
@click.option(
    "--endpoint",
    default=None,
    help="The endpoint to be used, if not provided, the endpoint given in input will be used",
)
@click.option(
    "--variables",
    default=None,
    help="The file to be used as variables, should be a json or yaml. if provided, all value will replaced in input",
)
@click.argument("file_input")
@coro
async def run(
    verbose: bool, file_input: str, concurrent: int, interactive: bool, endpoint: str | None, variables: str | None
):
    results = await run_checks(
        file_input,
        concurrent=concurrent,
        interactive=interactive,
        endpoint=endpoint,
        variables=variables,
        verbose=verbose,
    )

    if has_failures(results):
        raise SystemExit(1)
    logger.success("All tests passed!")


@click.command()
@click.option("-v", "--verbose", is_flag=True, show_default=True, default=False, help="Enable debug mode")
@click.argument("schema")
@click.option(
    "--key", default=None, help="The key to be used in the schema, if given, only the key in schema will be generated"
)
@click.argument("output")
@click.option(
    "--endpoint",
    default=None,
    help="The endpoint to be used for recording responses, required when --no-record is not set",
)
@click.option(
    "--concurrent",
    default=1,
    help="Number of concurrent requests when recording responses",
)
@click.option(
    "--headers",
    default=None,
    help="Headers to be used for requests, should be a json or yaml file",
)
@click.option(
    "--headers-variables",
    default=None,
    help="Variables to be used in headers template, should be a json or yaml file",
)
@click.option(
    "--no-record/-nr",
    is_flag=True,
    show_default=True,
    default=False,
    help="If try to request the endpoint and record the response as assert",
)
@click.option(
    "--no-example/-ne",
    is_flag=True,
    show_default=True,
    default=False,
    help="If try to generate checks from example in schema",
)
@coro
async def generate(
    verbose: bool,
    schema: str,
    output: str,
    key: str | None = None,
    endpoint: str | None = None,
    concurrent: int = 1,
    headers: str | None = None,
    headers_variables: str | None = None,
    no_example: bool = False,
    no_record: bool = False,
):
    await generate_checks(
        schema,
        output,
        key=key,
        endpoint=endpoint,
        concurrent=concurrent,
        headers=headers,
        headers_variables=headers_variables,
        no_example=no_example,
        no_record=no_record,
        verbose=verbose,
    )


api_sos.add_command(run)
api_sos.add_command(generate)

if __name__ == "__main__":
    api_sos()
