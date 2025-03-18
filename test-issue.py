import os

# 1. CRITICAL: OS Command Injection
def command_injection(user_input):
    os.system("rm -rf " + user_input) 

# 2. MAJOR: Hardcoded Credentials
def hardcoded_password():
    password = "SuperSecret123" 
    print("Using password:", password)

# 3. BLOCKER: Divide by Zero
def division_by_zero(user_input):
    return 10 / int(user_input) 