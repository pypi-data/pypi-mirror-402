from ul_api_utils.const import MIME__MSGPCK, MIME__JSON
from ul_api_utils.utils.api_format import ApiFormat


def test_serialize() -> None:
    cn = {"a": "b", "c": "рудддщ"}

    assert ApiFormat.MESSAGE_PACK.serialize_bytes(cn)

    assert ApiFormat.JSON.mime == MIME__JSON
    assert ApiFormat.MESSAGE_PACK.mime == MIME__MSGPCK
    assert ApiFormat.accept_mimes() == (MIME__MSGPCK, MIME__JSON)

    format_msgpck = ApiFormat.from_mime(MIME__MSGPCK)
    assert format_msgpck is not None
    format_json = ApiFormat.from_mime(MIME__JSON)
    assert format_json is not None

    assert (
        format_msgpck.parse_bytes(ApiFormat.MESSAGE_PACK.serialize_bytes(cn))
        == format_json.parse_bytes(ApiFormat.JSON.serialize_bytes(cn))
    )
