# Exercice 1
a = 10
b = 5.0
c = "Ciao"
d = "Bocconi!"
e = [25,57,34,"Ciao",4.56,1+2j]
f = {1,2,3,3,3}

# Exercice 2
print(type(a))
print(type(b))
print(type(c))
print(type(d))
print(type(e))
print(type(f))

# Exercice 3
i = complex(a, b)

# Exercice 4
cb = c + " " + d

# Exercice 5
e.sort()

# Exercice 6
e.append("Ciao")
e.remove("Ciao")
print(e.count("Ciao"))
e.pop()
print(e.count("Ciao"))

# Exercice 7
h = set(e)

# Exercice 8
print(f)

# Exercice 9
t = "The wonderful world of Python!"
print(t[0:4])
print(t[-1])
print(t[t.find("Python"):t.find("!")])
print(t[::2])
print(t[::-1])

# Exercice 10
print(t.find("Python") > -1)
print(t.index("Python") > -1)

# Exercice 11
print("%s" %(t))

# Exercice 12
x = [[1,2,3],[4,5,6],[7,8,9]]

# Exercice 13
import copy as cp
print(x[1][2])
print(x[1:3])
y = x
y[0][0] = 5
print(x)
print(y)
z = cp.deepcopy(x)
z[0][0] = 10
print(x)
print(z)