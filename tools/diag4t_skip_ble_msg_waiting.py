from pathlib import Path
p=Path('examples/companion_radio/MyMesh.cpp')
s=p.read_text()
old='''  if (_serial->isConnected()) {\n    uint8_t frame[1];\n    frame[0] = PUSH_CODE_MSG_WAITING; // send push 'tickle'\n    _serial->writeFrame(frame, 1);\n  }\n\n#ifdef DISPLAY_CLASS\n'''
new='''  if (_serial->isConnected()) {\n    // DIAG4T: deliberately skip PUSH_CODE_MSG_WAITING to isolate BLE writeFrame crash\n  }\n\n#ifdef DISPLAY_CLASS\n'''
if old not in s: raise SystemExit('message waiting block anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('DIAG4T: skipped BLE PUSH_CODE_MSG_WAITING writeFrame for received contact messages')
