accounts = {}
def deposit(number,amount):
    if number not in accounts:
        return False
    else:
        accounts[number] = accounts[number] + amount
        return True
def create(number):
    if number in accounts:
        return False
    else:
        accounts[number] = 0
        return True
def withdraw(number,amount):
    if amount > accounts[number] or number not in accounts:
        return False
    else:
        accounts[number] = accounts[number] - amount
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
        return True
def delete(number):
    if number not in accounts:
        return False
    else:
        del accounts[number]
        return True
def deleteall():
    accounts.clear()
    return True
def resetall():
    for key in accounts:
        accounts[key] = 0
    return True
def reset(number):
    if number not in accounts:
        return False
    else:
        accounts[number] = 0
        return True