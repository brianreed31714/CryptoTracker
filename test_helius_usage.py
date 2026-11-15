"""Offline credit enforcement and current-service integration regressions."""
import ast
import json
import os
import sqlite3
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from helius_usage import HeliusUsage, HeliusBudgetDenied


ROOT = Path(__file__).resolve().parent


class BudgetFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = time.time()
        self.usage = HeliusUsage(self.root, lambda: self.now)
        self.configure()

    def configure(self, **values):
        config = {"HELIUS_ENABLED": 1, "HELIUS_CREDITS_PER_HOUR": 100,
                  "HELIUS_CREDITS_PER_DAY": 200,
                  "HELIUS_CREDITS_PER_31_DAYS": 300, **values}
        (self.root / ".env.config").write_text("\n".join(f"{k}={v}" for k, v in config.items()))


class BudgetTests(BudgetFixture):
    def test_reservations_survive_restart_and_cannot_overshoot(self):
        self.usage.reserve("enhanced_history")
        restarted = HeliusUsage(self.root, lambda: self.now)
        with self.assertRaises(HeliusBudgetDenied):
            restarted.reserve("getBalance")
        self.assertEqual(restarted.summary()["hour"], {"enhanced_history": 100})

    def test_rolling_windows_day_and_31_day_limit(self):
        for offset in (0, 3601):
            self.now += offset
            self.usage.reserve("enhanced_history")
        self.now += 3601
        with self.assertRaisesRegex(HeliusBudgetDenied, "PER_DAY"):
            self.usage.reserve("getBalance")
        self.now += 86400
        self.usage.reserve("enhanced_history")
        self.now += 86400
        with self.assertRaisesRegex(HeliusBudgetDenied, "31_DAYS"):
            self.usage.reserve("getBalance")
        self.now += 31 * 86400
        self.usage.reserve("getBalance")

    def test_concurrent_services_share_atomic_cap(self):
        def reserve(_):
            try:
                HeliusUsage(self.root, lambda: self.now).reserve("getTokenAccounts")
                return True
            except HeliusBudgetDenied:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(reserve, range(30))), 10)
        self.assertEqual(self.usage.summary()["hour"], {"getTokenAccounts": 100})

    def test_cache_survives_restart_and_empty_history_is_cached(self):
        fetch = Mock(return_value=[])
        self.assertEqual(self.usage.cached("history:test", 3600, fetch), [])
        restarted = HeliusUsage(self.root, lambda: self.now)
        self.assertEqual(restarted.cached("history:test", 3600, fetch), [])
        fetch.assert_called_once()
        self.now += 3601
        restarted.cached("history:test", 3600, fetch)
        self.assertEqual(fetch.call_count, 2)

    def test_failed_refresh_has_persistent_cooldown_and_sanitized_error(self):
        fetch = Mock(side_effect=RuntimeError("secret-api-key-in-url"))
        with self.assertRaisesRegex(HeliusBudgetDenied, "HELIUS_REFRESH_FAILED"):
            self.usage.cached("wallet", 3600, fetch)
        with self.assertRaisesRegex(HeliusBudgetDenied, "COOLDOWN"):
            HeliusUsage(self.root, lambda: self.now).cached("wallet", 3600, fetch)
        fetch.assert_called_once()

    def test_concurrent_cache_refresh_is_coalesced(self):
        def fetch():
            with self.assertRaisesRegex(HeliusBudgetDenied, "COOLDOWN"):
                HeliusUsage(self.root, lambda: self.now).cached("same", 3600, Mock())
            return {"count": 5}
        self.assertEqual(self.usage.cached("same", 3600, fetch), {"count": 5})

    def test_disabled_invalid_unpriced_and_corrupt_ledger_fail_closed(self):
        for config in ({"HELIUS_ENABLED": 0}, {"HELIUS_CREDITS_PER_DAY": "bad"},
                       {"HELIUS_CREDITS_PER_DAY": 0}):
            self.configure(**config)
            with self.assertRaises(HeliusBudgetDenied):
                self.usage.reserve("getBalance")
        self.configure()
        with self.assertRaisesRegex(HeliusBudgetDenied, "UNPRICED"):
            self.usage.reserve("unknown")
        self.usage.path.parent.mkdir(exist_ok=True)
        self.usage.path.write_text("broken sqlite")
        with self.assertRaisesRegex(HeliusBudgetDenied, "LEDGER_UNAVAILABLE"):
            self.usage.reserve("getBalance")

    def test_local_environment_cannot_inflate_tracked_budget(self):
        with patch.dict(os.environ, {"HELIUS_CREDITS_PER_HOUR": "1000000"}):
            self.usage.reserve("enhanced_history")
            with self.assertRaises(HeliusBudgetDenied):
                self.usage.reserve("getBalance")

    def test_provider_halt_survives_restart(self):
        self.usage.halt(86400)
        with self.assertRaisesRegex(HeliusBudgetDenied, "HALTED"):
            HeliusUsage(self.root, lambda: self.now).reserve("getBalance")
        self.now += 86401
        self.usage.reserve("getBalance")

    def test_holder_only_mode_blocks_paid_history_and_general_rpc(self):
        with (self.root / ".env.config").open("a") as f:
            f.write("\nHELIUS_MODE=holders_only\n")
        for method in ("enhanced_history", "getBalance", "getTokenSupply"):
            with self.assertRaisesRegex(HeliusBudgetDenied, "HOLDER_ONLY"):
                self.usage.reserve(method)
        self.usage.reserve("getTokenAccounts")
        self.assertEqual(self.usage.summary()["hour"], {"getTokenAccounts": 10})
        with sqlite3.connect(self.usage.path) as conn:
            row = conn.execute("SELECT pid,length(module_digest) FROM clients").fetchone()
        self.assertEqual(row, (os.getpid(), 64))


