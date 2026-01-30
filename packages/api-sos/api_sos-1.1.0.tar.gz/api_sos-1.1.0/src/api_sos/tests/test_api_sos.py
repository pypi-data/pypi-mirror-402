from api_sos import AssertResponse, HTTPVersion, diff_response


def test_diff_response():
    assert (
        diff_response(
            AssertResponse(
                headers={"a": "b"},
                http_status=200,
                http_version=HTTPVersion(major=1, minor=1),
                encoding="utf-8",
                content="",
            ),
            AssertResponse(
                headers={"a": "b"},
                http_status=200,
                http_version=HTTPVersion(major=1, minor=1),
                encoding="utf-8",
                content="",
            ),
        )
        == []
    )

    assert (
        diff_response(
            AssertResponse(
                headers={"a": "b"},
                http_status=200,
                http_version=HTTPVersion(major=1, minor=1),
                encoding="utf-8",
                content={"a": "b"},
            ),
            AssertResponse(
                headers={"a": "b"},
                http_status=200,
                http_version=HTTPVersion(major=1, minor=1),
                encoding="utf-8",
                content={"a": "b"},
            ),
        )
        == []
    )

    assert (
        diff_response(
            AssertResponse(
                headers={"a": "b"},
                http_status=200,
                http_version=HTTPVersion(major=1, minor=1),
                encoding="utf-8",
                content={"a": "abcd"},
            ),
            AssertResponse(
                headers={"a": "b"},
                http_status=200,
                http_version=HTTPVersion(major=1, minor=1),
                encoding="utf-8",
                content={"a": "{{ actual|length == 4 }}"},
            ),
        )
        == []
    )

    # assert diff_response(Nested(Test(1, "a", 1.0)), Nested(Test(2, "a", 1.0))) == [
    #     DiffResult(field="field_d.field_a", actual_value=1, assert_value=2)
    # ]
