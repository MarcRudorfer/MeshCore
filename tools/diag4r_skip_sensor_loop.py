from pathlib import Path
p=Path('examples/companion_radio/main.cpp')
s=p.read_text()
old='  sensors.loop();\n'
new='  // DIAG4R: sensors.loop() intentionally skipped together with sensors.begin()\n'
if old not in s: raise SystemExit('sensors.loop anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('DIAG4R: sensors.loop skipped')
