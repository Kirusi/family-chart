from family_chart.utils import Utils


class TestExtractJson:
    def test_no_curly_brace_returns_none(self):
        assert Utils.extract_json("no json here") is None

    def test_empty_string_returns_none(self):
        assert Utils.extract_json("") is None

    def test_none_returns_none(self):
        assert Utils.extract_json(None) is None

    def test_plain_json_object(self):
        assert Utils.extract_json('{"a": 1}') == {"a": 1}

    def test_json_object_with_prefix_text(self):
        text = 'Some error occurred. Details: {"a": 1, "b": [1, 2, 3]}'
        assert Utils.extract_json(text) == {"a": 1, "b": [1, 2, 3]}

    def test_json_object_with_trailing_text_is_ignored(self):
        text = '{"a": 1} and then some trailing text'
        assert Utils.extract_json(text) == {"a": 1}

    def test_nested_json_object(self):
        text = 'prefix {"a": {"b": 2}, "c": [{"d": 3}]} suffix'
        assert Utils.extract_json(text) == {"a": {"b": 2}, "c": [{"d": 3}]}

    def test_empty_json_object(self):
        assert Utils.extract_json("{}") == {}

    def test_malformed_json_after_brace_returns_none(self):
        assert Utils.extract_json("{not valid json}") is None

    def test_only_json_array_with_no_curly_brace_returns_none(self):
        assert Utils.extract_json("[1, 2, 3]") is None

    def test_first_curly_brace_must_start_valid_json_even_if_a_later_one_would_work(self):
        # extract_json only ever looks at the first "{" it finds; a well-formed object
        # appearing later in the string is never reached if the first one fails to parse.
        text = '{ not json } {"a": 1}'
        assert Utils.extract_json(text) is None
