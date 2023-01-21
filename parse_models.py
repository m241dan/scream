import re
import unittest
import schema


regex_type_pattern = r'(\w+)\((\d+)\)'

models_schema = schema.Schema({
    "is_a": "model",
    "name": str,
    "schema": schema.Schema([{
        "name": str,
        "type": schema.And(str, lambda t: re.match(regex_type_pattern, t)),
        schema.Optional('test'): list,
        schema.Optional('len'): int,
    }])
})


def parse_models(model_schemas: list[dict]) -> dict:
    models = {}

    for model in model_schemas:
        models_schema.validate(model)

        parameters = []
        for parameter in model["schema"]:
            type_matches = re.match(regex_type_pattern, parameter["type"])

            parameters.append({
                "name": parameter["name"],
                "type": type_matches.group(1),
                "size": int(type_matches.group(2)),
                "test": parameter["test"] if "test" in parameter else None,
                "len": parameter["len"] if "len" in parameter else 1,
            })

        models[model["name"]] = parameters

    return models


class TestParsingModelsFromDataThatMeetsTheGeneralSchemaForm(unittest.TestCase):
    def test_that_the_schema_for_a_collection_of_models_is_following_the_correct_format(self) -> None:
        self.assertRaises(schema.SchemaError, parse_models, [{"is_a": "any"}])  # bad is_a value
        self.assertRaises(schema.SchemaError, parse_models, [{"is_a": "model", "nam": "player"}])  # missing name key
        self.assertRaises(schema.SchemaError, parse_models, [{"is_a": "model", "name": 1}])  # bad name value
        self.assertRaises(schema.SchemaError, parse_models, [{"is_a": "model", "name": "player", "shema": []}])  # missing schema key
        self.assertRaises(schema.SchemaError, parse_models, [{"is_a": "model", "name": "player", "schema": {}}])  # bad schema value

    def test_that_the_entries_in_the_model_match_the_minimum_schema(self) -> None:
        self.assertRaises(schema.SchemaError, parse_models, [{"is_a": "model", "name": "player", "schema": [{"nme": "age", "type": "int(2)"}]}])  # missing name key
        self.assertRaises(schema.SchemaError, parse_models, [{"is_a": "model", "name": "player", "schema": [{"name": "age", "typ": "int(2)"}]}])  # missing type key
        self.assertRaises(schema.SchemaError, parse_models, [{"is_a": "model", "name": "player", "schema": [{"name": "age", "type": "int"}]}])  # missing type size

    def test_that_a_model_with_one_field_parses_that_fields_name_and_size_appropriately(self) -> None:
        models = [{"is_a": "model", "name": "player", "schema": [
            {"name": "age", "type": "int(2)"},
        ]}]

        expected_models = {"player": [
            {"name": "age", "type": "int", "size": 2, "test": None, "len": 1}
        ]}

        actual_models = parse_models(models)

        self.assertEqual(expected_models, actual_models)

    def test_that_a_model_with_two_fields_parses_those_fields_names_and_sizes_appropriately(self) -> None:
        models = [{"is_a": "model", "name": "player", "schema": [
            {"name": "name", "type": "str(30)"},
            {"name": "age", "type": "int(2)"},
        ]}]

        expected_models = {"player": [
            {"name": "name", "type": "str", "size": 30, "test": None, "len": 1},
            {"name": "age", "type": "int", "size": 2, "test": None, "len": 1},
        ]}

        actual_models = parse_models(models)

        self.assertEqual(expected_models, actual_models)

    def test_that_a_model_with_the_optional_test_and_len_field_parse_appropriately(self) -> None:
        models = [{"is_a": "model", "name": "weapon", "schema": [
            {"name": "type", "type": "str(20)", "test": ["Sword", "Axe", "Spear"]},
            {"name": "stats", "type": "list(30)", "len": 30},
        ]}]

        expected_models = {"weapon": [
            {"name": "type", "type": "str", "size": 20, "test": ["Sword", "Axe", "Spear"], "len": 1},
            {"name": "stats", "type": "list", "size": 30, "len": 30, "test": None},
        ]}

        actual_models = parse_models(models)

        self.assertEqual(expected_models, actual_models)
