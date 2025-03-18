import os

def insecure_function(user_input):
    # Security issue: Using eval() with untrusted input
    return eval(user_input)  

def unused_function():
    # Code Smell: Unused function
    pass

def hardcoded_secret():
    # Security issue: Hardcoded credentials
    api_key = "12345-ABCDE-SECRET"
    return api_key

def duplicate_code():
    # Code Smell: Duplicate logic
    x = 5
    y = 10
    sum1 = x + y

    a = 5
    b = 10
    sum2 = a + b  # Duplicate logic

    return sum1, sum2

def resource_leak():
    # Bug: File opened but not closed properly
    file = open("example.txt", "w")
    file.write("Hello, world!")  # Forgot to close the file

def division_by_zero():
    # Bug: Potential division by zero
    num = 10
    denom = 0
    return num / denom  # This will crash