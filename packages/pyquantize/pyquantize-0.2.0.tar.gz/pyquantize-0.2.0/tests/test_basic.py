from pyquantize import quantize
from math import copysign

def is_neg_zero(x):
	return x == 0 and copysign(1, x) == -1

def is_pos_zero(x):
	return x == 0 and copysign(1, x) == 1

test_set = [-1.5, -1.25, -1, -0.75, -0.5, -0.25, -0.0, 0, 0.25, 0.5, 0.75, 1, 1.25, 1.5]
modes = ['near', 'far', 'floor', 'ceil', 'toward', 'away', 'even', 'odd', 'threshold', 'alternate', 'random', 'stochastic']

def test_defaults():
	expects = [-2, -1, -1, -1, -0.0, -0.0, -0.0, 0, 0, 0, 1, 1, 1, 2]
	results = [quantize(num) for num in test_set]

	for expect, result in zip(expects,results):
		assert result == expect
	
	for result in results[4:7]:
		assert is_neg_zero(result)

def test_signed_zeroes():
	assert copysign(1, quantize( 0.0)) ==  1
	assert copysign(1, quantize(-0.0)) == -1

def test_floor():
	#test_set = [-1.5, -1.25, -1, -0.75, -0.5, -0.25, -0.0, 0, 0.25, 0.5, 0.75, 1, 1.25, 1.5]
	expects   = [-2  , -2   , -1, -1   , -1  , -1   , -0.0, 0, 0   , 0  , 0   , 1, 1   , 1]
	results = [quantize(num, mode='floor', tie='floor') for num in test_set]

	for result, expect in zip(results, expects):
		assert result == expect
	
def test_ceil():
	expects = [-1, -1, -1, -0.0, -0.0, -0.0, -0.0, 0.0, 1, 1, 1, 1, 2, 2]
	results = [quantize(num, mode='ceil', tie='ceil') for num in test_set]

	for result, expect in zip(results, expects):
		assert result == expect
	
def test_toward():
	expects = [-1, -1, -1, -0.0, -0.0, -0.0, -0.0, 0, 0, 0, 0, 1, 1, 1]
	results = [quantize(num, mode='toward', tie='toward') for num in test_set]

	for result, expect in zip(results, expects):
		assert result == expect

def test_away():
	expects = [-2, -2, -1, -1, -1, -1, -0.0, 0, 1, 1, 1, 1, 2, 2]
	results = [quantize(num, mode='away', tie='away') for num in test_set]

	for result, expect in zip(results, expects):
		assert result == expect

def test_threshold():
	#test_set = [-1.5, -1.25, -1, -0.75, -0.5, -0.25, -0.0, 0, 0.25, 0.5, 0.75, 1, 1.25, 1.5]
	expects   = [-2  , -1   , -1, -1   , -0.0, -0.0 , -0.0, 0, 0.0 , 0.0, 1   , 1, 1   , 2]

	results = [quantize(num, mode='threshold', tie='even') for num in test_set]

	for result, expect in zip(results, expects):
		assert result == expect

def test_alternate():
	from statistics import mean
	
	things = [quantize(0.8, mode='alternate', tie='alternate') for i in range(10000)]

	avg = mean(things)

	assert 0 < avg < 1
	assert 0.4 < avg < 0.6
	assert 0.49 < avg < 0.51
	assert avg == 0.5
	assert sum(things[0::2]) == 0
	assert sum(things[1::2]) == 5000

def test_random():
	from statistics import mean

	things = [quantize(0.8, mode='random', tie='random') for i in range(10000)]

	avg = mean(things)

	assert 0 < avg < 1
	assert 0.25 < avg < 0.75

def test_stochastic():
	from statistics import mean
	
	things = [quantize(0.8, mode='stochastic', tie='random') for i in range(10000)]

	avg = mean(things)

	assert 0 < avg < 1
	assert 0.6 < avg < 1
