## 2024-05-24 - Prevent Client-Side Fee Manipulation
**Vulnerability:** The `collect_fee` function in `onchain_utils.py` accepted a `fee_percent` parameter, allowing potential client-side manipulation if the application allowed users to specify or pass this value through the frontend.
**Learning:** Security-critical constants, like protocol fee percentages, must be enforced server-side. Relying on an argument passed to a function that processes these fees opens the system up to manipulation.
**Prevention:** Hardcode or load such constants directly from a secure backend configuration (e.g., `config.py`) within the function that executes the sensitive logic, rather than accepting them as arguments.

## 2024-05-24 - Prevent Command Argument Injection in Subprocesses
**Vulnerability:** The `get_swap_quote` and `get_historical_kline` functions in `onchain_utils.py` directly passed user-controlled inputs to `subprocess.run` without validation, exposing the system to Command Argument Injection.
**Learning:** Passing unsanitized inputs as arguments to a subprocess, even without `shell=True`, can still lead to security risks if the arguments begin with hyphens (interpreted as flags) or contain unintended payload structures.
**Prevention:** Implement strict validation checks (like `is_safe_arg`) for all user-supplied data before passing it to `subprocess.run`, ensuring it conforms to expected formats and preventing argument injection.