#!/usr/bin/env python3
import sys, os
path = sys.argv[1]
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)
data = open(path, 'rb').read()
n = len(data)
found = []
for i in range(0, n - 0x40):
    if data[i:i+2] == b'MZ':
        e = int.from_bytes(data[i+0x3c:i+0x40], 'little')
        if 0 < e < 0x1000 and data[i+e:i+e+4] == b'PE\0\0':
            found.append(i)
print('found', len(found))
for idx, off in enumerate(found):
    # determine PE size: use next PE offset or end
    end = found[idx+1] if idx+1 < len(found) else n
    if end - off > 200*1024*1024:
        end = min(n, off + 200*1024*1024)
    chunk = data[off:end]
    p = os.path.join(outdir, f'pe_{idx}_{off}.bin')
    open(p, 'wb').write(chunk)
    print(idx, off, len(chunk), chunk[:2].hex())
