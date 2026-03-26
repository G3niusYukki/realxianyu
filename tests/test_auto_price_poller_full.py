"""自动改价轮询器测试。"""

import threading
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.modules.orders.auto_price_poller import (
    AutoPricePoller,
    get_price_poller,
    set_price_poller,
    _POLL_INTERVAL_DEFAULT,
    _MAX_QUOTE_AGE_DEFAULT,
    _PROCESSED_CACHE_TTL,
)


@pytest.fixture()
def poller():
    get_config_fn = MagicMock(return_value={})
    p = AutoPricePoller(get_config_fn=get_config_fn, interval=10)
    yield p
    p.stop()
    AutoPricePoller._instance = None


class TestSingleton:
    def test_get_set(self):
        AutoPricePoller._instance = None
        assert get_price_poller() is None
        mock_p = MagicMock()
        set_price_poller(mock_p)
        assert get_price_poller() is mock_p
        set_price_poller(None)
        assert get_price_poller() is None


class TestInit:
    def test_minimum_interval(self):
        p = AutoPricePoller(get_config_fn=MagicMock(), interval=1)
        assert p._interval == 10
        p.stop()

    def test_default_interval(self):
        p = AutoPricePoller(get_config_fn=MagicMock())
        assert p._interval == _POLL_INTERVAL_DEFAULT
        p.stop()

    def test_custom_interval(self):
        p = AutoPricePoller(get_config_fn=MagicMock(), interval=30)
        assert p._interval == 30
        p.stop()

    def test_initial_state(self, poller):
        assert poller._thread is None
        assert not poller._stop_event.is_set()
        assert poller._processed == {}
        assert poller._reminded == {}


class TestStartStop:
    def test_start_creates_thread(self, poller):
        poller.start()
        assert poller._thread is not None
        assert poller._thread.is_alive()

    def test_double_start_noop(self, poller):
        poller.start()
        t1 = poller._thread
        poller.start()
        assert poller._thread is t1

    def test_stop(self, poller):
        poller.start()
        poller.stop()
        assert poller._thread is None

    def test_stop_without_start(self, poller):
        poller.stop()  # Should not raise


class TestTriggerNow:
    def test_sets_trigger_event(self, poller):
        assert not poller._trigger_event.is_set()
        poller.trigger_now()
        assert poller._trigger_event.is_set()


class TestEvictStaleCache:
    def test_evicts_old_processed(self, poller):
        poller._processed["old_order"] = time.time() - _PROCESSED_CACHE_TTL - 100
        poller._processed["new_order"] = time.time()
        poller._evict_stale_cache()
        assert "old_order" not in poller._processed
        assert "new_order" in poller._processed

    def test_evicts_old_reminded(self, poller):
        poller._reminded["old_remind"] = time.time() - _PROCESSED_CACHE_TTL - 100
        poller._reminded["new_remind"] = time.time()
        poller._evict_stale_cache()
        assert "old_remind" not in poller._reminded
        assert "new_remind" in poller._reminded

    def test_empty_cache(self, poller):
        poller._evict_stale_cache()  # Should not raise


class TestBuildClient:
    def test_no_config_returns_none(self, poller):
        poller._get_config = MagicMock(return_value={})
        assert poller._build_client() is None

    def test_missing_app_key(self, poller):
        poller._get_config = MagicMock(return_value={"xianguanjia": {"app_secret": "secret"}})
        assert poller._build_client() is None

    def test_missing_app_secret(self, poller):
        poller._get_config = MagicMock(return_value={"xianguanjia": {"app_key": "key"}})
        assert poller._build_client() is None

    def test_valid_config(self, poller):
        poller._get_config = MagicMock(
            return_value={
                "xianguanjia": {
                    "app_key": "key123",
                    "app_secret": "secret456",
                    "base_url": "https://api.test.com",
                    "timeout": 10,
                    "mode": "self_developed",
                    "seller_id": "seller1",
                }
            }
        )
        with patch("src.integrations.xianguanjia.open_platform_client.OpenPlatformClient") as MockClient:
            poller._build_client()
            MockClient.assert_called_once()


