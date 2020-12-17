from random import choice, randint
digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

sound = ["A", "E", "I", "O", "U"]
duplicative = ["O", "E", "M", "N", "S"]

specials = ["P", "S", "C", "G", "T"]

empty = letters.copy()
for s in sound:
	empty.remove(s)

def getName(length):
	name = ""
	name += choice(letters)
	for i in range(length-1):
		if name[-1] in specials:
			if randint(0,4) == 0:
				name += "H"
				continue
		if len(name) > 1:
			if name[-1] in empty and name[-2] in empty:
				name += choice(sound)
				continue
			if name[-1] in sound and name[-2] in sound:
				name += choice(empty)
				continue
		if name[-1] in empty:
			if randint(0,2) >= 1:
				name += choice(empty)
			else:
				name += choice(sound)
		else:
			name += choice(letters)
	return name
