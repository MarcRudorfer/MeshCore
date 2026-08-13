from pathlib import Path
p=Path('examples/companion_radio/MyMesh.cpp')
s=p.read_text()
anchor='void MyMesh::onMessageRecv(const ContactInfo& from, uint8_t type, uint8_t* payload, size_t payload_len) {'
helper='''static bool diag4j_out4_onoff(const char* text, const char*& reply) {\n  if (strcmp(text, "LINK OUT4 ON") == 0) { pinMode(45, OUTPUT); digitalWrite(45, HIGH); reply = "LINK ACK OUT4 ON ISOLATED GPIO45"; return true; }\n  if (strcmp(text, "LINK OUT4 OFF") == 0) { pinMode(45, OUTPUT); digitalWrite(45, LOW); reply = "LINK ACK OUT4 OFF ISOLATED GPIO45"; return true; }\n  return false;\n}\n\n'''
if anchor not in s: raise SystemExit('handler anchor missing')
s=s.replace(anchor,helper+anchor,1)
old='''    // OUT4 deliberately has no REMOTE_GPIO_OUT4 macro, timer state, STATUS hook or boot init.\n    // The first command configures GPIO45 as OUTPUT and then drives it.\n    if (strcmp(text, "LINK OUT4 ON") == 0) {\n      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);\n      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, HIGH);\n      gpio_reply = "LINK ACK OUT4 ON ISOLATED GPIO45";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {\n      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);\n      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);\n      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";\n      gpio_command_recognized = true;\n    }\n'''
new='''    if (diag4j_out4_onoff(text, gpio_reply)) {\n      gpio_command_recognized = true;\n    }\n'''
if old not in s: raise SystemExit('OUT4 block missing')
s=s.replace(old,new,1)
p.write_text(s)
print('DIAG4J: OUT4 ON/OFF moved out of main parser')