class TestFetchPendingOrders:
    def test_no_client(self, poller):
        with patch.object(poller, "_build_client", return_value=None):
            assert poller._fetch_pending_orders() == []

    def test_api_error(self, poller):
        mock_client = MagicMock()
        mock_client.list_orders.side_effect = Exception("network error")
        with patch.object(poller, "_build_client", return_value=mock_client):
            assert poller._fetch_pending_orders() == []

    def test_api_not_ok(self, poller):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.error_message = "auth failed"
        mock_client = MagicMock()
        mock_client.list_orders.return_value = mock_resp
        with patch.object(poller, "_build_client", return_value=mock_client):
            assert poller._fetch_pending_orders() == []

    def test_dict_response(self, poller):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.data = {"list": [{"order_no": "A1"}, {"order_no": "A2"}]}
        mock_client = MagicMock()
        mock_client.list_orders.return_value = mock_resp
        with patch.object(poller, "_build_client", return_value=mock_client):
            orders = poller._fetch_pending_orders()
            assert len(orders) == 2

    def test_nested_data_response(self, poller):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.data = {"data": {"list": [{"order_no": "B1"}]}}
        mock_client = MagicMock()
        mock_client.list_orders.return_value = mock_resp
        with patch.object(poller, "_build_client", return_value=mock_client):
            orders = poller._fetch_pending_orders()
            assert len(orders) == 1

    def test_list_response(self, poller):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.data = [{"order_no": "C1"}]
        mock_client = MagicMock()
        mock_client.list_orders.return_value = mock_resp
        with patch.object(poller, "_build_client", return_value=mock_client):
            orders = poller._fetch_pending_orders()
            assert len(orders) == 1

    def test_filters_non_dict(self, poller):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.data = {"list": [{"order_no": "D1"}, "not_a_dict", None]}
        mock_client = MagicMock()
        mock_client.list_orders.return_value = mock_resp
        with patch.object(poller, "_build_client", return_value=mock_client):
            orders = poller._fetch_pending_orders()
            assert len(orders) == 1


class TestRunAutoPrice:
    def test_no_client(self, poller):
        with patch.object(poller, "_build_client", return_value=None):
            poller._run_auto_price([{"order_no": "X1"}], {})

    def test_skips_processed(self, poller):
        poller._processed["X1"] = time.time()
        mock_client = MagicMock()
        with patch.object(poller, "_build_client", return_value=mock_client):
            with patch.object(poller, "_process_order") as mock_process:
                poller._run_auto_price([{"order_no": "X1"}], {})
                mock_process.assert_not_called()

    def test_skips_empty_order_no(self, poller):
        mock_client = MagicMock()
        with patch.object(poller, "_build_client", return_value=mock_client):
            with patch.object(poller, "_process_order") as mock_process:
                poller._run_auto_price([{"order_no": ""}], {})
                mock_process.assert_not_called()


class TestProcessOrder:
    def test_no_buyer_info(self, poller):
        mock_client = MagicMock()
        mock_detail = MagicMock()
        mock_detail.ok = True
        mock_detail.data = {}
        mock_client.get_order_detail.return_value = mock_detail

        with patch("src.modules.quote.ledger.get_quote_ledger") as mock_ledger:
            poller._process_order(mock_client, "O1", {"order_no": "O1"}, {})

    def test_no_quote_found(self, poller):
        mock_client = MagicMock()
        mock_ledger_inst = MagicMock()
        mock_ledger_inst.find_by_buyer.return_value = None

        order = {"order_no": "O1", "buyer_nick": "买家A", "buyer_eid": "eid1", "goods": {"item_id": "i1"}}

        with patch("src.modules.quote.ledger.get_quote_ledger", return_value=mock_ledger_inst):
            poller._process_order(mock_client, "O1", order, {})

    def test_fallback_use_listing_price(self, poller):
        mock_client = MagicMock()
        mock_ledger_inst = MagicMock()
        mock_ledger_inst.find_by_buyer.return_value = None

        order = {"order_no": "O1", "buyer_nick": "买家A", "buyer_eid": "eid1", "goods": {"item_id": "i1"}}
        cfg = {"fallback_action": "use_listing_price"}

        with patch("src.modules.quote.ledger.get_quote_ledger", return_value=mock_ledger_inst):
            poller._process_order(mock_client, "O1", order, cfg)
            assert "O1" in poller._processed

    def test_price_already_correct(self, poller):
        mock_client = MagicMock()
        mock_ledger_inst = MagicMock()
        mock_ledger_inst.find_by_buyer.return_value = {
            "quote_rows": [{"courier": "圆通", "total_fee": 12.50}],
            "courier_choice": "圆通",
        }

        order = {
            "order_no": "O1",
            "buyer_nick": "买家A",
            "buyer_eid": "eid1",
            "goods": {"item_id": "i1"},
            "total_amount": 1250,
        }

        with patch("src.modules.quote.ledger.get_quote_ledger", return_value=mock_ledger_inst):
            poller._process_order(mock_client, "O1", order, {})
            assert "O1" in poller._processed

    def test_successful_price_modify(self, poller):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_client = MagicMock()
        mock_client.modify_order_price.return_value = mock_resp

        mock_ledger_inst = MagicMock()
        mock_ledger_inst.find_by_buyer.return_value = {
            "quote_rows": [{"courier": "圆通", "total_fee": 15.0}],
            "courier_choice": "圆通",
        }

        order = {
            "order_no": "O1",
            "buyer_nick": "买家A",
            "buyer_eid": "eid1",
            "goods": {"item_id": "i1"},
            "total_amount": 1000,
        }

        with patch("src.modules.quote.ledger.get_quote_ledger", return_value=mock_ledger_inst):
            poller._process_order(mock_client, "O1", order, {})
            assert "O1" in poller._processed

    def test_no_valid_fee_in_quote(self, poller):
        mock_client = MagicMock()
        mock_ledger_inst = MagicMock()
        mock_ledger_inst.find_by_buyer.return_value = {
            "quote_rows": [{"courier": "圆通", "total_fee": None}],
            "courier_choice": "圆通",
        }

        order = {"order_no": "O1", "buyer_nick": "买家A", "buyer_eid": "eid1", "goods": {"item_id": "i1"}}

        with patch("src.modules.quote.ledger.get_quote_ledger", return_value=mock_ledger_inst):
            poller._process_order(mock_client, "O1", order, {})

    def test_uses_min_fee_when_no_courier_choice(self, poller):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_client = MagicMock()
        mock_client.modify_order_price.return_value = mock_resp

        mock_ledger_inst = MagicMock()
        mock_ledger_inst.find_by_buyer.return_value = {
            "quote_rows": [
                {"courier": "圆通", "total_fee": 15.0},
                {"courier": "顺丰", "total_fee": 25.0},
            ],
            "courier_choice": "",
        }

        order = {
            "order_no": "O1",
            "buyer_nick": "买家A",
            "buyer_eid": "eid1",
            "goods": {"item_id": "i1"},
            "total_amount": 0,
        }

        with patch("src.modules.quote.ledger.get_quote_ledger", return_value=mock_ledger_inst):
            poller._process_order(mock_client, "O1", order, {})
            call_args = mock_client.modify_order_price.call_args[0][0]
            assert call_args["order_price"] == 1500  # min fee * 100


