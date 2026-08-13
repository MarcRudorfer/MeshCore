from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = 'static bool gpio_notify_contact_valid = false;\n'
extra = anchor + '\nstatic ContactInfo gpio_link_peer;\nstatic bool gpio_link_peer_valid = false;\n#ifdef REMOTE_GPIO_OUT3\nstatic volatile uint8_t gpio_link_out3_runtime_pin = REMOTE_GPIO_OUT3;\n#endif\n'
if anchor not in s:
    raise SystemExit('peer-state anchor not found')
s = s.replace(anchor, extra, 1)

anchor = '  bool gpio_command_recognized = false;\n\n'
block = '''  bool gpio_command_recognized = false;\n\n  bool gpio_link_sender_ok = gpio_link_peer_valid &&\n      memcmp(from.id.pub_key, gpio_link_peer.id.pub_key, PUB_KEY_SIZE) == 0;\n\n  if (strcmp(text, "LINK PAIR") == 0) {\n    gpio_link_peer = from;\n    gpio_link_peer_valid = true;\n    gpio_link_sender_ok = true;\n    gpio_reply = "LINK: PAIRED";\n    gpio_command_recognized = true;\n  }\n\n  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {\n    gpio_reply = gpio_link_peer_valid ? "LINK: PAIRED" : "LINK: UNPAIRED";\n    gpio_command_recognized = true;\n  }\n\n  // DIAG3I: runtime OUT3 path plus LINK OUT3 TIMER.\n  if (gpio_link_sender_ok) {\n#ifdef REMOTE_GPIO_OUT1\n    if (strcmp(text, "LINK OUT1 ON") == 0) { gpio_out1_timer_expiry = 0; gpio_out1_timer_contact_valid = false; digitalWrite(REMOTE_GPIO_OUT1, HIGH); gpio_reply = "LINK ACK OUT1 ON"; gpio_command_recognized = true; }\n    else if (strcmp(text, "LINK OUT1 OFF") == 0) { gpio_out1_timer_expiry = 0; gpio_out1_timer_contact_valid = false; digitalWrite(REMOTE_GPIO_OUT1, LOW); gpio_reply = "LINK ACK OUT1 OFF"; gpio_command_recognized = true; }\n#endif\n#ifdef REMOTE_GPIO_OUT2\n    if (strcmp(text, "LINK OUT2 ON") == 0) { gpio_out2_timer_expiry = 0; gpio_out2_timer_contact_valid = false; digitalWrite(REMOTE_GPIO_OUT2, HIGH); gpio_reply = "LINK ACK OUT2 ON"; gpio_command_recognized = true; }\n    else if (strcmp(text, "LINK OUT2 OFF") == 0) { gpio_out2_timer_expiry = 0; gpio_out2_timer_contact_valid = false; digitalWrite(REMOTE_GPIO_OUT2, LOW); gpio_reply = "LINK ACK OUT2 OFF"; gpio_command_recognized = true; }\n#endif\n#ifdef REMOTE_GPIO_OUT3\n    if (strcmp(text, "LINK OUT3 ON") == 0) {\n      gpio_out3_timer_expiry = 0; gpio_out3_timer_contact_valid = false;\n      digitalWrite((uint8_t)gpio_link_out3_runtime_pin, HIGH);\n      gpio_reply = "LINK ACK OUT3 ON"; gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT3 OFF") == 0) {\n      gpio_out3_timer_expiry = 0; gpio_out3_timer_contact_valid = false;\n      digitalWrite((uint8_t)gpio_link_out3_runtime_pin, LOW);\n      gpio_reply = "LINK ACK OUT3 OFF"; gpio_command_recognized = true;\n    } else if (strncmp(text, "LINK OUT3 TIMER", 15) == 0 && (text[15] == 0 || text[15] == ' ')) {\n      unsigned long seconds = 5; bool valid = true;\n      if (text[15] == ' ') { char *endptr = nullptr; seconds = strtoul(text + 16, &endptr, 10); valid = (endptr != text + 16 && *endptr == 0 && seconds >= 1 && seconds <= 3600); }\n      gpio_command_recognized = true;\n      if (valid) {\n        digitalWrite((uint8_t)gpio_link_out3_runtime_pin, HIGH);\n        gpio_out3_timer_expiry = futureMillis(seconds * 1000UL);\n        gpio_out3_timer_contact = from; gpio_out3_timer_contact_valid = true;\n        snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "LINK ACK OUT3 TIMER %luS", seconds); gpio_reply = gpio_reply_buf;\n      } else gpio_reply = "LINK OUT3 TIMER: USE 1-3600S";\n    }\n#endif\n  }\n\n'''
if anchor not in s:
    raise SystemExit('LINK receive anchor not found')
s = s.replace(anchor, block, 1)

s = s.replace('digitalWrite(REMOTE_GPIO_OUT3, LOW); gpio_out3_timer_expiry = 0;', 'digitalWrite((uint8_t)gpio_link_out3_runtime_pin, LOW); gpio_out3_timer_expiry = 0;', 1)

p.write_text(s)
print('Heltec V4 V5 DIAG3I applied: OUT3 runtime pin with LINK TIMER command')
