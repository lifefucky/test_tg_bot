"""Tests for OnlineContract with mocked HTTP."""

from unittest.mock import MagicMock, patch

from fetch_modules.online_trade import OnlineContract


def _mock_response(status: int, json_data=None, json_raises=None):
    r = MagicMock()
    r.status_code = status
    if json_raises:
        r.json.side_effect = json_raises
    else:
        r.json.return_value = json_data if json_data is not None else {}
    return r


@patch("fetch_modules.online_trade.requests.get")
def test_get_procedures_non_200_returns_none(mock_get):
    mock_get.return_value = _mock_response(500)
    oc = OnlineContract()
    assert oc.get_procedures(["1811"]) is None


@patch("fetch_modules.online_trade.requests.get")
def test_get_procedures_empty_body_returns_none(mock_get):
    mock_get.return_value = _mock_response(200, json_data={})
    oc = OnlineContract()
    assert oc.get_procedures(["1811"]) is None


@patch("fetch_modules.online_trade.requests.get")
def test_get_procedures_missing_data_key_returns_none(mock_get):
    mock_get.return_value = _mock_response(200, json_data={"total": 0})
    oc = OnlineContract()
    assert oc.get_procedures(["1811"]) is None


@patch("fetch_modules.online_trade.requests.get")
def test_get_procedures_empty_list(mock_get):
    mock_get.return_value = _mock_response(200, json_data={"data": []})
    oc = OnlineContract()
    assert oc.get_procedures(["1811"]) == []


@patch("fetch_modules.online_trade.requests.get")
def test_get_procedures_success_normalizes_row(mock_get):
    mock_get.return_value = _mock_response(
        200,
        json_data={
            "data": [
                {
                    "id": 100,
                    "type": 1,
                    "name": "Proc",
                    "date": "d",
                    "status": 1,
                    "useNDS": False,
                    "nds": 0,
                    "reBiddingStart": "a",
                    "reBiddingEnd": "b",
                    "owner": {"name": "ACME"},
                }
            ]
        },
    )
    oc = OnlineContract()
    rows = oc.get_procedures(["1811"])
    assert len(rows) == 1
    r0 = rows[0]
    assert r0["owner"] == "ACME"
    assert r0["link"] == "https://onlinecontract.ru/tenders/100"
    assert r0["name"] == "Proc"


@patch("fetch_modules.online_trade.requests.get")
def test_get_positions_non_200_returns_none(mock_get):
    mock_get.return_value = _mock_response(404)
    oc = OnlineContract()
    assert oc.get_positions("123") is None


@patch("fetch_modules.online_trade.requests.get")
def test_get_positions_empty_data_array(mock_get):
    mock_get.return_value = _mock_response(200, json_data={"data": []})
    oc = OnlineContract()
    out = oc.get_positions("555")
    assert out["positions"] == []
    assert out["common_message"]["Id"] == "555"


@patch("fetch_modules.online_trade.requests.get")
def test_get_positions_with_rows(mock_get):
    mock_get.return_value = _mock_response(
        200,
        json_data={
            "data": [
                {
                    "name": "N1",
                    "totalCount": 1,
                    "unit": "u",
                    "price": 5,
                    "ownerSrok": "pay",
                    "ownerSklad": "ship",
                    "deliveryPlace": "here",
                }
            ]
        },
    )
    oc = OnlineContract()
    out = oc.get_positions("1")
    assert len(out["positions"]) == 1
    assert out["positions"][0]["name"] == "N1"
    assert out["common_message"].get("Id") == "1"
