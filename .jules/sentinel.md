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

## 2024-05-18 - Information Disclosure via Subprocess Output
**Vulnerability:** Raw `stdout` and `stderr` payloads from `subprocess.run` were being returned directly in error handlers, potentially leaking sensitive execution details, CLI internals, or stack traces to callers (and the frontend UI).
**Learning:** `subprocess.CalledProcessError.stderr` and unparsed `subprocess.CompletedProcess.stdout` can contain system paths, execution arguments, or debug information that should not be visible to users.
**Prevention:** Catch specific exceptions (like `subprocess.CalledProcessError` or `json.JSONDecodeError`) and return sanitized, generic error strings instead of passing raw underlying logs.

## 2026-04-15 - Prevent Denial of Service via Subprocess Thread Exhaustion
**Vulnerability:** Synchronous `subprocess.run` calls to external CLI tools (e.g., `onchainos`) were made without a `timeout` parameter. If the external process hangs or takes too long, it indefinitely blocks the thread (and Streamlit's UI thread), leading to a Denial of Service (DoS) through thread exhaustion.
**Learning:** Never assume external processes or CLIs will return promptly. Always design for failure by explicitly defining how long an operation is allowed to run before failing securely.
**Prevention:** Enforce explicit `timeout` parameters on all synchronous `subprocess.run` calls (e.g., `timeout=15`). Always catch `subprocess.TimeoutExpired` alongside standard process errors to fail gracefully and return sanitized messages to the frontend.
## 2026-04-09 - Prevent Denial of Service via Subprocess Thread Exhaustion
**Vulnerability:** Multiple synchronous `subprocess.run` calls in `onchain_utils.py` (e.g., `execute_swap`, `get_historical_kline`) did not enforce execution timeouts. If the `onchainos` CLI process hangs or delays indefinitely, the calling Python thread will block forever, leading to thread exhaustion and a Denial of Service (DoS) condition in the main application.
**Learning:** Security and resilience require that all external system calls or subprocess invocations have strict time boundaries to prevent resource starvation.
**Prevention:** Enforce explicit `timeout` parameters on all synchronous `subprocess.run` calls, and specifically catch and gracefully handle `subprocess.TimeoutExpired` exceptions alongside existing error handling.
## 2026-04-09 - Prevent Denial of Service (DoS) via Unbounded Subprocess Calls
**Vulnerability:** Calls to external CLI tools (`onchainos`) via `subprocess.run` lacked a `timeout` parameter, allowing a hanging, unresponsive, or maliciously delayed node process to indefinitely block the application's execution thread, creating a Denial of Service (DoS) risk.
**Learning:** Any blocking synchronous operation that communicates with external systems (including local CLIs or network requests via subprocesses) without a strict bound can lead to thread exhaustion and complete application unavailability.
**Prevention:** Always enforce a strict `timeout` parameter on all `subprocess.run` calls (e.g., `timeout=15`) and gracefully handle the resulting `subprocess.TimeoutExpired` exception to ensure system resilience.

## 2026-04-18 - Prevent Insecure File Generation and Disk Exhaustion
**Vulnerability:** The application previously generated and overwritten a single static file (`dca_simulation_chart.png`) during simulations. Generating per-request files with UUIDs prevents race conditions but creates a Denial of Service (DoS) vulnerability via disk exhaustion if the files are not explicitly cleaned up.
**Learning:** Writing ephemeral artifacts to disk creates lifecycle management complexity and risks resource exhaustion if cleanup fails or is omitted.
**Prevention:** Always prefer using in-memory buffers (like `io.BytesIO`) instead of disk storage for temporary artifact generation (like images or charts) that are only needed for immediate UI rendering or data transmission.

## 2026-04-19 - Prevent Information Disclosure via Unparsed CLI JSON Output
**Vulnerability:** The `execute_swap` function in `onchain_utils.py` returned the raw, unparsed JSON output directly from the `onchainos swap execute` CLI command. This exposes all fields (including potentially sensitive tokens, keys, or certs returned by real node implementations) to the caller and ultimately to the Streamlit UI via `st.code()`.
**Learning:** Returning raw JSON payloads from internal tools or APIs creates an Information Disclosure vulnerability because the underlying tool's schema may include sensitive fields (e.g., `accessToken`, `apiKey`) not intended for the end user.
**Prevention:** Always parse the JSON response from internal CLI commands or APIs and construct a new, sanitized dictionary containing strictly only the required, safe fields (e.g., `txHash`) before returning the result to the caller or frontend.
