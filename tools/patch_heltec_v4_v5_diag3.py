from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = 'static bool gpio_notify_contact_valid = false;\n'
extra = anchor + '\nstatic ContactInfo gpio_link_peer;\nstatic bool gpio_link_peer_valid = false;\n'
if anchor not in s:
    raise SystemExit('peer-state anchor not found')
s = s.replace(anchor, extra, 1)

anchor = '  bool gpio_command_recognized = false;\n\n'
block = '''  bool gpio_command_recognized = false;\n\n  bool gpio_link_sender_ok = gpio_link_peer_valid &&\n      memcmp(from.id.pub_key, gpio_link_peer.id.pub_key, PUB_KEY_SIZE) == 0;\n\n  if (strcmp(text, "LINK PAIR") == 0) {\n    gpio_link_peer = from;\n    gpio_link_peer_valid = true;\n    gpio_link_sender_ok = true;\n    gpio_reply = "LINK: PAIRED";\n    gpio_command_recognized = true;\n  }\n\n  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {\n    gpio_reply = gpio_link_peer_valid ? "LINK: PAIRED" : "LINK: UNPAIRED";\n    gpio_command_recognized = true;\n  }\n\n  // DIAG3C: remote OUT1 + OUT2 + OUT3 receive only. No OUT4 and no automatic IN->OUT send.\n  if (gpio_link_sender_ok) {\n#ifdef REMOTE_GPIO_OUT1\n    if (strcmp(text, "LINK OUT1 ON") == 0) {\n      gpio_out1_timer_expiry = 0;\n      gpio_out1_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT1, HIGH);\n      gpio_reply = "LINK ACK OUT1 ON";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT1 OFF") == 0) {\n      gpio_out1_timer_expiry = 0;\n      gpio_out1_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT1, LOW);\n      gpio_reply = "LINK ACK OUT1 OFF";\n      gpio_command_recognized = true;\n    }\n#endif\n#ifdef REMOTE_GPIO_OUT2\n    if (strcmp(text, "LINK OUT2 ON") == 0) {\n      gpio_out2_timer_expiry = 0;\n      gpio_out2_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT2, HIGH);\n      gpio_reply = "LINK ACK OUT2 ON";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT2 OFF") == 0) {\n      gpio_out2_timer_expiry = 0;\n      gpio_out2_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT2, LOW);\n      gpio_reply = "LINK ACK OUT2 OFF";\n      gpio_command_recognized = true;\n    }\n#endif\n#ifdef REMOTE_GPIO_OUT3\n    if (strcmp(text, "LINK OUT3 ON") == 0) {\n      gpio_out3_timer_expiry = 0;\n      gpio_out3_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT3, HIGH);\n      gpio_reply = "LINK ACK OUT3 ON";\n      gpio_command_recognized = true;\n    } else if (strcmp(text, "LINK OUT3 OFF") == 0) {\n      gpio_out3_timer_expiry = 0;\n      gpio_out3_timer_contact_valid = false;\n      digitalWrite(REMOTE_GPIO_OUT3, LOW);\n      gpio_reply = "LINK ACK OUT3 OFF";\n      gpio_command_recognized = true;\n    }\n#endif\n  }\n\n'''
if anchor not in s:
    raise SystemExit('LINK receive anchor not found')
s = s.replace(anchor, block, 1)
p.write_text(s)
print('Heltec V4 V5 diagnostic step 3C applied: LINK OUT1 + OUT2 + OUT3')
