from pathlib import Path

# Restore the proven V5 LINK logic on top of the already-applied GPIO patch.
# IMPORTANT: this script changes no GPIO mapping and does not re-apply the GPIO patch.
p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# RAM-only peer state, exactly as used by the previously working V5 LINK proof-of-concept.
anchor = "static bool gpio_notify_contact_valid = false;\n"
extra = anchor + '''\nstatic ContactInfo gpio_link_peer;\nstatic bool gpio_link_peer_valid = false;\n\n#ifdef REMOTE_GPIO_IN1\nstatic int gpio_link_in1_last = HIGH;\n#endif\n#ifdef REMOTE_GPIO_IN2\nstatic int gpio_link_in2_last = HIGH;\n#endif\n#ifdef REMOTE_GPIO_IN3\nstatic int gpio_link_in3_last = HIGH;\n#endif\n#ifdef REMOTE_GPIO_IN4\nstatic int gpio_link_in4_last = HIGH;\n#endif\n'''
if anchor not in s:
    raise SystemExit("link globals anchor not found")
s = s.replace(anchor, extra, 1)

# LINK PAIR / STATUS and remote OUT1..OUT4 handling.
anchor = "  bool gpio_command_recognized = false;\n\n"
link_commands = r'''  bool gpio_command_recognized = false;

  bool gpio_link_sender_ok = gpio_link_peer_valid &&
      memcmp(from.id.pub_key, gpio_link_peer.id.pub_key, PUB_KEY_SIZE) == 0;

  if (strcmp(text, "LINK PAIR") == 0) {
    gpio_link_peer = from;
    gpio_link_peer_valid = true;
    gpio_reply = "LINK PAIRED";
    gpio_command_recognized = true;
    gpio_link_sender_ok = true;
  }

  // First valid LINK command can claim an unpaired receiver. This makes the
  // initial two-board test easy: pair one side, then the first input event
  // automatically establishes the reverse peer.
  bool gpio_is_link_out = strncmp(text, "LINK OUT", 8) == 0;
  if (gpio_is_link_out && !gpio_link_peer_valid) {
    gpio_link_peer = from;
    gpio_link_peer_valid = true;
    gpio_link_sender_ok = true;
  }

  if (gpio_is_link_out && gpio_link_sender_ok) {
#ifdef REMOTE_GPIO_OUT1
    if (strcmp(text, "LINK OUT1 ON") == 0) {
      gpio_out1_timer_expiry = 0; gpio_out1_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT1, HIGH);
      gpio_reply = "LINK ACK OUT1 ON"; gpio_command_recognized = true;
    } else if (strcmp(text, "LINK OUT1 OFF") == 0) {
      gpio_out1_timer_expiry = 0; gpio_out1_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT1, LOW);
      gpio_reply = "LINK ACK OUT1 OFF"; gpio_command_recognized = true;
    }
#endif
#ifdef REMOTE_GPIO_OUT2
    if (strcmp(text, "LINK OUT2 ON") == 0) {
      gpio_out2_timer_expiry = 0; gpio_out2_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT2, HIGH);
      gpio_reply = "LINK ACK OUT2 ON"; gpio_command_recognized = true;
    } else if (strcmp(text, "LINK OUT2 OFF") == 0) {
      gpio_out2_timer_expiry = 0; gpio_out2_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT2, LOW);
      gpio_reply = "LINK ACK OUT2 OFF"; gpio_command_recognized = true;
    }
#endif
#ifdef REMOTE_GPIO_OUT3
    if (strcmp(text, "LINK OUT3 ON") == 0) {
      gpio_out3_timer_expiry = 0; gpio_out3_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT3, HIGH);
      gpio_reply = "LINK ACK OUT3 ON"; gpio_command_recognized = true;
    } else if (strcmp(text, "LINK OUT3 OFF") == 0) {
      gpio_out3_timer_expiry = 0; gpio_out3_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT3, LOW);
      gpio_reply = "LINK ACK OUT3 OFF"; gpio_command_recognized = true;
    }
#endif
#ifdef REMOTE_GPIO_OUT4
    if (strcmp(text, "LINK OUT4 ON") == 0) {
      gpio_out4_timer_expiry = 0; gpio_out4_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT4, HIGH);
      gpio_reply = "LINK ACK OUT4 ON"; gpio_command_recognized = true;
    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {
      gpio_out4_timer_expiry = 0; gpio_out4_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT4, LOW);
      gpio_reply = "LINK ACK OUT4 OFF"; gpio_command_recognized = true;
    }
#endif
  }

  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {
    gpio_reply = gpio_link_peer_valid ? "LINK = PAIRED" : "LINK = UNPAIRED";
    gpio_command_recognized = true;
  }

'''
if anchor not in s:
    raise SystemExit("onMessageRecv link anchor not found")
