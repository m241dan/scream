import unittest


class EmptyRawDataError(Exception):
    pass


class MissingIsAError(Exception):
    pass


class NoTypesError(Exception):
    pass


class NoLanguageError(Exception):
    pass


class NoSchemaError(Exception):
    pass


# should probably not take raw data but something that has already filtered for the first two checks?
def parse_types(raw_data: list[dict]) -> dict:
    if not raw_data:
        raise EmptyRawDataError

    for data in raw_data:
        if 'is_a' not in data.keys():
            raise MissingIsAError

    types_data = [data for data in raw_data if data['is_a'] == "types"]
    if not types_data:
        raise NoTypesError

    for data in types_data:
        if 'language' not in data.keys():
            raise NoLanguageError

    raise NoSchemaError


class TestParsingTypesFromRawData(unittest.TestCase):
    def test_that_parse_types_throws_an_EmptyRawDataError_when_a_raw_data_list_is_empty(self) -> None:
        self.assertRaises(EmptyRawDataError, parse_types, [])

    def test_that_parse_types_throws_a_MissingIsAError_when_an_entry_in_raw_data_does_not_have_an_is_a_key(self) -> None:
        self.assertRaises(MissingIsAError, parse_types, [{}])

    def test_that_parse_types_throws_a_NoTypesError_when_no_types_entries_are_present_in_the_raw_data(self) -> None:
        self.assertRaises(NoTypesError, parse_types, [{"is_a": "model"}])

    def test_that_parse_types_throws_a_NoLanguageError_when_no_language_is_specified_by_a_types_entry(self) -> None:
        self.assertRaises(NoLanguageError, parse_types, [{"is_a": "types"}])

    def test_that_parse_types_throws_a_NoSchemaError_when_a_types_entry_does_not_specify_a_schema(self) -> None:
        self.assertRaises(NoSchemaError, parse_types, [{"is_a": "types", "language": "cpp"}])
