import unittest
import schema


general_schema = schema.Schema([{
    "is_a": schema.Or("types", "model", "value"),
    "schema": schema.Or(dict, list)
}], ignore_extra_keys=True)


types_schema = schema.Schema({
    "is_a": "types",
    "language": str,
    "schema": dict[str, dict]
})


individual_type_schema = schema.Schema({
    "code": str,
    schema.Optional("imports"): str,
    schema.Optional("template"): str,
})


class RepeatedTypesError(Exception):
    pass


def parse_types(type_schemas: list[dict]) -> dict:
    types = {}

    for type_entry in type_schemas:
        types_schema.validate(type_entry)
        language = type_entry["language"]

        if language not in types:
            types[language] = {}

        types_for_language = types[language]

        for schema_entry_key, schema_entry in type_entry["schema"].items():
            if schema_entry_key in types_for_language:
                raise RepeatedTypesError
            individual_type_schema.validate(schema_entry)
            types_for_language[schema_entry_key] = schema_entry

    return types


class TestParsingTypesFromDataThatMeetsTheGeneralSchemaForm(unittest.TestCase):
    def test_that_the_schema_for_a_collection_of_types_is_following_the_correct_format(self) -> None:
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "any", "language": "cpp", "schema": {"int": {"code": "int"}}}])  # bad "is_a" value
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "types", "lgauage": "cpp", "schema": {"int": {"code": "int"}}}])  # missing "language" key
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "types", "language": 6, "schema": {"int": {"code": "int"}}}])  # bad "language" value
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "types", "shema": {}, "language": "cpp"}])  # missing "schema" key
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "types", "schema": 1, "language": "cpp"}])  # bad "schema" type
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "types", "language": "cpp", "schema": {}}])  # empty schema entry
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "types", "language": "cpp", "schema": {1: "blah"}}])  # bad schema entry

    def test_that_the_schema_for_an_individual_entry_in_a_types_schema_is_follow_the_correct_format(self) -> None:
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "types", "language": "cpp", "schema": {"int": {"coded": "int"}}}])  # missing "code" key
        self.assertRaises(schema.SchemaError, parse_types, [{"is_a": "types", "language": "cpp", "schema": {"int": {"code": 1}}}])  # bad "code" value
        parse_types([{"is_a": "types", "language": "cpp", "schema": {"int": {"code": "int", "imports": "int_lib", "template": "enum_file.x"}}}])  # should not raise

    def test_that_within_a_given_language_in_a_collection_of_types_there_are_no_repeated_keys(self) -> None:
        types_schema = [
            {"is_a": "types", "language": "cpp", "schema": {"int": {"code": "int"}}},
            {"is_a": "types", "language": "cpp", "schema": {"int": {"code": "int"}}},
        ]

        self.assertRaises(RepeatedTypesError, parse_types, types_schema)

    def test_that_the_schema_copies_individual_entries_for_its_language_into_the_greater_language_dictionary(self) -> None:
        types_schema = [{"is_a": "types", "language": "cpp", "schema": {
            "str": {"code": "std::string", "imports": "string"},
        }}]

        expected_types = {
            "cpp": {
                "str": {
                    "code": "std::string",
                    "imports": "string"
                }
            }
        }

        types = parse_types(types_schema)

        self.assertEqual(expected_types, types)

    def test_that_the_schema_copies_multiple_entries_for_its_language_into_a_greater_language_dictionary(self) -> None:
        types_schema = [{"is_a": "types", "language": "cpp", "schema": {
            "int": {"code": "int"},
            "float": {"code": "double"},
            "enum": {"code": "{_1}", "template": "cpp_enum.h"}
        }}]

        expected_types = {
            "cpp": {
                "int": {"code": "int"},
                "float": {"code": "double"},
                "enum": {"code": "{_1}", "template": "cpp_enum.h"}
            }
        }

        types = parse_types(types_schema)

        self.assertEqual(expected_types, types)

    def test_that_the_schema_handles_multiple_entries_and_multiple_languages_being_parsed_into_a_greater_types_dictionary(self) -> None:
        types_schema = [
            {"is_a": "types", "language": "cpp", "schema": {
                "int": {"code": "int"},
                "str": {"code": "std::string", "imports": "string"},
            }},
            {"is_a": "types", "language": "python", "schema": {
                "int": {"code": "int"},
                "enum": {"code": "{_1}", "template": "python_enum.h"},
            }},
        ]

        expected_types = {
            "cpp": {
                "int": {"code": "int"},
                "str": {"code": "std::string", "imports": "string"},
            },
            "python": {
                "int": {"code": "int"},
                "enum": {"code": "{_1}", "template": "python_enum.h"},
            },
        }

        types = parse_types(types_schema)

        self.assertEqual(expected_types, types)
