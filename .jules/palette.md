## 2024-05-18 - Portfolio Split Ambiguity
**Learning:** Users can easily confuse whether a numerical input for a distributed action refers to the "total amount" or the "amount per item". Without explicit clarification, a user might accidentally invest N times their intended amount when splitting a portfolio.
**Action:** Always provide explicit mathematical or logical clarifications in tooltips (e.g., `help="..."`) for inputs that involve distributions, splits, or multiplications across multiple selections.
## 2026-04-13 - Explicit Mathematical Clarifications in Tooltips
**Learning:** When users must input values that are distributed across multiple selections (like portfolio splits), they often become confused about whether the input represents the *total* or the *amount per item*.
**Action:** Always provide explicit mathematical examples in the `help` parameter tooltip (e.g., '100 split across 2 = 50 each') to remove ambiguity.
