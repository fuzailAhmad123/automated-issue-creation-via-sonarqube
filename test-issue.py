
# import hashlib

def faulty_exception_handling():
    try:
        result = 10 / 0 
    except ValueError:  
        print("Handled error incorrectly")

faulty_exception_handling()