class TestRunAutoRemind:
    def test_skips_processed(self, poller):
        poller._reminded["O1"] = time.time()
        poller._run_auto_remind([{"order_no": "O1"}], {})

    def test_skips_recent_order(self, poller):
        order = {"order_no": "O1", "order_time": int(time.time())}
        poller._run_auto_remind([order], {"auto_remind_delay_minutes": 60})

    def test_no_session_id(self, poller):
        order = {"order_no": "O1", "buyer_nick": "买家A", "order_time": 0}
        with patch.object(poller, "_resolve_session_for_remind", return_value=""):
            poller._run_auto_remind([order], {"auto_remind_delay_minutes": 0})


class TestResolveSession:
    def test_empty_buyer_nick(self, poller):
        assert poller._resolve_session_for_remind("O1", "") == ""

    def test_from_ledger(self, poller):
        with patch("src.modules.quote.ledger.get_quote_ledger") as mock_gl:
            mock_gl.return_value.find_by_buyer.return_value = {"session_id": "sess123"}
            result = poller._resolve_session_for_remind("O1", "买家A")
            assert result == "sess123"

    def test_from_ws_live(self, poller):
        with patch("src.modules.quote.ledger.get_quote_ledger") as mock_gl:
            mock_gl.return_value.find_by_buyer.return_value = None
            with patch("src.modules.messages.ws_live.get_session_by_buyer_nick", return_value="ws_sess"):
                result = poller._resolve_session_for_remind("O1", "买家A")
                assert result == "ws_sess"

    def test_all_fail_returns_empty(self, poller):
        with patch("src.modules.quote.ledger.get_quote_ledger") as mock_gl:
            mock_gl.return_value.find_by_buyer.return_value = None
            with patch("src.modules.messages.ws_live.get_session_by_buyer_nick", return_value=None):
                assert poller._resolve_session_for_remind("O1", "买家A") == ""


class TestLoop:
    def test_loop_disabled_both(self, poller):
        poller._get_config = MagicMock(return_value={})
        poller._stop_event.set()
        poller._loop()  # Should exit immediately

    def test_loop_with_trigger(self, poller):
        poller._get_config = MagicMock(
            return_value={
                "auto_price_modify": {"enabled": False},
                "order_reminder": {"auto_remind_enabled": False},
            }
        )
        poller._trigger_event.set()
        poller._stop_event.set()
        poller._loop()
