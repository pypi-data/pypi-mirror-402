import asyncio
import json
import re
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Dict, Union

import aiohttp
from jinja2 import Environment, StrictUndefined
from loguru import logger

from api_sos.entity import (
    APICheck,
    AssertResponse,
    BasicAuth,
    DiffResult,
    HTTPRequestTimeout,
    HTTPVersion,
    Input,
    Parameter,
)

# 创建全局 Jinja2 环境
_env = Environment(keep_trailing_newline=True, autoescape=False, undefined=StrictUndefined)

# 类型映射字典
_type_map = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "None": type(None),
}
# 添加自定义过滤器
_env.filters.update(
    {
        "matches": lambda value, pattern: bool(re.match(pattern, str(value))),
        "contains": lambda value, substr: substr in str(value),
        "gt": lambda value, other: float(value) > float(other),
        "lt": lambda value, other: float(value) < float(other),
        "gte": lambda value, other: float(value) >= float(other),
        "lte": lambda value, other: float(value) <= float(other),
        "ne": lambda value, other: value != other,
        "is_numeric": lambda value: str(value).replace(".", "").isdigit(),
        "is_date": lambda value: bool(re.match(r"^\d{4}-\d{2}-\d{2}$", str(value))),
        "is_email": lambda value: bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", str(value))),
        "length": lambda value: len(value),
        "starts_with": lambda value, prefix: str(value).startswith(prefix),
        "ends_with": lambda value, suffix: str(value).endswith(suffix),
        "in_range": lambda value, min_val, max_val: float(min_val) <= float(value) <= float(max_val),
        "is_empty": lambda value: not value or len(str(value).strip()) == 0,
        "is_type": lambda value, expected_type: isinstance(value, _type_map.get(expected_type, object)),
        "pass": lambda value: True,
    }
)


def evaluate_field(field_value: Any, actual_value: Any, context: Dict[str, Any]) -> bool:
    """
    评估字段值：
    - 如果包含 {{ }}，则作为 Jinja2 模板处理
    - 否则作为普通字符串比较
    """
    if isinstance(field_value, str):
        # 检查是否是模板表达式
        if "{{" in field_value and "}}" in field_value:
            try:
                # 创建模板
                template = _env.from_string(field_value)
                # 渲染模板
                rendered_value = template.render(actual=actual_value, **context)

                # 如果渲染后的值是布尔值，直接返回
                if rendered_value in ("True", "False"):
                    return rendered_value == "True"
                # 否则比较值
                return rendered_value == actual_value
            except Exception as e:
                logger.warning(f"Failed to render template: {e}")
                # 如果模板渲染失败，尝试直接比较
                return field_value == str(actual_value)
        # 普通字符串直接比较
        return field_value == str(actual_value)
    # 非字符串直接比较
    return field_value == actual_value


@dataclass
class CheckResult:
    """检查结果"""

    diffs: list[DiffResult] = field(default_factory=list)
    error: Exception | None = None
    check_name: str = ""
    path: str = ""
    method: str = ""
    status_code: int | None = None
    request_body: Any = None
    response_body: Any = None
    response: AssertResponse | None = None

    def __str__(self) -> str:
        """格式化输出结果"""
        if self.error:
            return f"❌ {self.check_name} ({self.method} {self.path}) failed: {self.error}"

        if not self.diffs:
            return f"✅ {self.check_name} ({self.method} {self.path}) passed"

        diffs_str = "\n".join(f"  - {diff}" for diff in self.diffs)
        return f"❌ {self.check_name} ({self.method} {self.path}) has differences:\n{diffs_str}"


def _auth_to_aiohttp(auth: BasicAuth | None) -> aiohttp.BasicAuth | None:
    if not auth:
        return auth
    return aiohttp.BasicAuth(login=auth.login, password=auth.password, encoding=auth.encoding)


def _timeout_to_aiohttp(timeout: HTTPRequestTimeout | None) -> aiohttp.ClientTimeout | None:
    if not timeout:
        return timeout
    return aiohttp.ClientTimeout(
        total=timeout.total,
        connect=timeout.connect,
        sock_read=timeout.sock_read,
        sock_connect=timeout.sock_connect,
        ceil_threshold=timeout.ceil_threshold,
    )


def _http_version_to_entity(version: aiohttp.HttpVersion | None) -> HTTPVersion | None:
    if not version:
        return version
    return HTTPVersion(major=version.major, minor=version.minor)


