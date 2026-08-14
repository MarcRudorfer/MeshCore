from pathlib import Path
p=Path('examples/companion_radio/MyMesh.cpp')
s=p.read_text()
old='  addToOfflineQueue(out_frame, i);\n'
new='  // DIAG4U: skip addToOfflineQueue() for incoming contact messages\n'
# Replace only the first occurrence in queueMessage().
if old not in s: raise SystemExit('addToOfflineQueue anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('DIAG4U: incoming contact addToOfflineQueue skipped')
