# Sentinel Security Journal

## 2026-04-07 - REQUIRE_TESTNET Safe-Mode Bypass via UI

**Vulnerability:** `REQUIRE_TESTNET=true` in `.env` was intended to lock execution to testnet and prevent accidental mainnet swaps. However, in `app.py`, the flag was only checked inside the `if is_testnet:` branch. When the user selected "X Layer Mainnet (196)" in the sidebar radio, the `else` branch ran unconditionally setting `chain_id = 196`, completely bypassing the safe-mode guard. Real funds could be spent even with safe mode enabled.

**Learning:** Boolean "safe mode" flags must be checked FIRST — before any UI-driven branching — to avoid branches that bypass them. The pattern `if REQUIRE_TESTNET: enforce_safe_mode() elif is_testnet: ... else: ...` ensures the guard cannot be skipped.

**Prevention:** In any DeFi/financial app, environment-level safety flags (testnet locks, kill switches) must take unconditional precedence over user UI inputs. Never check the safety flag only inside the "happy path" branch.