def diff_values(actual: Any, should: Any, field_name: str, context: Dict[str, Any] | None = None) -> list[DiffResult]:
    """比较两个值并返回差异"""
    results: list[DiffResult] = []
    context = context or {}

    if is_dataclass(actual) and is_dataclass(should):
        for field in fields(type(actual)):  # type: ignore
            actual_value = getattr(actual, field.name)
            should_value = getattr(should, field.name)
            diffs = diff_values(actual_value, should_value, f"{field_name}.{field.name}", context)
            results.extend(diffs)
    elif isinstance(actual, dict) and isinstance(should, dict):
        # 检查所有键
        all_keys = set(actual.keys()) | set(should.keys())
        for key in all_keys:
            actual_value = actual.get(key)
            should_value = should.get(key)
            diffs = diff_values(actual_value, should_value, f"{field_name}.{key}", context)
            results.extend(diffs)
    elif isinstance(actual, list) and isinstance(should, list):
        for i, (actual_value, should_value) in enumerate(zip(actual, should)):
            diffs = diff_values(actual_value, should_value, f"{field_name}[{i}]", context)
            results.extend(diffs)
    else:
        if not evaluate_field(should, actual, context):
            results.append(DiffResult(field=field_name, actual_value=actual, assert_value=should))

    return results


def diff_response(
    actual: AssertResponse, should: AssertResponse, context: Dict[str, Any] | None = None
) -> list[DiffResult]:
    """
    比较实际响应和预期响应
    :param actual: 实际响应
    :param should: 预期响应
    :param context: 模板上下文
    :return: 差异列表
    """
    results: list[DiffResult] = []
    context = context or {}

    for each_field in fields(type(actual)):
        field_name = each_field.name
        actual_value = getattr(actual, field_name)
        should_value = getattr(should, field_name)
        if should_value is None:
            continue
        results.extend(diff_values(actual_value, should_value, field_name, context))

    return results


def process_params(path: str, parameters: list[Parameter] | None) -> tuple[str, dict[str, str | int | float] | None]:
    """处理请求参数，将布尔值转换为字符串的 'true' 或 'false'"""
    if not parameters:
        return path, None
    params = {}
    for p in parameters:
        if p.in_ == "path":
            path = path.replace(f"{{{p.name}}}", str(p.value))
        else:
            params[p.name] = str(p.value).lower() if isinstance(p.value, bool) else p.value
    return path, params


async def run(
    input_: Input, concurrent: int = 1, variables: dict[str, Any] | None = None
) -> list[Union[CheckResult, Exception]]:
    """
    运行 API 检查
    :param input_: 输入配置
    :param concurrent: 并发数
    :param variables: 变量
    :return: 检查结果列表
    """
    async with aiohttp.ClientSession() as session:
        # 创建信号量限制并发
        sema = asyncio.Semaphore(concurrent)

        async def run_with_sema(check: APICheck) -> list[Union[CheckResult, Exception]]:
            async with sema:
                return await _run_check(session, input_.endpoint, check, variables)

        tasks = [asyncio.create_task(run_with_sema(check)) for check in input_.checks]

        results = await asyncio.gather(*tasks)
        return [result for sublist in results for result in sublist]


def replace_variables[T: str | bytes | dict[str, Any] | list[Any] | None](
    content: T, variables: dict[str, Any] | None = None
) -> T:
    """替换变量"""
    if not content or not variables:
        return content

    env = Environment()

    if isinstance(content, str):
        template = env.from_string(content)
        return template.render(**variables)  # type: ignore
    elif isinstance(content, dict):
        return {k: replace_variables(v, variables) for k, v in content.items()}  # type: ignore
    elif isinstance(content, list):
        return [replace_variables(item, variables) for item in content]  # type: ignore
    return content


