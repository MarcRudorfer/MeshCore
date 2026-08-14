from pathlib import Path

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

anchor = "static bool gpio_notify_contact_valid = false;\n"
extra = anchor + '''\nstatic ContactInfo gpio_link_peer;\nstatic bool gpio_link_peer_valid = false;\n#ifdef REMOTE_GPIO_IN1\nstatic int gpio_link_in1_last = HIGH;\n#endif\n#ifdef REMOTE_GPIO_IN2\nstatic int gpio_link_in2_last = HIGH;\n#endif\n#ifdef REMOTE_GPIO_IN3\nstatic int gpio_link_in3_last = HIGH;\n#endif\n#ifdef REMOTE_GPIO_IN4\nstatic int gpio_link_in4_last = HIGH;\n#endif\n'''
if anchor not in s: raise SystemExit("LINK globals anchor not found")
s = s.replace(anchor, extra, 1)

anchor = "  bool gpio_command_recognized = false;\n\n"
block = r'''  bool gpio_command_recognized = false;

  bool gpio_link_sender_ok = gpio_link_peer_valid &&
      memcmp(from.id.pub_key, gpio_link_peer.id.pub_key, PUB_KEY_SIZE) == 0;

  if (strcmp(text, "LINK PAIR") == 0) {
    gpio_link_peer = from;
    gpio_link_peer_valid = true;
    gpio_link_sender_ok = true;
    gpio_reply = "LINK PAIRED";
    gpio_command_recognized = true;
  }
  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {
    gpio_reply = gpio_link_peer_valid ? "LINK = PAIRED" : "LINK = UNPAIRED";
    gpio_command_recognized = true;
  }

#define LINK_OUT_HANDLER(N) \
  if (gpio_link_sender_ok && strcmp(text, "LINK OUT" #N " ON") == 0) { \
    gpio_out##N##_timer_expiry = 0; gpio_out##N##_timer_contact_valid = false; \
    digitalWrite(REMOTE_GPIO_OUT##N, HIGH); gpio_reply = "LINK ACK OUT" #N " ON"; gpio_command_recognized = true; \
  } else if (gpio_link_sender_ok && strcmp(text, "LINK OUT" #N " OFF") == 0) { \
    gpio_out##N##_timer_expiry = 0; gpio_out##N##_timer_contact_valid = false; \
    digitalWrite(REMOTE_GPIO_OUT##N, LOW); gpio_reply = "LINK ACK OUT" #N " OFF"; gpio_command_recognized = true; \
  }
#ifdef REMOTE_GPIO_OUT1
  LINK_OUT_HANDLER(1)
#endif
#ifdef REMOTE_GPIO_OUT2
  LINK_OUT_HANDLER(2)
#endif
#ifdef REMOTE_GPIO_OUT3
  LINK_OUT_HANDLER(3)
#endif
#ifdef REMOTE_GPIO_OUT4
  LINK_OUT_HANDLER(4)
#endif
#undef LINK_OUT_HANDLER

'''
if anchor not in s: raise SystemExit("LINK command anchor not found")
s = s.replace(anchor, block, 1)

anchor = "  if (_cli_rescue) {\n"
loop = r'''#ifdef REMOTE_GPIO_IN1
  if (gpio_in1_stable != gpio_link_in1_last) {
    gpio_link_in1_last = gpio_in1_stable;
    if (gpio_link_peer_valid) { uint32_t expected_ack=0, est_timeout=0; sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0, gpio_in1_stable == LOW ? "LINK OUT1 ON" : "LINK OUT1 OFF", expected_ack, est_timeout); }
  }
#endif
#ifdef REMOTE_GPIO_IN2
  if (gpio_in2_stable != gpio_link_in2_last) {
    gpio_link_in2_last = gpio_in2_stable;
    if (gpio_link_peer_valid) { uint32_t expected_ack=0, est_timeout=0; sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0, gpio_in2_stable == LOW ? "LINK OUT2 ON" : "LINK OUT2 OFF", expected_ack, est_timeout); }
  }
#endif
#ifdef REMOTE_GPIO_IN3
  if (gpio_in3_stable != gpio_link_in3_last) {
    gpio_link_in3_last = gpio_in3_stable;
    if (gpio_link_peer_valid) { uint32_t expected_ack=0, est_timeout=0; sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0, gpio_in3_stable == LOW ? "LINK OUT3 ON" : "LINK OUT3 OFF", expected_ack, est_timeout); }
  }
#endif
#ifdef REMOTE_GPIO_IN4
  if (gpio_in4_stable != gpio_link_in4_last) {
    gpio_link_in4_last = gpio_in4_stable;
    if (gpio_link_peer_valid) { uint32_t expected_ack=0, est_timeout=0; sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0, gpio_in4_stable == LOW ? "LINK OUT4 ON" : "LINK OUT4 OFF", expected_ack, est_timeout); }
  }
#endif

  if (_cli_rescue) {
'''
if anchor not in s: raise SystemExit("LINK loop anchor not found")
s = s.replace(anchor, loop, 1)
p.write_text(s)
print("Applied LINK CH1-CH4 using verified CH1 pattern; no begin/boot changes")
