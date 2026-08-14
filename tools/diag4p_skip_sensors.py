from pathlib import Path
p=Path('examples/companion_radio/main.cpp')
s=p.read_text()
old='  sensors.begin();\n'
new='''  // DIAG4P: sensors.begin() intentionally skipped to isolate reboot at D11\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D12 SKIP SENS OK"); disp->endFrame(); }\n#endif\n'''
if old not in s: raise SystemExit('sensors.begin anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('DIAG4P: sensors.begin skipped')