async def _run_check(
    session: aiohttp.ClientSession,
    endpoint: str | None,
    check: APICheck,
    variables: dict[str, Any] | None = None,
) -> list[Union[CheckResult, Exception]]:
    """
    运行单个检查
    :param session: aiohttp 会话
    :param endpoint: 基础端点
    :param check: 检查配置
    :param variables: 变量
    :return: 差异列表和错误
    """
    if endpoint:
        url = f"{endpoint.rstrip('/')}/{check.pathname.lstrip('/')}"
    else:
        url = check.pathname
    headers = check.headers or {}
    url, params = process_params(url, check.parameters)
    payload = check.payload.value if check.payload else None
    if variables:
        url = replace_variables(url, variables)
        headers = replace_variables(headers, variables)
        params = replace_variables(params, variables)
        payload = replace_variables(payload, variables)

    try:
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request Headers: {headers}")
        logger.debug(f"Request Params: {params}")
        logger.debug(f"Request Payload: {payload}")
        async with session.request(
            method=check.method,
            url=url,
            headers=headers,
            params=params,
            json=payload if isinstance(payload, dict) else None,
            data=payload if isinstance(payload, bytes) else None,
            auth=_auth_to_aiohttp(check.proxy_auth),
            proxy=check.proxy,
            timeout=_timeout_to_aiohttp(check.timeout),
        ) as response:
            response_body = await response.text()
            response_json = None

            # 尝试解析 JSON 响应
            try:
                if response.headers.get("content-type", "").startswith("application/json"):
                    response_json = json.loads(response_body)
                    logger.debug(f"Response JSON: {response_json}")
                else:
                    logger.debug(f"Response is not JSON: {response_body[:200]}...")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                logger.debug(f"Raw response: {response_body[:200]}...")
            except Exception as e:
                logger.error(f"Unexpected error while parsing response: {e}")
                logger.debug(f"Raw response: {response_body[:200]}...")

            actual = AssertResponse(
                headers=dict(response.headers),
                http_status=response.status,
                http_version=_http_version_to_entity(response.version),
                encoding=response.get_encoding(),
                content=response_json or response_body,
            )

            if check.assert_:
                diffs = diff_response(actual, check.assert_, variables)
                if diffs:
                    return [
                        CheckResult(
                            diffs=diffs,
                            check_name=check.name,
                            path=check.pathname,
                            method=check.method,
                            status_code=response.status,
                            request_body=payload,
                            response_body=response_json or response_body,
                            response=actual,
                        )
                    ]
            return [
                CheckResult(
                    check_name=check.name,
                    path=check.pathname,
                    method=check.method,
                    status_code=response.status,
                    request_body=payload,
                    response_body=response_json or response_body,
                    response=actual,
                )
            ]

    except aiohttp.ClientError as e:
        error_msg = (
            f"{'='*50}\n"
            f"Request Failed: {e}\n"
            f"{'-'*30} Request Details {'-'*30}\n"
            f"URL: {url}\n"
            f"Method: {check.method}\n"
            f"Headers: {headers}\n"
            f"Query Params: {params}\n"
            f"Request Body: {payload}\n"
            f"{'='*50}"
        )
        logger.error(error_msg)
        return [
            CheckResult(
                error=Exception(error_msg),
                check_name=check.name,
                path=check.pathname,
                method=check.method,
                request_body=payload,
            )
        ]
    except asyncio.TimeoutError as e:
        error_msg = (
            f"{'='*50}\n"
            f"Request Timeout: {e}\n"
            f"{'-'*30} Request Details {'-'*30}\n"
            f"URL: {url}\n"
            f"Method: {check.method}\n"
            f"Timeout Settings: {check.timeout}\n"
            f"{'='*50}"
        )
        logger.error(error_msg)
        return [
            CheckResult(
                error=Exception(error_msg),
                check_name=check.name,
                path=check.pathname,
                method=check.method,
                request_body=payload,
            )
        ]
    except json.JSONDecodeError as e:
        error_msg = (
            f"{'='*50}\n"
            f"JSON Parse Error: {e}\n"
            f"{'-'*30} Request Details {'-'*30}\n"
            f"URL: {url}\n"
            f"Method: {check.method}\n"
            f"Response Preview: {str(e.doc)[:200] if hasattr(e, 'doc') else 'Not available'}\n"
            f"{'='*50}"
        )
        logger.error(error_msg)
        return [
            CheckResult(
                error=Exception(error_msg),
                check_name=check.name,
                path=check.pathname,
                method=check.method,
                request_body=payload,
            )
        ]
    except Exception as e:
        error_msg = (
            f"{'='*50}\n"
            f"Unexpected Error: {e}\n"
            f"{'-'*30} Request Details {'-'*30}\n"
            f"URL: {url}\n"
            f"Method: {check.method}\n"
            f"Error Type: {type(e).__name__}\n"
            f"Error Details: {str(e)}\n"
            f"{'-'*30} Debug Information {'-'*30}\n"
            f"Headers: {headers}\n"
            f"Query Params: {params}\n"
            f"Request Body: {payload}\n"
            f"{'='*50}"
        )
        logger.error(error_msg)
        return [
            CheckResult(
                error=Exception(error_msg),
                check_name=check.name,
                path=check.pathname,
                method=check.method,
                request_body=payload,
            )
        ]
