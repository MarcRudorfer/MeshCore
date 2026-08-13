from pathlib import Path
p=Path('examples/companion_radio/MyMesh.cpp')
s=p.read_text()

# Keep OUT4 handling compact and outside the long command chain.
anchor='  bool gpio_command_recognized = false;\n\n'
helper='''  auto diag4k_out4 = [&](const char* cmd) -> bool {\n    if (strcmp(cmd, "LINK OUT4 ON") == 0) {\n      gpio_link_out4_expiry = 0;\n      pinMode(45, OUTPUT); digitalWrite(45, HIGH);\n      gpio_reply = "LINK ACK OUT4 ON ISOLATED GPIO45";\n      return true;\n    }\n    if (strcmp(cmd, "LINK OUT4 OFF") == 0) {\n      gpio_link_out4_expiry = 0;\n      pinMode(45, OUTPUT); digitalWrite(45, LOW);\n      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";\n      return true;\n    }\n    if (strncmp(cmd, "LINK OUT4 TIMER", 15) == 0 && (cmd[15] == 0 || cmd[15] == ' ')) {\n      unsigned long seconds = 5;\n      bool valid = true;\n      if (cmd[15] == ' ') {\n        char* endptr = nullptr;\n        seconds = strtoul(cmd + 16, &endptr, 10);\n        valid = endptr != cmd + 16 && *endptr == 0 && seconds >= 1 && seconds <= 3600;\n      }\n      if (!valid) { gpio_reply = "LINK OUT4 TIMER: USE 1-3600S"; return true; }\n      pinMode(45, OUTPUT); digitalWrite(45, HIGH);\n      gpio_link_out4_expiry = futureMillis(seconds * 1000UL);\n      snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "LINK ACK OUT4 TIMER %luS", seconds);\n      gpio_reply = gpio_reply_buf;\n      return true;\n    }\n    return false;\n  };\n\n'''
if anchor not in s: raise SystemExit('LINK parser anchor missing')
s=s.replace(anchor,anchor+helper,1)

old='''    // OUT4 deliberately has no REMOTE_GPIO_OUT4 macro, timer state, STATUS hook or boot init.\n    // The first command configures GPIO45 as OUTPUT and then drives it.\n    if (strcmp(text, "LINK OUT4 ON") == 0) {\n      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);\n      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, HIGH);\n      gpio_reply = "LINK ACK OUT4 ON ISOLATED GPIO45";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {\n      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);\n      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);\n      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";\n      gpio_command_recognized = true;\n    }\n'''
new='''    if (diag4k_out4(text)) {\n      gpio_command_recognized = true;\n    }\n'''
if old not in s: raise SystemExit('OUT4 block missing')
s=s.replace(old,new,1)

# Minimal timer expiry: GPIO45 goes LOW when the timer expires. No extra sendMessage path yet.
loop_anchor='#ifdef REMOTE_GPIO_IN1\n  {\n    int raw = digitalRead(REMOTE_GPIO_IN1);'
expiry='''  if (gpio_link_out4_expiry && millisHasNowPassed(gpio_link_out4_expiry)) {\n    digitalWrite(45, LOW);\n    gpio_link_out4_expiry = 0;\n  }\n\n'''
if loop_anchor not in s: raise SystemExit('loop anchor missing')
s=s.replace(loop_anchor,expiry+loop_anchor,1)

p.write_text(s)
print('DIAG4K: OUT4 ON/OFF/TIMER compact dispatcher + minimal auto-OFF expiry')
