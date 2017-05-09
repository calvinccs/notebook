# Exercice 1
def isPerfectNumber(n):
    sum = 0
    for x in range(1, n):
        if n % x == 0:
            sum += x
    return sum == n
print(isPerfectNumber(6))



# Exercice 2
def isPalindrome(string):
	left_pos = 0
	right_pos = len(string) - 1

	while right_pos >= left_pos:
		if not string[left_pos] == string[right_pos]:
			return False
		left_pos += 1
		right_pos -= 1
	return True
print(isPalindrome('sugus'))




# Exercice 4
import numpy as np
 
#create a list of play options
t = ["Rock", "Paper", "Scissors"]
 
#assign a random play to the computer
computer = np.random.choice(t)
 
while True:
    player = input("Rock, Paper, Scissors? ")
    if player == computer:
        print("Tie!")
    elif player == "Rock":
        if computer == "Paper":
            print("You lose!", computer, "covers", player)
        else:
            print("You win!", player, "smashes", computer)
    elif player == "Paper":
        if computer == "Scissors":
            print("You lose!", computer, "cut", player)
        else:
            print("You win!", player, "covers", computer)
    elif player == "Scissors":
        if computer == "Rock":
            print("You lose...", computer, "smashes", player)
        else:
            print("You win!", player, "cut", computer)
    elif player == "quit":
        print("Good bye!")
        break
    else:
        print("That's not a valid play. Check your spelling!")
    computer = t[np.random.randint(0,2)]