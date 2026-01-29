accounts = {}
transactionhistory = {}
def deposit(number,amount):
    if number not in accounts:
        return False
    else:
        accounts[number] = accounts[number] + amount
        transactionhistory[number] = f"${amount} added to account #{number}; " + transactionhistory[number]
        return True
def create(number):
    if number in accounts:
        return False
    else:
        accounts[number] = 0
        transactionhistory[number] = ""
        return True
def withdraw(number,amount):
    if amount > accounts[number] or number not in accounts:
        return False
    else:
        accounts[number] = accounts[number] - amount
        transactionhistory[number] = f"${amount} removed from account #{number}; " + transactionhistory[number]
        return True
def balance(number):
    if number not in accounts:
        return False
    else:
        return accounts[number]
def transfer(number1,number2, amount):
    if number1 not in accounts or number2 not in accounts or number1 == number2:
        return False
    else:
        accounts[number1] = accounts[number1] - amount
        accounts[number2] = accounts[number2] + amount
        transactionhistory[number1] = f"${amount} removed from account #{number1}; " + transactionhistory[number1]
        transactionhistory[number2] = f"${amount} added to account #{number2}; " + transactionhistory[number2]
        return True
def delete(number):
    if number not in accounts:
        return False
    else:
        del accounts[number]
        del transactionhistory[number]
        return True
def deleteall():
    accounts.clear()
    transactionhistory.clear()
    return True
def resetall():
    for key in accounts:
        accounts[key] = 0
    for key in transactionhistory:
        transactionhistory[key] = ""
    return True
def reset(number):
    if number not in accounts:
        return False
    else:
        accounts[number] = 0
        transactionhistory[number] = ""
        return True
def history(number):
    if number not in accounts:
        return False
    else:
        return transactionhistory[number]