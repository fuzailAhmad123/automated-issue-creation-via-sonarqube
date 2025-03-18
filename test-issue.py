
import hashlib

def weak_hashing(password):
    hash_value = hashlib.md5(password.encode()).hexdigest() 
    return hash_value

def division_by_zero(user_input):
    return 10 / int(user_input)

division_by_zero("0")
print(weak_hashing("password123"))