#!/usr/bin/env python3
import json

# Load database
with open('database/combined_videos.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check for duplicates
codes = [v['code'] for v in data]
print(f'Total videos: {len(data)}')
print(f'Unique codes: {len(set(codes))}')

duplicates = [c for c in codes if codes.count(c) > 1]
if duplicates:
    print(f'\nDuplicates in database:')
    for code in set(duplicates):
        count = codes.count(code)
        print(f'  {code}: {count} copies')
else:
    print('\n✅ No duplicates in database!')

# Check StreamWish hosting
print(f'\nStreamWish uploads:')
streamwish_codes = []
for v in data:
    if 'streamwish' in v.get('hosting', {}):
        streamwish_codes.append(v['code'])

print(f'  Total: {len(streamwish_codes)}')
print(f'  Unique: {len(set(streamwish_codes))}')

if len(streamwish_codes) != len(set(streamwish_codes)):
    print(f'  ⚠️ Duplicates detected!')
else:
    print(f'  ✅ No duplicates!')