s = s.replace(anchor, link_commands, 1)

# Initialize LINK tracking after all GPIO inputs are initialized.
anchor = "  gpio_notify_contact_valid = false;\n  BaseChatMesh::begin();"
init = r'''  gpio_notify_contact_valid = false;
  gpio_link_peer_valid = false;
#ifdef REMOTE_GPIO_IN1
  gpio_link_in1_last = gpio_in1_stable;
#endif
#ifdef REMOTE_GPIO_IN2
  gpio_link_in2_last = gpio_in2_stable;
#endif
#ifdef REMOTE_GPIO_IN3
  gpio_link_in3_last = gpio_in3_stable;
#endif
#ifdef REMOTE_GPIO_IN4
  gpio_link_in4_last = gpio_in4_stable;
#endif
  BaseChatMesh::begin();'''
if anchor not in s:
    raise SystemExit("link begin anchor not found")
s = s.replace(anchor, init, 1)

# Mirror each stable local input change to the corresponding output on the paired peer.
anchor = "  if (_cli_rescue) {\n"
link_loop = r'''#ifdef REMOTE_GPIO_IN1
  if (gpio_in1_stable != gpio_link_in1_last) {
    gpio_link_in1_last = gpio_in1_stable;
    if (gpio_link_peer_valid) {
      uint32_t expected_ack = 0, est_timeout = 0;
      sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0,
                  gpio_in1_stable == LOW ? "LINK OUT1 ON" : "LINK OUT1 OFF",
                  expected_ack, est_timeout);
    }
  }
#endif
#ifdef REMOTE_GPIO_IN2
  if (gpio_in2_stable != gpio_link_in2_last) {
    gpio_link_in2_last = gpio_in2_stable;
    if (gpio_link_peer_valid) {
      uint32_t expected_ack = 0, est_timeout = 0;
      sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0,
                  gpio_in2_stable == LOW ? "LINK OUT2 ON" : "LINK OUT2 OFF",
                  expected_ack, est_timeout);
    }
  }
#endif
#ifdef REMOTE_GPIO_IN3
  if (gpio_in3_stable != gpio_link_in3_last) {
    gpio_link_in3_last = gpio_in3_stable;
    if (gpio_link_peer_valid) {
      uint32_t expected_ack = 0, est_timeout = 0;
      sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0,
                  gpio_in3_stable == LOW ? "LINK OUT3 ON" : "LINK OUT3 OFF",
                  expected_ack, est_timeout);
    }
  }
#endif
#ifdef REMOTE_GPIO_IN4
  if (gpio_in4_stable != gpio_link_in4_last) {
    gpio_link_in4_last = gpio_in4_stable;
    if (gpio_link_peer_valid) {
      uint32_t expected_ack = 0, est_timeout = 0;
      sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0,
                  gpio_in4_stable == LOW ? "LINK OUT4 ON" : "LINK OUT4 OFF",
                  expected_ack, est_timeout);
    }
  }
#endif

  if (_cli_rescue) {
'''
if anchor not in s:
    raise SystemExit("link loop anchor not found")
s = s.replace(anchor, link_loop, 1)

p.write_text(s)
print("Proven V5 LINK logic restored: PAIR/STATUS + IN1-4 -> remote OUT1-4; GPIO mapping untouched")
