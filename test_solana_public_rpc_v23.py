"""Offline safety tests for the read-only Solana public RPC observer."""
import unittest
from unittest.mock import patch
from SmartMoneyMonitor.solana_public_rpc_v23 import classify_swap, process_wallet, rpc

WALLET = "watched-wallet"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

def balance(mint, value):
    return {"owner":WALLET, "mint":mint,
            "uiTokenAmount":{"uiAmountString":str(value)}}

def tx(signed=True, buy=True):
    return {"transaction":{"message":{"accountKeys":[
                {"pubkey":WALLET,"signer":signed}]}},
            "meta":{"err":None,
                    "preTokenBalances":[balance(USDC,100)],
                    "postTokenBalances":[balance(USDC,75)] +
                         ([balance("TOKEN",1000)] if buy else [])}}

class PublicRPCTests(unittest.TestCase):
    def test_stablecoin_funded_buy(self):
        buy = classify_swap(tx(), WALLET)
        self.assertEqual(buy["estimated_spend_usd"],25)
        self.assertEqual(buy["token_mint"],"TOKEN")

    def test_airdrop_not_a_buy(self):
        value = tx()
        value["meta"]["preTokenBalances"] = []
        self.assertIsNone(classify_swap(value,WALLET))

    def test_failed_transaction_not_a_buy(self):
        value = tx()
        value["meta"]["err"] = {"InstructionError":[0,"Fail"]}
        self.assertIsNone(classify_swap(value,WALLET))

    def test_requires_wallet_signature(self):
        self.assertIsNone(classify_swap(tx(signed=False),WALLET))

    def test_does_not_use_legacy_helius_initialized_state(self):
        class Trader:
            wallet = WALLET
            name = "Test Whale"
        state={"seen_signatures":["legacy"],"initialized":{WALLET:True}}
        with patch("SmartMoneyMonitor.solana_public_rpc_v23.recent_signatures",
                   return_value=[{"signature":"old"}]), patch(
                    "SmartMoneyMonitor.solana_public_rpc_v23.fetch_transaction") as fetch:
            n=process_wallet(Trader(),state,lambda *args: self.fail("Unexpected buy"),
                             lambda s: None)
            fetch.assert_not_called()
        self.assertEqual(n,0)
        self.assertIn("old",state["rpc_seen_signatures"][WALLET])
        self.assertTrue(state["rpc_initialized"][WALLET])

    def test_rpc_never_accepts_helius_url(self):
        with patch.dict("os.environ",{"SMART_MONEY_SOLANA_RPC_URL":
                                     "https://mainnet.helius-rpc.com"}):
            with self.assertRaises(ValueError):
                rpc("getSlot",[])

    def test_empty_rpc_page_does_not_initialize(self):
        class Trader:
            wallet = WALLET
            name = "Test Whale"
        state={}
        with patch("SmartMoneyMonitor.solana_public_rpc_v23.recent_signatures",
                   return_value=[]):
            self.assertEqual(process_wallet(Trader(),state,lambda *a: None,lambda s: None),0)
        self.assertFalse(state.get("rpc_initialized",{}).get(WALLET,False))

    def test_new_transaction_processed_after_baseline(self):
        class Trader:
            wallet = WALLET
            name = "Test Whale"
        state={"rpc_initialized":{WALLET:True},
               "rpc_seen_signatures":{WALLET:["old"]}}
        buys=[]
        with patch("SmartMoneyMonitor.solana_public_rpc_v23.recent_signatures",
                   return_value=[{"signature":"new","blockTime":12345},
                                 {"signature":"old"}]), patch(
                  "SmartMoneyMonitor.solana_public_rpc_v23.fetch_transaction",
                   return_value=tx()):
            n=process_wallet(Trader(),state,lambda *args: buys.append(args),lambda s: None)
        self.assertEqual(n,1)
        self.assertEqual(len(buys),1)
        self.assertIn("new",state["rpc_seen_signatures"][WALLET])

if __name__ == "__main__":
    unittest.main()
