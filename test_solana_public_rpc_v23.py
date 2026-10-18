"""Offline tests for the conservative public-RPC Solana observer."""
import unittest
from unittest.mock import patch
from SmartMoneyMonitor.solana_public_rpc_v23 import classify_swap, process_wallet

WALLET = "watched-wallet"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

def balance(mint, value):
    return {"owner": WALLET, "mint": mint, "uiTokenAmount": {"uiAmountString": str(value)}}

class PublicRPCTests(unittest.TestCase):
    def test_stablecoin_funded_buy(self):
        tx = {"meta":{"err":None,"preTokenBalances":[balance(USDC,100)],
                      "postTokenBalances":[balance(USDC,75),balance("TOKEN",1000)]}}
        buy = classify_swap(tx,WALLET)
        self.assertEqual(buy["estimated_spend_usd"],25)
        self.assertEqual(buy["token_mint"],"TOKEN")

    def test_airdrop_not_a_buy(self):
        tx = {"meta":{"err":None,"preTokenBalances":[],
                      "postTokenBalances":[balance("TOKEN",1000)]}}
        self.assertIsNone(classify_swap(tx,WALLET))

    def test_failed_transaction_not_a_buy(self):
        self.assertIsNone(classify_swap({"meta":{"err":{"InstructionError":[0,"Fail"]}}},WALLET))

    def test_baseline_never_replays_old_transactions(self):
        class Trader: wallet = WALLET
        state={"seen_signatures":[],"initialized":{}}
        with patch("SmartMoneyMonitor.solana_public_rpc_v23.recent_signatures",return_value=[{"signature":"old"}]):
            n=process_wallet(Trader(),state,lambda *args: self.fail("Unexpected trade"),lambda s: None)
        self.assertEqual(n,0)
        self.assertIn("old",state["seen_signatures"])

if __name__ == "__main__":
    unittest.main()
