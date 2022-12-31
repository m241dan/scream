import re
import unittest
import yaml


class NoTypesError(Exception):
    def __init__(self, raw_data: list[dict], msg: str = "Raw data contains no 'is_a: types' map entry: "):
        self.raw_data = raw_data
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f'{self.msg} {self.raw_data}'


class NoSchemaError(Exception):
    pass


class SchemaFormatError(Exception):
    pass


class RedundantTypeError(Exception):
    pass


def parse_types(raw_data: list[dict]) -> dict:
    is_a_filtered_data = [data for data in raw_data if 'is_a' in data.keys() and data['is_a'] == 'types']

    if len(is_a_filtered_data) == 0:
        raise NoTypesError(raw_data)

    type_schemas = [data['schema'] for data in is_a_filtered_data if 'schema' in data.keys()]

    if len(type_schemas) == 0:
        raise NoSchemaError

    for schema in type_schemas:
        if not isinstance(schema, dict):
            raise SchemaFormatError

        if len(schema) == 0:
            raise SchemaFormatError

        for key in schema.keys():
            if not isinstance(key, str):
                raise SchemaFormatError

        for entry in schema.values():
            if not isinstance(entry, dict):
                raise SchemaFormatError

            for inner in entry.values():
                if not isinstance(inner, str) and not isinstance(inner, dict):
                    raise SchemaFormatError

                if isinstance(inner, dict):
                    if 'generator' not in inner:
                        raise SchemaFormatError
                    if len(inner) != 1:
                        raise SchemaFormatError

    type_mappings = {}
    for schema in type_schemas:
        for key, type_map in schema.items():
            if key in type_mappings:
                raise RedundantTypeError

            args = [len(re.findall(r"{_[1-9]}", pattern)) for pattern in type_map.values()]

            type_mappings[key] = type_map | {"maximum_possible_args": max(args)}

    return type_mappings


class TestingLoadParse(unittest.TestCase):
    test_data: list[dict] = []

    def test_that_parse_types_throws_a_NoTypesError_when_no_types_are_present_in_the_raw_data(self) -> None:
        self.assertRaises(NoTypesError, parse_types, [{"is_a": "model"}])

    def test_that_parse_types_throws_a_NoSchemaError_when_there_a_types_entry_that_is_missing_a_schema_definition(self) -> None:
        self.assertRaises(NoSchemaError, parse_types, [{"is_a": "types"}])

    def test_that_parse_types_throws_a_SchemaFormatError_when_the_given_schema_does_not_match_the_format_for_types(self) -> None:
        self.assertRaises(SchemaFormatError, parse_types, [{"is_a": "types", "schema": 1}])  # schema should be a map
        self.assertRaises(SchemaFormatError, parse_types, [{"is_a": "types", "schema": {}}])  # schema should have at least one entry
        self.assertRaises(SchemaFormatError, parse_types, [{"is_a": "types", "schema": {2: "cpp"}}])  # schema keys should be strings
        self.assertRaises(SchemaFormatError, parse_types, [{"is_a": "types", "schema": {"int": 3}}])  # schema entries should be maps
        self.assertRaises(SchemaFormatError, parse_types, [{"is_a": "types", "schema": {"int": {"cpp": 4}}}])  # schema entry maps should be strings or inner maps
        self.assertRaises(SchemaFormatError, parse_types, [{"is_a": "types", "schema": {"int": {"cpp": {5: "cpp"}}}}])  # schema inner maps should have only one "generator": str_path pairing
        self.assertRaises(SchemaFormatError, parse_types, [{"is_a": "types", "schema": {"int": {"cpp": {"generator": "generators/test.py", "generator2": "should not be here"}}}}])  # ibid

    def test_that_parse_types_throws_a_SchemaFormatError_for_all_given_schemas_in_a_group_if_any_are_bad(self) -> None:
        raw_data = [
            {"is_a": "types", "schema": {"int": {"cpp": "int", "py": "int"}}},  # known good data
            {"is_a": "types", "schema": {"int": {"cpp": {"generator": "generators/test.py", "generator2": "should not be here"}}}},  # known bad data
        ]

        self.assertRaises(SchemaFormatError, parse_types, raw_data)

    def test_that_parse_types_throws_(self) -> None:
        raw_data = [
            {"is_a": "types", "schema": {"int": {"cpp": "int", "py": "int"}}},
            {"is_a": "types", "schema": {"int": {"cpp": "int", "py": "int"}}},
        ]

        self.assertRaises(RedundantTypeError, parse_types, raw_data)

    def test_that_parse_types_can_load_a_simple_str_to_str_types_that_have_no_arguments(self) -> None:
        raw_data = [{
            "is_a": "types",
            "schema": {
                "int": {
                    "cpp": "int",
                    "py": "int",
                },
            },
        }]

        types_map = parse_types(raw_data)

        self.assertEqual(types_map, {"int": {"cpp": "int", "py": "int", "maximum_possible_args": 0}})

    def test_that_parse_types_can_load_multiple_simple_str_to_str_types_that_have_no_arguments(self) -> None:
        raw_data = [{
            "is_a": "types",
            "schema": {
                "float": {
                    "cpp": "double",
                    "py": "float",
                },
                "str": {
                    "cpp": "std::string",
                    "py": "str",
                },
            },
        }]

        types_map = parse_types(raw_data)

        self.assertEqual(types_map, {"float": {"cpp": "double", "py": "float", "maximum_possible_args": 0}, "str": {"cpp": "std::string", "py": "str", "maximum_possible_args": 0}})

    def test_that_parse_types_can_load_simple_str_to_str_types_that_have_one_argument(self) -> None:
        raw_data = [{
            "is_a": "types",
            "schema": {
                "array": {
                    "cpp": r"std::vector<{_1}>",
                    "py": r"list[{_1}]",
                }
            }
        }]

        types_map = parse_types(raw_data)

        self.assertEqual(types_map, {"array": {"cpp": r"std::vector<{_1}>", "py": r"list[{_1}]", "maximum_possible_args": 1}})

    def test_that_parse_types_can_load_simple_str_to_str_types_that_have_more_than_one_argument(self) -> None:
        raw_data = [{
            "is_a": "types",
            "schema": {
                "map": {
                    "cpp": r"std::map<{_1}, {_2}>",
                    "py": r"dict[{_1}, {_2}]",
                }
            }
        }]

        types_map = parse_types(raw_data)

        self.assertEqual(types_map, {"map": {"cpp": r"std::map<{_1}, {_2}>", "py": r"dict[{_1}, {_2}]", "maximum_possible_args": 2}})
