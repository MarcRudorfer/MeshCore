from pathlib import Path
p=Path('examples/companion_radio/main.cpp')
s=p.read_text()

def mark(txt):
    return '#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "'+txt+'"); disp->endFrame(); }\n#endif\n'

gps='#if ENV_INCLUDE_GPS == 1\n  the_mesh.applyGpsPrefs();\n#endif\n'
ui='  ui_task.begin(disp, &sensors, the_mesh.getNodePrefs());  // still want to pass this in as dependency, as prefs might be moved\n'
boot='  board.onBootComplete();\n'
if gps not in s: raise SystemExit('GPS anchor missing')
if ui not in s: raise SystemExit('UI anchor missing')
if boot not in s: raise SystemExit('BOOT anchor missing')
s=s.replace(gps, mark('D13 GPS PRE')+gps+mark('D14 GPS POST'), 1)
s=s.replace(ui, mark('D15 UI PRE')+ui+mark('D16 UI POST'), 1)
s=s.replace(boot, mark('D17 BOOT PRE')+boot+mark('D18 BOOT POST'), 1)
p.write_text(s)
print('DIAG4Q: post-D12 markers applied')