class ServiceTests(BudgetFixture):
    def setUp(self):
        super().setUp()
        # Extract the real functions without importing the engine or its wallet
        # dependencies, starting services, or reading the user's .env.
        source = ast.parse((ROOT / "auto_trader_with_alerts_v11_10_research_fairness.py").read_text(encoding="utf-8-sig"))
        names = {"_helius_post_json", "_helius_holder_count", "holder_metrics_for_token", "_refresh_holder_metrics"}
        tree = ast.Module(body=[n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
        self.api = Mock()
        self.api.RequestException = requests.RequestException
        self.env = dict(ROOT=self.root, HeliusUsage=HeliusUsage, HeliusBudgetDenied=HeliusBudgetDenied,
                        os=os, time=time, datetime=datetime, timezone=timezone,
                        requests=self.api, safe_number=lambda x: float(x or 0),
                        helius_enabled=lambda *args: True, _helius_circuit_open=lambda: False,
                        _is_helius_url=lambda url: "helius" in url,
                        _permanent_helius_failure=lambda *args: False,
                        _warn_api_once=Mock(), _load_holder_history=Mock(return_value=[]),
                        _prior_holder_sample=Mock(return_value=None), _holder_change=Mock(return_value=(1, 1)),
                        _append_holder_history=Mock(), _save_holder_latest=Mock())
        exec(compile(tree, "engine-credit-functions", "exec"), self.env)

    def response(self, code=200, body=None):
        obj = Mock(status_code=code, text="", headers={})
        obj.json.return_value = body or {"result": {"token_accounts": []}}
        return obj

    def test_every_retry_reserves_credits(self):
        self.api.post.side_effect = [self.response(429), self.response()]
        with patch.object(time, "sleep"):
            self.env["_helius_post_json"]("https://mainnet.helius-rpc.com", {"method": "getTokenAccounts"})
        self.assertEqual(self.usage.summary()["hour"], {"getTokenAccounts": 20})

    def test_exhausted_budget_never_sends_request(self):
        self.usage.reserve("enhanced_history")
        with self.assertRaises(HeliusBudgetDenied):
            self.env["_helius_post_json"]("https://mainnet.helius-rpc.com", {"method": "getTokenAccounts"})
        self.api.post.assert_not_called()

    def test_public_rpc_does_not_reserve_helius_credits(self):
        self.api.post.return_value = self.response()
        self.env["_helius_post_json"]("https://api.mainnet-beta.solana.com", {"method": "getBalance"})
        self.assertEqual(self.usage.summary()["hour"], {})

    def test_holder_page_cap_and_cache_survive_restart_and_force(self):
        self.api.post.return_value = self.response(body={"result": {"token_accounts": [{"owner": "one", "amount": 1}]}})
        settings = {"HOLDER_METRICS_PAGE_LIMIT": 1, "HOLDER_METRICS_MAX_PAGES": 10}
        with patch.dict(os.environ, {"HELIUS_API_KEY": "test-key"}):
            first = self.env["holder_metrics_for_token"]("mint", "TEST", 100, settings)
            second = self.env["holder_metrics_for_token"]("mint", "TEST", 200, settings, force=True)
        self.assertEqual(self.api.post.call_count, 2)
        self.assertTrue(first["holder_count_capped"])
        self.assertEqual(first["holder_change_10m"], "")
        self.assertEqual(second["market_cap_per_holder"], 200)
        self.assertEqual(first["observed_at"], second["observed_at"])
        self.env["_append_holder_history"].assert_called_once()

    def test_old_samples_do_not_fabricate_short_term_growth(self):
        self.env["_prior_holder_sample"].return_value = {"dt": datetime.now(timezone.utc) - timedelta(hours=6), "holder_count": 10}
        self.api.post.return_value = self.response(body={"result": {"token_accounts": [{"owner": "one", "amount": 1}]}})
        with patch.dict(os.environ, {"HELIUS_API_KEY": "test-key"}):
            metrics = self.env["holder_metrics_for_token"]("mint", "TEST", 100, {})
        self.assertEqual(metrics["holder_change_10m"], "")
        self.assertEqual(metrics["holder_change_30m"], "")

    def test_holder_error_is_not_recorded_as_zero_holders(self):
        self.api.post.side_effect = requests.RequestException("failure")
        with patch.dict(os.environ, {"HELIUS_API_KEY": "test-key"}), patch.object(time, "sleep"):
            result = self.env["holder_metrics_for_token"]("mint", "TEST", 100, {"HELIUS_MAX_RETRIES": 0})
            self.env["holder_metrics_for_token"]("mint", "TEST", 100, {})
        self.assertNotEqual(result["holder_status"], "OK")
        self.env["_append_holder_history"].assert_not_called()
        self.assertEqual(self.api.post.call_count, 1)

    def test_monitor_history_uses_same_budget_and_persistent_cache(self):
        from SmartMoneyMonitor import smart_money_monitor_v2_3_feed_health_audit as monitor
        with (self.root / ".env.config").open("a") as f:
            f.write("\nSMART_MONEY_HELIUS_ENABLED=1\n")
        response = Mock(status_code=200)
        response.json.return_value = []
        with patch.object(monitor, "PROJECT_ROOT", self.root), patch.object(monitor, "HELIUS_REPO_DISABLED", False), patch.object(monitor.requests, "get", return_value=response) as get:
            self.assertEqual(monitor.helius_recent_transactions("wallet"), [])
            self.assertEqual(monitor.helius_recent_transactions("wallet"), [])
            get.assert_called_once()
        self.assertEqual(self.usage.summary()["hour"], {"enhanced_history": 100})
        with self.assertRaises(HeliusBudgetDenied):
            self.usage.reserve("getTokenAccounts")


if __name__ == "__main__":
    unittest.main()
