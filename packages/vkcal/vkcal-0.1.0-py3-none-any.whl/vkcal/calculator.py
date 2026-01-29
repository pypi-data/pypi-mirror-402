def add(a,b):
    """ This is retrun addition of two number """
    return a+b

def substract(a,b):
    """ This is retrun addition of two number """
    return a-b

def multiply(a,b):
    """ This is retrun addition of two number """
    return a*b

def divide(a,b):
    """ This is retrun addition of two number """
    if b==0:
        raise ValueError("cannot divide by Zero")
    return a/b  

def power(a,b):
    return a**b