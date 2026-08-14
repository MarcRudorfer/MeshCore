from pathlib import Path
p=Path('examples/companion_radio/main.cpp')
s=p.read_text()
old='''#if ENV_INCLUDE_GPS == 1\n  the_mesh.applyGpsPrefs();\n#endif\n\n#ifdef DISPLAY_CLASS\n  ui_task.begin(disp, &sensors, the_mesh.getNodePrefs());  // still want to pass this in as dependency, as prefs may be moved\n#endif\n\n  board.onBootComplete();\n'''
new='''#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D13 GPS PRE"); disp->endFrame(); }\n#endif\n#if ENV_INCLUDE_GPS == 1\n  the_mesh.applyGpsPrefs();\n#endif\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D14 GPS POST"); disp->endFrame(); }\n#endif\n\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D15 UI PRE"); disp->endFrame(); }\n  ui_task.begin(disp, &sensors, the_mesh.getNodePrefs());  // still want to pass this in as dependency, as prefs may be moved\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D16 UI POST"); disp->endFrame(); }\n#endif\n\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D17 BOOT PRE"); disp->endFrame(); }\n#endif\n  board.onBootComplete();\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D18 BOOT POST"); disp->endFrame(); }\n#endif\n'''
if old not in s: raise SystemExit('post-sensor block anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('DIAG4Q: post-sensor boot markers D13..D18 added')
