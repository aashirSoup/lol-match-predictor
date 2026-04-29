import json
import pprint
with open("data/raw/NA1_5541699314.json") as f:
    match = json.load(f)

print('main keys:' , match.keys())
print('\ninfo keys:')
pprint.pprint(match['info'].keys())
print("\nparticipant keys: ")
pprint.pprint(match['info']['participants'][0].keys())
print('\nteams keys: ')
pprint.pprint(match['info']['teams'][0].keys())
print("\nobjectives: ")
pprint.pprint(match['info']['teams'][0]['objectives'])
print('\nbans: ')
pprint.pprint(match['info']['teams'][0]['bans'])
