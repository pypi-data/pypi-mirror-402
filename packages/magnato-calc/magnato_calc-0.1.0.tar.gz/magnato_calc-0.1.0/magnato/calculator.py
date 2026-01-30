def add(a,b):
    """ This will return addition of two number """
    return a+b
def multiply(a,b):
    return a*b
def subtract(a,b):
    return a-b

def divide(a,b):
    if b==0:
        raise ValueError("Can't divide by zero")
    return a/b
def power(a,b):
    return a**b

def max(a,b,c):
    if a>b and a>c:
        return a
    elif b>a and a>c:
        return b
    else:
        return c
    
def min(a,b,c):
    if a<b and b<c:
        return a
    elif b<a and b<c:
        return b
    else: 
        return c
    

def average(a):
    if len(a)==0:
        return 0
    return sum(a)/len(a)
    