"""
def test_alternate_mode():
	from statistics import mean
	mode = 'alternate'
	quantize.alternate_last = False

	assert quantize(-1.5 , mode=mode, tie=tie) == -2
	assert quantize(-1.25, mode=mode, tie=tie) == -1
	assert quantize(-1   , mode=mode, tie=tie) == -1
	assert quantize(-0.75, mode=mode, tie=tie) == -1
	assert quantize(-0.5 , mode=mode, tie=tie) == -0.0
	assert quantize(-0.25, mode=mode, tie=tie) == -0.0
	assert quantize(-0.0 , mode=mode, tie=tie) == -0.0
	assert quantize( 0.0 , mode=mode, tie=tie) ==  0.0
	assert quantize( 0.25, mode=mode, tie=tie) ==  0.0
	assert quantize( 0.5 , mode=mode, tie=tie) ==  0.0
	assert quantize( 0.75, mode=mode, tie=tie) ==  1
	assert quantize( 1   , mode=mode, tie=tie) ==  1
	assert quantize( 1.25, mode=mode, tie=tie) ==  1
	assert quantize( 1.5 , mode=mode, tie=tie) ==  2

	quantize.alternate_last = False
	mode = 'alternate'

	things = [quantize(0.8, mode=mode, tie=tie) for i in range(10000)]

	avg = mean(things)

	assert 0 < avg < 1
	assert 0.4 < avg < 0.6
	assert 0.49 < avg < 0.51
	assert avg == 0.5
	assert sum(things[0::2]) == 0
	assert sum(things[1::2]) == 5000

def test_random_mode():
	mode = 'random'
	assert quantize(-1.5 , mode=mode, tie=tie) in [-2, -1]
	assert quantize(-1.25, mode=mode, tie=tie) == -1
	assert quantize(-1   , mode=mode, tie=tie) == -1
	assert quantize(-0.75, mode=mode, tie=tie) == -1
	assert quantize(-0.5 , mode=mode, tie=tie) in [-1, -0.0]
	assert quantize(-0.25, mode=mode, tie=tie) == -0.0
	assert quantize(-0.0 , mode=mode, tie=tie) == -0.0
	assert quantize( 0.0 , mode=mode, tie=tie) ==  0.0
	assert quantize( 0.25, mode=mode, tie=tie) ==  0.0
	assert quantize( 0.5 , mode=mode, tie=tie) in [0, 1]
	assert quantize( 0.75, mode=mode, tie=tie) ==  1
	assert quantize( 1   , mode=mode, tie=tie) ==  1
	assert quantize( 1.25, mode=mode, tie=tie) ==  1
	assert quantize( 1.5 , mode=mode, tie=tie) in [1, 2]

def test_stochastic_mode():
	mode = 'stochastic'
	tie = 'random'
	assert quantize(-1.5 , mode=mode, tie=tie) in [-2, -1]
	assert quantize(-1.25, mode=mode, tie=tie) == -1
	assert quantize(-1   , mode=mode, tie=tie) == -1
	assert quantize(-0.75, mode=mode, tie=tie) == -1
	assert quantize(-0.5 , mode=mode, tie=tie) in [-1, -0.0]
	assert quantize(-0.25, mode=mode, tie=tie) == -0.0
	assert quantize(-0.0 , mode=mode, tie=tie) == -0.0
	assert quantize( 0.0 , mode=mode, tie=tie) ==  0.0
	assert quantize( 0.25, mode=mode, tie=tie) ==  0.0
	assert quantize( 0.5 , mode=mode, tie=tie) in [0, 1]
	assert quantize( 0.75, mode=mode, tie=tie) ==  1
	assert quantize( 1   , mode=mode, tie=tie) ==  1
	assert quantize( 1.25, mode=mode, tie=tie) ==  1
	assert quantize( 1.5 , mode=mode, tie=tie) in [1, 2]
"""
