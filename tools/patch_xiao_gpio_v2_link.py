from pathlib import Path

# XIAO nRF52840 GPIO V2 LINK
# Start from the already hardware-tested V2 FINAL behavior.
# D6 = IN1 (INPUT_PULLUP), D7 = OUT1.
# Link protocol intentionally matches the finished Heltec V3/V4 implementation:
#   LINK PAIR
#   LINK OUT1 ON
#   LINK OUT1 OFF
#   LINK STATUS
# A stable IN1 LOW mirrors to remote OUT1 ON; HIGH mirrors to OUT1 OFF.

exec(Path("tools/patch_xiao_gpio_v2.py").read_text(), {"__name__": "__main__"})

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# Separate peer state so the normal V2 notification target remains untouched.
anchor = "static bool gpio_in1_notify_contact_valid = false;\n"
extra = anchor + '''static ContactInfo gpio_link_peer;\nstatic bool gpio_link_peer_valid = false;\nstatic int gpio_link_in1_last = HIGH;\n'''
if anchor not in s:
    raise SystemExit("XIAO link globals anchor not found")
s = s.replace(anchor, extra, 1)

# Add the same LINK commands used by the Heltec V3/V4 link firmware.
anchor = "  const char* gpio_reply = nullptr;\n  char gpio_reply_buf[128];\n\n"
link_commands = r'''  const char* gpio_reply = nullptr;
  char gpio_reply_buf[128];

#ifdef REMOTE_GPIO_IN1
  bool gpio_link_sender_ok = gpio_link_peer_valid &&
      memcmp(from.id.pub_key, gpio_link_peer.id.pub_key, PUB_KEY_SIZE) == 0;

  if (strcmp(text, "LINK PAIR") == 0) {
    gpio_link_peer = from;
    gpio_link_peer_valid = true;
    gpio_link_sender_ok = true;
    gpio_reply = "LINK PAIRED";
  }

  // Same behavior as Heltec: the first valid LINK OUT command can establish
  // the reverse peer automatically on an unpaired receiver.
  bool gpio_is_link_out = strncmp(text, "LINK OUT", 8) == 0;
  if (gpio_is_link_out && !gpio_link_peer_valid) {
    gpio_link_peer = from;
    gpio_link_peer_valid = true;
    gpio_link_sender_ok = true;
  }

#ifdef REMOTE_GPIO_OUT1
  if (gpio_is_link_out && gpio_link_sender_ok) {
    if (strcmp(text, "LINK OUT1 ON") == 0) {
      gpio_out1_timer_expiry = 0;
      gpio_out1_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT1, HIGH);
      gpio_reply = "LINK ACK OUT1 ON";
    } else if (strcmp(text, "LINK OUT1 OFF") == 0) {
      gpio_out1_timer_expiry = 0;
      gpio_out1_timer_contact_valid = false;
      digitalWrite(REMOTE_GPIO_OUT1, LOW);
      gpio_reply = "LINK ACK OUT1 OFF";
    }
  }
#endif

  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {
    gpio_reply = gpio_link_peer_valid ? "LINK = PAIRED" : "LINK = UNPAIRED";
  }
#endif

'''
if anchor not in s:
    raise SystemExit("XIAO link command anchor not found")
s = s.replace(anchor, link_commands, 1)

# Initialize link tracking from the already initialized stable V2 input state.
anchor = "  gpio_in1_last_change_ms = millis();\n#endif\n"
init = "  gpio_in1_last_change_ms = millis();\n  gpio_link_in1_last = gpio_in1_stable_state;\n  gpio_link_peer_valid = false;\n#endif\n"
if anchor not in s:
    raise SystemExit("XIAO link begin anchor not found")
s = s.replace(anchor, init, 1)

# Mirror every debounced stable IN1 change to the paired device, using exactly
# the Heltec V3/V4 LINK OUT1 command semantics. Keep the normal V2 automatic
# IN1 HIGH/LOW notification in place as well.
anchor = '''    if (gpio_in1_notify_contact_valid) {\n      uint32_t expected_ack = 0, est_timeout = 0;\n      const char* msg = gpio_in1_stable_state == HIGH ? "IN1 = HIGH" : "IN1 = LOW";\n      sendMessage(gpio_in1_notify_contact, getRTCClock()->getCurrentTimeUnique(), 0,\n                  msg, expected_ack, est_timeout);\n    }\n'''
replacement = anchor + r'''
    if (gpio_in1_stable_state != gpio_link_in1_last) {
      gpio_link_in1_last = gpio_in1_stable_state;
      if (gpio_link_peer_valid) {
        uint32_t expected_ack = 0, est_timeout = 0;
        sendMessage(gpio_link_peer, getRTCClock()->getCurrentTimeUnique(), 0,
                    gpio_in1_stable_state == LOW ? "LINK OUT1 ON" : "LINK OUT1 OFF",
                    expected_ack, est_timeout);
      }
    }
'''
if anchor not in s:
    raise SystemExit("XIAO link input-change anchor not found")
s = s.replace(anchor, replacement, 1)

p.write_text(s)
print("XIAO GPIO V2 LINK: D6 IN1 -> paired remote OUT1; Heltec V3/V4 compatible protocol")
