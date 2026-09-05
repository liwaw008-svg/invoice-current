# Invoice Current

Invoice Current produces an advisory receivable eligibility record from three role-bound sources: invoice, delivery acknowledgement and debtor policy. Validators verify the exact decision, risk codes and all three content digests before state changes.

Eligible records can be marked settled by their owner; abandoned filed records can expire. The contract never transfers funds and does not claim to mutate an external registry. Run `python -m pytest -q` and `genvm-lint contract/invoice_current.py`.
