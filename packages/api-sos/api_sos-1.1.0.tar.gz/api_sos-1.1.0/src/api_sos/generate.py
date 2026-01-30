import json
import random
from pathlib import Path
from typing import Any

import ruamel.yaml
from faker import Faker
from prance import ResolvingParser
from pydantic_core import to_jsonable_python

from api_sos.entity import APICheck, Parameter, Payload
from api_sos.utils import gen_string

yaml = ruamel.yaml.YAML(typ="safe")
yaml.preserve_quotes = True


def _normalize_path(path: str) -> str:
    return path.strip("/")


def _resolve_type(value: dict, from_example: bool) -> list[Any]:
    fake = Faker()
    type_ = value.get("type", "object")
    if "default" in value:
        return [value["default"]]
    if "example" in value:
        return [value["example"]["value"]]
    if "examples" in value:
        return [v["value"] for v in value["examples"]]
    match type_:
        case "object":
            if "oneOf" in value:
                return [_resolve_type(one_of, from_example=from_example) for one_of in value["oneOf"]]
            if "allOf" in value or "anyOf" in value:
                if "allOf" in value:
                    resolved = [_resolve_type(all_of, from_example=from_example) for all_of in value["allOf"]]
                else:
                    resolved = [_resolve_type(any_of, from_example=from_example) for any_of in value["anyOf"]]

                payloads = [{}]
                for each_all_of in resolved:
                    for i, possible in enumerate(each_all_of):
                        new_merged = []
                        for previous in payloads:
                            if isinstance(previous, dict) and isinstance(possible, dict):
                                copy_previous = previous.copy()
                                copy_previous.update(possible)
                                new_merged.append(copy_previous)

                        payloads = new_merged
            else:
                payloads = [{}]
                for key, value in value["properties"].items():
                    values = _resolve_type(value, from_example=from_example)
                    for i, possible in enumerate(values):
                        new_payloads = []
                        for payload in payloads:
                            new_payload = payload.copy()
                            new_payload[key] = possible
                            new_payloads.append(new_payload)
                        payloads = new_payloads

            return payloads
        case "array":
            payload = []
            array_type = value.get("items", {"type": "string"})["type"]
            if "minItems" in value:
                min_items = value["minItems"]
            else:
                min_items = random.randint(0, 5)
            if "maxItems" in value:
                max_items = value["maxItems"]
            else:
                max_items = random.randint(min_items, min_items + 5)
            for _ in range(random.randint(min_items, max_items)):
                resolved = _resolve_type({"type": array_type}, from_example=from_example)
                for i, res in enumerate(resolved):
                    if i == 0:
                        payload.append([res])
                    else:
                        payload[i].append(res)

            return payload
        case "string":
            min_length = value.get("minLength", random.randint(5, 10))
            max_length = value.get("maxLength", random.randint(min_length, min_length + 5))
            if "enum" not in value:
                return [gen_string(random.randint(min_length, max_length))]
            return [random.choice(value["enum"])]
        case "integer":
            return [fake.random_int()]
        case "number":
            return [fake.random_number()]
        case "boolean":
            return [fake.boolean()]
        case "null":
            return [None]
        case _:
            raise Exception(f"Type {type_} is not supported yet")


def _openapi_to_checks(path: str, value: dict, from_example: bool = True) -> list[APICheck]:
    res = []
    for method, method_value in value.items():
        name = f"{path} {method}"
        if "operationId" in method_value:
            name = method_value["operationId"]
        elif "summary" in method_value:
            name = method_value["summary"]
        elif "description" in method_value:
            name = method_value["description"]

        if "requestBody" in method_value:
            request_content = method_value["requestBody"]["content"]
            for content_type, content_value in request_content.items():
                if "examples" in content_value:
                    for example_name, example in content_value["examples"].items():
                        res.append(
                            APICheck(
                                name=f"{name} - {content_type} - {example_name}",
                                pathname=path,
                                method=method,
                                payload=Payload(value=example["value"]),
                                headers={"Content-Type": content_type},
                                **{"assert_": None},
                            )
                        )
                    continue
                schema = content_value["schema"]
                payloads = _resolve_type(schema, from_example=from_example)
                for payload in payloads:
                    res.append(
                        APICheck(
                            name=f"{name} - {content_type}",
                            pathname=path,
                            method=method,
                            payload=Payload(value=payload),
                            headers={"Content-Type": content_type},
                            **{"assert_": None},
                        )
                    )
        elif "parameters" in method_value:
            parameters = method_value["parameters"]
            res_parameters: list[list[Parameter]] = []
            for i, parameter in enumerate(parameters):
                resolved = _resolve_type(parameter["schema"], from_example=from_example)
                if "examples" in parameter:
                    for example_name, example in parameter["examples"].items():
                        res.append(
                            APICheck(
                                name=f"{name} - {example_name}",
                                pathname=path,
                                method=method,
                                parameters=[
                                    Parameter(name=parameter["name"], in_=parameter["in"], value=example["value"])  # type: ignore
                                ],
                                **{"assert_": None},
                            )
                        )
                        continue
                for resolved_value in resolved:
                    parameter_entity = Parameter(  # type: ignore
                        name=parameter["name"],
                        in_=parameter["in"],  # type: ignore
                        value=resolved_value,
                    )

                    if i == 0:
                        res_parameters.append([parameter_entity])
                    else:
                        new_parameters = []
                        for previous in res_parameters:
                            new_parameters.append(previous + [parameter_entity])
                        res_parameters = new_parameters

            for parameter in res_parameters:
                res.append(
                    APICheck(
                        name=name,
                        pathname=path,
                        method=method,
                        parameters=parameter,
                        **{"assert_": None},
                    )
                )

    return res


def openapi_to_checks(
    schema_path: str, path: str | None = None, key: str | None = None, from_example: bool = True
) -> list[APICheck]:
    parser = ResolvingParser(schema_path)
    assert parser.specification, "The schema is empty"
    assert not (key and path), "You can only use key or path, not both"
    paths = parser.specification["paths"]
    res = []
    for path_in_schema, value_in_schema in paths.items():
        for _, method_value in value_in_schema.items():
            # only use the selected path
            if path and _normalize_path(path) == _normalize_path(path_in_schema):
                res.extend(_openapi_to_checks(path_in_schema, value_in_schema, from_example))
            # only use the selected key
            elif key and "operationId" in method_value and key == method_value["operationId"]:
                res.extend(_openapi_to_checks(path_in_schema, value_in_schema, from_example))
            # key and path not provided, use all
            elif not path and not key:
                res.extend(_openapi_to_checks(path_in_schema, value_in_schema, from_example))
    return res


def file_add_checks(path: str, checks: list[APICheck]) -> None:
    schema_file_ = Path(path)
    schema = None
    if schema_file_.exists():
        match schema_file_.suffix.lower():
            case ".json":
                schema = json.loads(schema_file_.read_text())
            case ".yaml" | ".yml":
                schema = yaml.load(schema_file_)
            case _:
                raise Exception(f"File {path} is not a valid format or not supported yet.")
    schema = schema or {"checks": [], "version": "1.0.0"}

    schema["checks"].extend([to_jsonable_python(check) for check in checks])
    with open(path, "w") as f:
        match schema_file_.suffix.lower():
            case ".json":
                json.dump(schema, f, indent=4)
            case ".yaml" | ".yml":
                yaml.dump(schema, f)
            case _:
                raise Exception(f"File {path} is not a valid format or not supported yet.")
