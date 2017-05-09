import numpy as np

# Exercice 1
a = np.random.randn(10)
for x in a:
    if (x >= 0):
        print(x)
        
# Exercice 2
t = 0
p = 100
r = 0.15

while p < 200:
    t += 1
    p += r*p
    print("Time %s: Population = %.2f" %(t, p))
    
# Exercice 3
x = np.random.randn()
y = np.random.randn()

print("%.2f vs %.2f" %(x,y))
if x < 0 and y < 0:
    print("Both negatives")
elif x > 0 and y > 0:
    print("Both positives")
else:
    print("Different signs")
    
# Exercice 4
T = 5000
omega = 0.005
alpha = 0.15
beta = 0.8

e = np.random.randn(T)
x = np.zeros(T)
s = np.ones(T)

for t in range(1, T):
    s[t] = omega + alpha*x[t-1]**2 + beta*s[t-1]
    x[t] = s[t]*e[t]
    print("%d: %.2f - %.2f" %(t, s[t], x[t]))

print(s)
print(x)