import random
def random_string(n):
	return ''.join([chr(random.randint(33,127)) for x in range(n)])