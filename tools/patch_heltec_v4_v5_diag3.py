from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = 'static bool gpio_notify_contact_valid = false;\n'
extra = anchor + '''
static ContactInfo gpio_link_peer;
static bool gpio_link_peer_valid = false;
#ifdef REMOTE_GPIO_OUT3
static volatile uint8_t gpio_link_out3_runtime_pin = REMOTE_GPIO_OUT3;
#endif
// DIAG4D: OUT4 is intentionally NOT defined through REMOTE_GPIO_OUT4.
// Keep it completely isolated from the base OUT4 implementation.
static volatile uint8_t gpio_link_out4_runtime_pin = 45;
static uint32_t gpio_link_out4_expiry = 0;
'''
if anchor not in s:
    raise SystemExit('peer-state anchor not found')
s = s.replace(anchor, extra, 1)

anchor = '  bool gpio_command_recognized = false;\n\n'
block = '''  bool gpio_command_recognized = false;

  bool gpio_link_sender_ok = gpio_link_peer_valid &&
      memcmp(from.id.pub_key, gpio_link_peer.id.pub_key, PUB_KEY_SIZE) == 0;

  if (strcmp(text, "LINK PAIR") == 0) {
    gpio_link_peer = from;
    gpio_link_peer_valid = true;
    gpio_link_sender_ok = true;
    gpio_reply = "LINK: PAIRED";
    gpio_command_recognized = true;
  }

  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {
    gpio_reply = gpio_link_peer_valid ? "LINK: PAIRED" : "LINK: UNPAIRED";
    gpio_command_recognized = true;
  }

  // DIAG4D: known-good OUT1/2, proven OUT3 runtime+timer, isolated OUT4 runtime GPIO45.
  if (gpio_link_sender_ok) {
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
      digitalWrite((uint8_t)gpio_link_out3_runtime_pin, HIGH);
      gpio_reply = "LINK ACK OUT3 ON"; gpio_command_recognized = true;
    } else if (strcmp(text, "LINK OUT3 OFF") == 0) {
      gpio_out3_timer_expiry = 0; gpio_out3_timer_contact_valid = false;
      digitalWrite((uint8_t)gpio_link_out3_runtime_pin, LOW);
      gpio_reply = "LINK ACK OUT3 OFF"; gpio_command_recognized = true;
    } else if (strncmp(text, "LINK OUT3 TIMER", 15) == 0 && (text[15] == 0 || text[15] == ' ')) {
      unsigned long seconds = 5; bool valid = true;
      if (text[15] == ' ') {
        char *endptr = nullptr;
        seconds = strtoul(text + 16, &endptr, 10);
        valid = (endptr != text + 16 && *endptr == 0 && seconds >= 1 && seconds <= 3600);
      }
      gpio_command_recognized = true;
      if (valid) {
        digitalWrite((uint8_t)gpio_link_out3_runtime_pin, HIGH);
        gpio_out3_timer_expiry = futureMillis(seconds * 1000UL);
        gpio_out3_timer_contact = from; gpio_out3_timer_contact_valid = true;
        snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "LINK ACK OUT3 TIMER %luS", seconds);
        gpio_reply = gpio_reply_buf;
      } else {
        gpio_reply = "LINK OUT3 TIMER: USE 1-3600S";
      }
    }
#endif

    // OUT4 deliberately has no REMOTE_GPIO_OUT4 macro, timer state, STATUS hook or boot init.
    // The first command configures GPIO45 as OUTPUT and then drives it.
    if (strcmp(text, "LINK OUT4 ON") == 0) {
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
  }

'''
if anchor not in s:
    raise SystemExit('LINK receive anchor not found')
s = s.replace(anchor, block, 1)

# Keep the already proven OUT3 timer expiry on the runtime path.
s = s.replace(
    'digitalWrite(REMOTE_GPIO_OUT3, LOW); gpio_out3_timer_expiry = 0;',
    'digitalWrite((uint8_t)gpio_link_out3_runtime_pin, LOW); gpio_out3_timer_expiry = 0;',
    1
)

p.write_text(s)
print('Heltec V4 V5 DIAG4D applied: isolated OUT4 runtime GPIO45, no REMOTE_GPIO_OUT4 macro')
