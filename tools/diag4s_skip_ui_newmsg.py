from pathlib import Path
p=Path('examples/companion_radio/MyMesh.cpp')
s=p.read_text()
old='''  if (should_display && _ui) {\n    _ui->newMsg(path_len, from.name, text, offline_queue_len);\n    if (!_serial->isConnected()) {\n      _ui->notify(UIEventType::contactMessage);\n    }\n  }\n'''
new='''  if (should_display && _ui) {\n    // DIAG4S: skip UI newMsg() to isolate reboot on incoming text message\n    if (!_serial->isConnected()) {\n      _ui->notify(UIEventType::contactMessage);\n    }\n  }\n'''
if old not in s: raise SystemExit('UI newMsg block anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('DIAG4S: UI newMsg skipped for contact messages')
