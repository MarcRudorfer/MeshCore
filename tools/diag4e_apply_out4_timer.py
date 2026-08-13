from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

old = '''    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {
      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);
      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";
      gpio_command_recognized = true;
    }
'''
new = '''    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {
      gpio_link_out4_expiry = 0;
      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);
      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";
      gpio_command_recognized = true;
    } else if (strncmp(text, "LINK OUT4 TIMER", 15) == 0 && (text[15] == 0 || text[15] == ' ')) {
      unsigned long seconds = 5;
      bool valid = true;
      if (text[15] == ' ') {
        char *endptr = nullptr;
        seconds = strtoul(text + 16, &endptr, 10);
        valid = (endptr != text + 16 && *endptr == 0 && seconds >= 1 && seconds <= 3600);
      }
      gpio_command_recognized = true;
      if (valid) {
        pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
        digitalWrite((uint8_t)gpio_link_out4_runtime_pin, HIGH);
        gpio_link_out4_expiry = futureMillis(seconds * 1000UL);
        snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "LINK ACK OUT4 TIMER %luS", seconds);
        gpio_reply = gpio_reply_buf;
      } else {
        gpio_reply = "LINK OUT4 TIMER: USE 1-3600S";
      }
    }
'''
if old not in s:
    raise SystemExit('OUT4 OFF anchor not found')
s = s.replace(old, new, 1)

old_loop = '''void MyMesh::loop() {
  BaseChatMesh::loop();
'''
new_loop = '''void MyMesh::loop() {
  if (gpio_link_out4_expiry && millisHasNowPassed(gpio_link_out4_expiry)) {
    digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);
    gpio_link_out4_expiry = 0;
  }
  BaseChatMesh::loop();
'''
if old_loop not in s:
    raise SystemExit('loop anchor not found')
s = s.replace(old_loop, new_loop, 1)

p.write_text(s)
print('DIAG4E OUT4 timer applied on isolated GPIO45')
