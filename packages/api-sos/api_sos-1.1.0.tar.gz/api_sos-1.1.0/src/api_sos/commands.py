import os
import subprocess
import sys
import tempfile

import click
import ruamel.yaml
from jinja2 import Template
from loguru import logger
from pydantic_core import to_jsonable_python

import api_sos.api_sos as sos
from api_sos.api_sos import CheckResult
from api_sos.entity import APICheck, Input
from api_sos.generate import file_add_checks, openapi_to_checks
from api_sos.utils import auto_reader

VERSION = "1.0.0"


def setup_logger(verbose: bool = False) -> None:
    """Setup logger with appropriate level based on verbose flag."""
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if verbose else "INFO", backtrace=True, diagnose=True)


async def interactive_edit_check(input_file: str, check: APICheck, result: CheckResult, index: int) -> None:
    """
    交互式编辑指定的检查项

    :param input_file: 输入文件路径
    :param check: 需要编辑的检查项
    :param result: 检查结果
    :param index: 检查项在列表中的索引
    """
    if not result.diffs or not result.response:
        return

    editor = os.environ.get("EDITOR", "vim")

    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as temp_file:
        current_assert = check.assert_

        if current_assert is None:
            from api_sos.entity import AssertResponse

            current_assert = AssertResponse(
                headers=None, http_status=None, http_version=None, encoding="utf-8", content=None
            )

        yaml_content = {
            "assert": to_jsonable_python(current_assert),
            "actual": to_jsonable_python(result.response),
            "name": check.name,
        }

        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        yaml.dump(yaml_content, temp_file)
        temp_file_path = temp_file.name

        try:
            logger.info(f"正在打开编辑器编辑检查项 '{check.name}'...")
            subprocess.run([editor, temp_file_path], check=True)

            edited_content = auto_reader(temp_file_path)
            if "actual" in edited_content:
                del edited_content["actual"]

            if "name" in edited_content:
                del edited_content["name"]

            if "assert" in edited_content:
                check.assert_ = edited_content["assert"]

                input_data = auto_reader(input_file)

                if index < len(input_data["checks"]):
                    input_data["checks"][index]["assert"] = edited_content["assert"]

                    with open(input_file, "w") as f:
                        yaml = ruamel.yaml.YAML()
                        yaml.preserve_quotes = True
                        yaml.dump(input_data, f)

                    logger.info(f"已更新检查项 '{check.name}' 的断言")
                else:
                    logger.error(f"无法更新检查项，索引 {index} 超出范围")
        except Exception as e:
            logger.error(f"编辑检查项时出错: {e}")
        finally:
            os.unlink(temp_file_path)


def has_failures(results: list[CheckResult | Exception]) -> bool:
    return any(
        isinstance(result, Exception) or (isinstance(result, CheckResult) and (result.error or result.diffs))
        for result in results
    )


async def run_checks(
    file_input: str,
    concurrent: int = 1,
    interactive: bool = False,
    endpoint: str | None = None,
    variables: str | None = None,
    *,
    verbose: bool = False,
) -> list[CheckResult | Exception]:
    setup_logger(verbose)
    assert isinstance(interactive, bool), "interactive_edit must be a boolean, please input True or False"

    variables_dict = None
    if variables:
        logger.debug(f"loading variables from {variables}")
        variables_dict = auto_reader(variables)

    logger.debug(f"loading input {file_input}")
    input_ = Input.load(file_input)

    assert input_.version == VERSION

    input_.endpoint = endpoint or input_.endpoint

    logger.info(f"Running the input {file_input} with {concurrent} concurrent processes")

    results = await sos.run(input_, concurrent, variables_dict)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(str(result))
        elif isinstance(result, CheckResult):
            if result.error:
                logger.error(str(result))
            elif result.diffs:
                logger.warning(str(result))
                if interactive and result.diffs:
                    await interactive_edit_check(file_input, input_.checks[i], result, i)
            else:
                logger.success(str(result))

    return results


async def generate_checks(
    schema: str,
    output: str,
    *,
    key: str | None = None,
    endpoint: str | None = None,
    concurrent: int = 1,
    headers: str | None = None,
    headers_variables: str | None = None,
    no_example: bool = False,
    no_record: bool = False,
    verbose: bool = False,
) -> list[APICheck]:
    setup_logger(verbose)
    logger.debug(f"generating input {schema}")
    checks = openapi_to_checks(schema, key=key, from_example=not no_example)

    headers_dict = None
    if headers:
        logger.debug(f"loading headers from {headers}")
        headers_dict = auto_reader(headers)
        if headers_variables:
            logger.debug(f"loading headers variables from {headers_variables}")
            variables_dict = auto_reader(headers_variables)
            rendered_headers = {}
            for key, value in headers_dict.items():
                if isinstance(value, str) and "{{" in value and "}}" in value:
                    template = Template(value)
                    rendered_headers[key] = template.render(**variables_dict)
                else:
                    rendered_headers[key] = value
            headers_dict = rendered_headers

    if not no_record:
        if endpoint is None:
            raise click.UsageError(
                "\nEndpoint is required when recording responses (--no-record is not set).\n"
                "Please either:\n"
                "1. Provide an endpoint using --endpoint option\n"
                "   Example: api-sos generate openapi.yaml output.yaml --endpoint http://localhost:8000\n"
                "2. Or use --no-record to skip response recording\n"
                "   Example: api-sos generate openapi.yaml output.yaml --no-record"
            )

        logger.info("Running generated checks to record responses...")
        input_ = Input(version=VERSION, endpoint=endpoint, checks=checks)

        if headers_dict:
            for check in checks:
                check.headers = headers_dict

        results = await sos.run(input_, concurrent=concurrent)

        for check, result in zip(checks, results):
            if not isinstance(result, Exception) and result.response:
                check.assert_ = result.response

    if headers:
        original_headers = auto_reader(headers)
        for check in checks:
            check.headers = original_headers

    file_add_checks(output, checks)
    return checks
