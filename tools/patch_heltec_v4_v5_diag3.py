from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = 'static bool gpio_notify_contact_valid = false;\n'
extra = anchor + '\nstatic ContactInfo gpio_link_peer;\nstatic bool gpio_link_peer_valid = false;\n#ifdef REMOTE_GPIO_OUT3\nstatic volatile uint8_t gpio_link_out3_runtime_pin = REMOTE_GPIO_OUT3;\n#endif\n'
if anchor not in s:
    raise SystemExit('peer-state anchor not found')
s = s.replace(anchor, extra, 1)

anchor = '  bool gpio_command_recognized = false;\n\n'
block = '''  bool gpio_command_recognized = false;\n\n  bool gpio_link_sender_ok = gpio_link_peer_valid &&\n      memcmp(from.id.pub_key, gpio_link_peer.id.pub_key, PUB_KEY_SIZE) == 0;\n\n  if (strcmp(text, "LINK PAIR") == 0) {\n    gpio_link_peer = from;\n    gpio_link_peer_valid = true;\n    gpio_link_sender_ok = true;\n    gpio_reply = "LINK: PAIRED";\n    gpio_command_recognized = true;\n  }\n\n  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {\n    gpio_reply = gpio_link_peer_valid ? "LINK: PAIRED" : "LINK: UNPAIRED";\n    gpio_command_recognized = true;\n  }\n\n  // DIAG3G: OUT3 uses a runtime pin variable only; no OUT3 timer variables.\n  if (gpio_link_sender_ok) {\n#ifdef REMOTE_GPIO_OUT1\n    if (strcmp(text, "LINK OUT1 ON") == 0) {\n      gpio_out1_timer_expiry = 0;\n      gpio_out1_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT1, HIGH);\n      gpio_reply = "LINK ACK OUT1 ON";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT1 OFF") == 0) {\n      gpio_out1_timer_expiry = 0;\n      gpio_out1_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT1, LOW);\n      gpio_reply = "LINK ACK OUT1 OFF";\n      gpio_command_recognized = true;\n    }\n#endif\n#ifdef REMOTE_GPIO_OUT2\n    if (strcmp(text, "LINK OUT2 ON") == 0) {\n      gpio_out2_timer_expiry = 0;\n      gpio_out2_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT2, HIGH);\n      gpio_reply = "LINK ACK OUT2 ON";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT2 OFF") == 0) {\n      gpio_out2_timer_expiry = 0;\n      gpio_out2_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT2, LOW);\n      gpio_reply = "LINK ACK OUT2 OFF";\n      gpio_command_recognized = true;\n    }\n#endif\n#ifdef REMOTE_GPIO_OUT3\n    if (strcmp(text, "LINK OUT3 ON") == 0) {\n      digitalWrite((uint8_t)gpio_link_out3_runtime_pin, HIGH);\n      gpio_reply = "LINK ACK OUT3 ON RUNTIME";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT3 OFF") == 0) {\n      digitalWrite((uint8_t)gpio_link_out3_runtime_pin, LOW);\n      gpio_reply = "LINK ACK OUT3 OFF RUNTIME";\n      gpio_command_recognized = true;\n    }\n#endif\n  }\n\n'''
if anchor not in s:
    raise SystemExit('LINK receive anchor not found')
s = s.replace(anchor, block, 1)
p.write_text(s)
print('Heltec V4 V5 DIAG3G applied: OUT3 via runtime pin variable, no timer access')
