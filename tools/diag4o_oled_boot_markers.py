from pathlib import Path

p = Path('examples/companion_radio/main.cpp')
s = p.read_text()

# Helper macro local to setup(): overwrite the OLED with a short boot-stage marker.
needle = '''void setup() {\n  Serial.begin(115200);\n\n  board.begin();\n'''
repl = '''void setup() {\n  Serial.begin(115200);\n\n  board.begin();\n'''
if needle not in s:
    raise SystemExit('setup anchor missing')
# no change here; marker helper uses the existing disp pointer below

# Replace the initial Loading text so we know display init itself succeeded.
s = s.replace('disp->drawTextCentered(disp->width() / 2, 28, "Loading...");',
              'disp->drawTextCentered(disp->width() / 2, 28, "D0 DISPLAY OK");', 1)

# Show RADIO before and after radio_init, including failure.
old = '  if (!radio_init()) { halt(); }\n\n  fast_rng.begin(radio_driver.getRngSeed());\n'
new = '''#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D1 RADIO INIT"); disp->endFrame(); }\n#endif\n  if (!radio_init()) {\n#ifdef DISPLAY_CLASS\n    if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "ERR RADIO"); disp->endFrame(); }\n#endif\n    halt();\n  }\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D2 RADIO OK"); disp->endFrame(); }\n#endif\n\n  fast_rng.begin(radio_driver.getRngSeed());\n'''
if old not in s:
    raise SystemExit('radio anchor missing')
s = s.replace(old, new, 1)

# ESP32 path: mark each major initialization boundary.
old = '''#elif defined(ESP32)\n  SPIFFS.begin(true);\n  store.begin();\n  the_mesh.begin(\n'''
new = '''#elif defined(ESP32)\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D3 SPIFFS"); disp->endFrame(); }\n#endif\n  SPIFFS.begin(true);\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D4 STORE"); disp->endFrame(); }\n#endif\n  store.begin();\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D5 MESH BEGIN"); disp->endFrame(); }\n#endif\n  the_mesh.begin(\n'''
if old not in s:
    raise SystemExit('ESP32 init anchor missing')
s = s.replace(old, new, 1)

old = '''  );\n\n#ifdef WIFI_SSID\n'''
new = '''  );\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D6 MESH OK"); disp->endFrame(); }\n#endif\n\n#ifdef WIFI_SSID\n'''
# There are multiple ");\n\n#ifdef WIFI_SSID" possibilities; target last/ESP32 occurrence.
pos = s.rfind(old)
if pos < 0:
    raise SystemExit('mesh end anchor missing')
s = s[:pos] + new + s[pos+len(old):]

old = '''#elif defined(BLE_PIN_CODE)\n  serial_interface.begin(BLE_NAME_PREFIX, the_mesh.getNodePrefs()->node_name, the_mesh.getBLEPin());\n#elif defined(SERIAL_RX)\n'''
new = '''#elif defined(BLE_PIN_CODE)\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D7 BLE BEGIN"); disp->endFrame(); }\n#endif\n  serial_interface.begin(BLE_NAME_PREFIX, the_mesh.getNodePrefs()->node_name, the_mesh.getBLEPin());\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D8 BLE OK"); disp->endFrame(); }\n#endif\n#elif defined(SERIAL_RX)\n'''
if old not in s:
    raise SystemExit('ESP32 BLE anchor missing')
s = s.replace(old, new, 1)

old = '''  the_mesh.startInterface(serial_interface);\n#else\n  #error "need to define filesystem"\n#endif\n\n  sensors.begin();\n'''
new = '''#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D9 IFACE"); disp->endFrame(); }\n#endif\n  the_mesh.startInterface(serial_interface);\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D10 IFACE OK"); disp->endFrame(); }\n#endif\n#else\n  #error "need to define filesystem"\n#endif\n\n#ifdef DISPLAY_CLASS\n  if (disp) { disp->startFrame(); disp->drawTextCentered(disp->width()/2, 28, "D11 SENSORS"); disp->endFrame(); }\n#endif\n  sensors.begin();\n'''
# target the ESP32 occurrence, which is the last before filesystem error
pos = s.rfind(old)
if pos < 0:
    raise SystemExit('interface anchor missing')
s = s[:pos] + new + s[pos+len(old):]

p.write_text(s)
print('DIAG4O OLED boot markers applied: D0..D11')
