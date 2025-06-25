import random

def generate_random_otp(length=7):
    otp = ''.join([str(random.randint(0,9)) for i in range(7)])
    return otp

print(generate_random_otp())