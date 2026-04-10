## 2024-05-24 - Prevent Client-Side Fee Manipulation
**Vulnerability:** The `collect_fee` function in `onchain_utils.py` accepted a `fee_percent` parameter, allowing potential client-side manipulation if the application allowed users to specify or pass this value through the frontend.
**Learning:** Security-critical constants, like protocol fee percentages, must be enforced server-side. Relying on an argument passed to a function that processes these fees opens the system up to manipulation.
**Prevention:** Hardcode or load such constants directly from a secure backend configuration (e.g., `config.py`) within the function that executes the sensitive logic, rather than accepting them as arguments.

## 2024-05-24 - Prevent Command Argument Injection in Subprocesses
**Vulnerability:** The `get_swap_quote` and `get_historical_kline` functions in `onchain_utils.py` directly passed user-controlled inputs to `subprocess.run` without validation, exposing the system to Command Argument Injection.
**Learning:** Passing unsanitized inputs as arguments to a subprocess, even without `shell=True`, can still lead to security risks if the arguments begin with hyphens (interpreted as flags) or contain unintended payload structures.
**Prevention:** Implement strict validation checks (like `is_safe_arg`) for all user-supplied data before passing it to `subprocess.run`, ensuring it conforms to expected formats and preventing argument injection.
## 2026-04-08 - Explicit Allowlist Validation for Subprocess Arguments

**Vulnerability:** While basic regex filtering prevented arbitrary character injections, it didn't prevent logically valid but unsupported tokens from being passed to `onchainos` via subprocess calls.
**Learning:** Defense in depth is required. Relying solely on character format validation is insufficient for command arguments; when possible, inputs should be checked against an explicit allowlist of supported values.
**Prevention:** For parameters like `token_in` and `token_out`, validate user input against `SUPPORTED_TOKENS` before executing the subprocess to prevent unwanted commands.

## 2026-04-07 - Information Leakage via Subprocess Exceptions
**Vulnerability:** The error handlers in `execute_swap` and `get_swap_quote` (`onchain_utils.py`) directly returned CLI output and `stderr` (e.g., `e.stderr` and `result.stdout`) on failure, which were subsequently rendered directly in the Streamlit UI, exposing internal system details, potential stack traces, or command structures to end-users.
**Learning:** Even if `subprocess` outputs are standard application errors, exposing raw CLI output directly to a web frontend creates an Information Disclosure vulnerability (leaking internals/stack traces) that can aid attackers.
**Prevention:** Always log detailed external command errors securely on the server console or log file, and return generic, sanitized error messages (e.g., "Swap execution failed on the node. Please check server logs.") to the caller or frontend.

## 2024-05-24 - Prevent Information Disclosure via Error Messages
**Vulnerability:** Raw exceptions, standard error output (`stderr`), and execution outputs (`stdout`) were being exposed to the caller or printed directly when `subprocess.run` calls failed or JSON decoding failed in `onchain_utils.py` (specifically in `execute_swap`, `get_swap_quote`, and `check_wallet_status`).
**Learning:** Returning or logging raw system error strings or stack traces exposes sensitive internal context, configuration details, or internal application state, creating an Information Disclosure vulnerability.
**Prevention:** Always catch explicit exceptions (e.g., `subprocess.CalledProcessError`, `json.JSONDecodeError`) and return or log sanitized, generic error messages to the frontend/callers to prevent internal state leakage.
