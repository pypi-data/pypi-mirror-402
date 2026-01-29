# gamebanking

**gamebanking** is a Python module that makes coding game currency easier. It allows you to create accounts, deposit and withdraw currency, transfer money, track transaction history, and manage accounts.

## Functions

- `create(number)` - Creates a new account with the given number. Returns True if successful, False if the account already exists.
- `deposit(number, amount)` - Adds currency to the given account. Returns True if successful, False if the account does not exist. Logs the transaction in the account’s history.
- `withdraw(number, amount)` - Subtracts currency from the given account. Returns True if successful, False if the account does not exist or has insufficient funds. Logs the transaction in the account’s history.
- `balance(number)` - Returns the current balance of the given account. Returns False if the account does not exist.
- `transfer(number1, number2, amount)` - Moves currency from one account to another. Returns True if successful, False if accounts are invalid or the source account lacks funds. Both accounts’ histories are updated.
- `reset(number)` - Resets the balance of the given account to 0. Returns True if successful, False if the account does not exist.
- `resetall()` - Resets all accounts’ balances to 0.
- `delete(number)` - Deletes a single account. Returns True if successful, False if the account does not exist.
- `deleteall()` - Deletes all accounts.
- `history(number)` - Returns a list of all transactions for the given account. Returns an empty list if no transactions exist. Returns False if the account does not exist.

## Author

CorruptDragon24