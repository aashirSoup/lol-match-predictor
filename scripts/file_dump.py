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

# p = match['info']['participants'][0]
# print(p['championId'], p['championName'], p['teamPosition'], p['teamId'])

# p2 = match['info']['participants'][5]
# print(p2['championId'], p2['championName'], p2['teamPosition'], p2['teamId'])

for p in match['info']['participants']:
    print(p['teamId'], p['teamPosition'], p['championName'])

print(match['info']['teams'][0]['win'], match['info']['teams'][0]['teamId'])
print(match['info']['teams'][1]['win'], match['info']['teams'][1]['teamId'])