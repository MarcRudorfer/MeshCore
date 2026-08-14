from pathlib import Path

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# Pairing state + channel-1 edge tracker only.
anchor = "static bool gpio_notify_contact_valid = false;\n"
extra = anchor + '''\nstatic ContactInfo gpio_link_peer;\nstatic bool gpio_link_peer_valid = false;\n#ifdef REMOTE_GPIO_IN1\nstatic int gpio_link_in1_last = HIGH;\n#endif\n'''
if anchor not in s:
    raise SystemExit("LINK CH1 globals anchor not found")
s = s.replace(anchor, extra, 1)

# LINK PAIR / STATUS and receive-side OUT1 control only.
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

#ifdef REMOTE_GPIO_OUT1
  if (gpio_link_sender_ok && strcmp(text, "LINK OUT1 ON") == 0) {
    gpio_out1_timer_expiry = 0;
    gpio_out1_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT1, HIGH);
    gpio_reply = "LINK ACK OUT1 ON";
    gpio_command_recognized = true;
  } else if (gpio_link_sender_ok && strcmp(text, "LINK OUT1 OFF") == 0) {
    gpio_out1_timer_expiry = 0;
    gpio_out1_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT1, LOW);
    gpio_reply = "LINK ACK OUT1 OFF";
    gpio_command_recognized = true;
  }
#endif

'''
if anchor not in s:
    raise SystemExit("LINK CH1 command anchor not found")
s = s.replace(anchor, block, 1)

# Mirror only stable IN1 changes to the paired peer. No begin()/boot changes.
anchor = "  if (_cli_rescue) {\n"
loop = r'''#ifdef REMOTE_GPIO_IN1
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

  if (_cli_rescue) {
'''
if anchor not in s:
    raise SystemExit("LINK CH1 loop anchor not found")
s = s.replace(anchor, loop, 1)

p.write_text(s)
print("Applied isolated LINK CH1 patch: PAIR/STATUS + IN1 <-> remote OUT1")
