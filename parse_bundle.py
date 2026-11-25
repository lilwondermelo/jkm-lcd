#!/usr/bin/env python3
"""Parse .NET single-file bundle manifest backwards from EOF."""
import sys, json
path = sys.argv[1]
data = open(path, 'rb').read()
pos = len(data)
entries = []
while pos > 0:
    found = None
    for plen in range(1, 256):
        start = pos - plen
        if start < 26 or data[start-1] != plen:
            continue
        p = data[start:pos]
        if not all(32 <= b < 127 for b in p):
            continue
        hdr = start - 26
        if hdr < 0:
            continue
        typ = data[hdr+24]
        if typ not in (0,1,2,3,4,5) or data[hdr+25] != plen:
            continue
        off = int.from_bytes(data[hdr:hdr+8], 'little')
        size = int.from_bytes(data[hdr+8:hdr+16], 'little')
        comp = int.from_bytes(data[hdr+16:hdr+24], 'little')
        if 0 <= off <= len(data) and 0 <= size <= len(data) and 0 <= comp <= size:
            found = (hdr, off, size, comp, typ, p.decode('ascii'))
            break
    if not found:
        break
    entries.append(found)
    pos = found[0]
entries.reverse()
print('entries:', len(entries), 'header_end:', pos)
for hdr, off, size, comp, typ, name in entries:
    if any(k in name.lower() for k in ('fancondrol', 'hidsharp', 'librehardware', 'deps.json', 'runtimeconfig')):
        print(f'{hdr:>10} off={off:>10} size={size:>9} comp={comp:>9} type={typ} {name}')
json.dump(entries, open('/tmp/opencode/bundle_entries.json','w'))
