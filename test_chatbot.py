from app import handle_query

# Test Case 1: 'seats'
print('='*60)
print('Test Case 1: Query = "seats"')
print('='*60)
result = handle_query('seats')
print(result)
print()

# Test Case 2: 'strength'
print('='*60)
print('Test Case 2: Query = "strength"')
print('='*60)
result = handle_query('strength')
print(result)
print()

# Test Case 3: 'How many seats in computer science'
print('='*60)
print('Test Case 3: Query = "How many seats in computer science"')
print('='*60)
result = handle_query('How many seats in computer science')
print(result)
print()

# Test Case 4: 'no of seats'
print('='*60)
print('Test Case 4: Query = "no of seats"')
print('='*60)
result = handle_query('no of seats')
print(result)
