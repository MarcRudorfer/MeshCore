from pathlib import Path
p=Path('examples/companion_radio/MyMesh.cpp')
s=p.read_text()

anchor='  bool gpio_command_recognized = false;\n\n'
helper='''  auto diag4l_out4 = [&](const char* cmd) -> bool {\n    if (strcmp(cmd, "LINK OUT4 ON") == 0) {\n      gpio_link_out4_expiry = 0; pinMode(45, OUTPUT); digitalWrite(45, HIGH);\n      gpio_reply = "LINK ACK OUT4 ON ISOLATED GPIO45"; return true;\n    }\n    if (strcmp(cmd, "LINK OUT4 OFF") == 0) {\n      gpio_link_out4_expiry = 0; pinMode(45, OUTPUT); digitalWrite(45, LOW);\n      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45"; return true;\n    }\n    if (strcmp(cmd, "LINK OUT4 PULSE") == 0) {\n      pinMode(45, OUTPUT); digitalWrite(45, HIGH);\n      gpio_link_out4_expiry = futureMillis(10000UL);\n      gpio_reply = "LINK ACK OUT4 PULSE 10S"; return true;\n    }\n    return false;\n  };\n\n'''
if anchor not in s: raise SystemExit('LINK parser anchor missing')
s=s.replace(anchor,anchor+helper,1)
old='''    // OUT4 deliberately has no REMOTE_GPIO_OUT4 macro, timer state, STATUS hook or boot init.\n    // The first command configures GPIO45 as OUTPUT and then drives it.\n    if (strcmp(text, "LINK OUT4 ON") == 0) {\n      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);\n      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, HIGH);\n      gpio_reply = "LINK ACK OUT4 ON ISOLATED GPIO45";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {\n      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);\n      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);\n      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";\n      gpio_command_recognized = true;\n    }\n'''
new='''    if (diag4l_out4(text)) {\n      gpio_command_recognized = true;\n    }\n'''
if old not in s: raise SystemExit('OUT4 block missing')
s=s.replace(old,new,1)
loop_anchor='#ifdef REMOTE_GPIO_IN1\n  {\n    int raw = digitalRead(REMOTE_GPIO_IN1);'
expiry='''  if (gpio_link_out4_expiry && millisHasNowPassed(gpio_link_out4_expiry)) {\n    digitalWrite(45, LOW);\n    gpio_link_out4_expiry = 0;\n  }\n\n'''
if loop_anchor not in s: raise SystemExit('loop anchor missing')
s=s.replace(loop_anchor,expiry+loop_anchor,1)
p.write_text(s)
print('DIAG4L: fixed 10 second OUT4 PULSE, no timer parsing')
