from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

# Add OUT4 timer contact state beside the already isolated runtime timer state.
old_globals = 'static uint32_t gpio_link_out4_expiry = 0;\n'
new_globals = old_globals + 'static ContactInfo gpio_link_out4_timer_contact;\nstatic bool gpio_link_out4_timer_contact_valid = false;\n'
if old_globals not in s:
    raise SystemExit('OUT4 timer globals anchor not found')
s = s.replace(old_globals, new_globals, 1)

# Extend the proven OUT4 ON/OFF runtime command path with a timer command,
# mirroring the already-working OUT3 timer semantics.
old = '''    if (strcmp(text, "LINK OUT4 ON") == 0) {
      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, HIGH);
      gpio_reply = "LINK ACK OUT4 ON ISOLATED GPIO45";
      gpio_command_recognized = true;
    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {
      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);
      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";
      gpio_command_recognized = true;
    }
'''
new = '''    if (strcmp(text, "LINK OUT4 ON") == 0) {
      gpio_link_out4_expiry = 0;
      gpio_link_out4_timer_contact_valid = false;
      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, HIGH);
      gpio_reply = "LINK ACK OUT4 ON ISOLATED GPIO45";
      gpio_command_recognized = true;
    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {
      gpio_link_out4_expiry = 0;
      gpio_link_out4_timer_contact_valid = false;
      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);
      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";
      gpio_command_recognized = true;
    } else if (strncmp(text, "LINK OUT4 TIMER", 15) == 0 && (text[15] == 0 || text[15] == ' ')) {
      unsigned long seconds = 5; bool valid = true;
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
        gpio_link_out4_timer_contact = from;
        gpio_link_out4_timer_contact_valid = true;
        snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "LINK ACK OUT4 TIMER %luS", seconds);
        gpio_reply = gpio_reply_buf;
      } else {
        gpio_reply = "LINK OUT4 TIMER: USE 1-3600S";
      }
    }
'''
if old not in s:
    raise SystemExit('OUT4 runtime command anchor not found')
s = s.replace(old, new, 1)

# Service OUT4 at the same point in MyMesh::loop() as the proven OUT3 timer,
# immediately before the existing IN1 polling block. Do not add code ahead of
# BaseChatMesh::loop() and do not enable REMOTE_GPIO_OUT4.
loop_anchor = '''#ifdef REMOTE_GPIO_IN1
  {
    int raw = digitalRead(REMOTE_GPIO_IN1);'''
out4_service = '''  if (gpio_link_out4_expiry && millisHasNowPassed(gpio_link_out4_expiry)) {
    digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);
    gpio_link_out4_expiry = 0;
    if (gpio_link_out4_timer_contact_valid) {
      uint32_t expected_ack = 0, est_timeout = 0;
      sendMessage(gpio_link_out4_timer_contact,
                  getRTCClock()->getCurrentTimeUnique(), 0,
                  "LINK OUT4 = OFF (TIMER DONE)",
                  expected_ack, est_timeout);
      gpio_link_out4_timer_contact_valid = false;
    }
  }

'''
if loop_anchor not in s:
    raise SystemExit('OUT3-style loop service anchor not found')
s = s.replace(loop_anchor, out4_service + loop_anchor, 1)

p.write_text(s)
print('DIAG4F OUT4 timer applied: GPIO45 runtime timer mirrors proven OUT3 service path')
