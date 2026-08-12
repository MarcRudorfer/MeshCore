from pathlib import Path

# MeshCore 1.16 Heltec V3 custom GPIO V3:
# OUT1=GPIO4, OUT2=GPIO5, IN1=GPIO6, IN2=GPIO7
# Outputs: ON/OFF/TIMER 1..3600s
# Inputs: INPUT_PULLUP, active LOW, 50ms debounce, change notifications
# STATUS / STATUS? / STATUS ? returns all four states.

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

anchor = '#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n'
globals_block = '''#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n\n#ifdef REMOTE_GPIO_OUT1\nstatic unsigned long gpio_out1_timer_expiry = 0;\nstatic ContactInfo gpio_out1_timer_contact;\nstatic bool gpio_out1_timer_contact_valid = false;\n#endif\n#ifdef REMOTE_GPIO_OUT2\nstatic unsigned long gpio_out2_timer_expiry = 0;\nstatic ContactInfo gpio_out2_timer_contact;\nstatic bool gpio_out2_timer_contact_valid = false;\n#endif\n\nstatic ContactInfo gpio_notify_contact;\nstatic bool gpio_notify_contact_valid = false;\n\n#ifdef REMOTE_GPIO_IN1\nstatic int gpio_in1_stable = HIGH;\nstatic int gpio_in1_raw = HIGH;\nstatic unsigned long gpio_in1_debounce_expiry = 0;\n#endif\n#ifdef REMOTE_GPIO_IN2\nstatic int gpio_in2_stable = HIGH;\nstatic int gpio_in2_raw = HIGH;\nstatic unsigned long gpio_in2_debounce_expiry = 0;\n#endif\n'''
if anchor not in s:
    raise SystemExit("globals anchor not found")
s = s.replace(anchor, globals_block, 1)

old = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,
                           const char *text) {
  markConnectionActive(from); // in case this is from a server, and we have a connection
  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);
}'''
new = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,
                           const char *text) {
  markConnectionActive(from); // in case this is from a server, and we have a connection

  const char* gpio_reply = nullptr;
  char gpio_reply_buf[96];
  bool gpio_command_recognized = false;

#ifdef REMOTE_GPIO_OUT1
  if (strcmp(text, "OUT1 ON") == 0) {
    gpio_out1_timer_expiry = 0;
    gpio_out1_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT1, HIGH);
    gpio_reply = "OUT1 = ON";
    gpio_command_recognized = true;
  } else if (strcmp(text, "OUT1 OFF") == 0) {
    gpio_out1_timer_expiry = 0;
    gpio_out1_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT1, LOW);
    gpio_reply = "OUT1 = OFF";
    gpio_command_recognized = true;
  } else if (strncmp(text, "OUT1 TIMER", 10) == 0 && (text[10] == 0 || text[10] == ' ')) {
    unsigned long seconds = 5;
    bool valid = true;
    if (text[10] == ' ') {
      char *endptr = nullptr;
      seconds = strtoul(text + 11, &endptr, 10);
      valid = (endptr != text + 11 && *endptr == 0 && seconds >= 1 && seconds <= 3600);
    }
    gpio_command_recognized = true;
    if (valid) {
      digitalWrite(REMOTE_GPIO_OUT1, HIGH);
      gpio_out1_timer_expiry = futureMillis(seconds * 1000UL);
      gpio_out1_timer_contact = from;
      gpio_out1_timer_contact_valid = true;
      snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT1 = ON (TIMER %luS)", seconds);
      gpio_reply = gpio_reply_buf;
    } else {
      gpio_reply = "OUT1 TIMER: USE 1-3600S";
    }
  }
#endif

#ifdef REMOTE_GPIO_OUT2
  if (strcmp(text, "OUT2 ON") == 0) {
    gpio_out2_timer_expiry = 0;
    gpio_out2_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT2, HIGH);
    gpio_reply = "OUT2 = ON";
    gpio_command_recognized = true;
  } else if (strcmp(text, "OUT2 OFF") == 0) {
    gpio_out2_timer_expiry = 0;
    gpio_out2_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT2, LOW);
    gpio_reply = "OUT2 = OFF";
    gpio_command_recognized = true;
  } else if (strncmp(text, "OUT2 TIMER", 10) == 0 && (text[10] == 0 || text[10] == ' ')) {
    unsigned long seconds = 5;
    bool valid = true;
    if (text[10] == ' ') {
      char *endptr = nullptr;
      seconds = strtoul(text + 11, &endptr, 10);
      valid = (endptr != text + 11 && *endptr == 0 && seconds >= 1 && seconds <= 3600);
    }
    gpio_command_recognized = true;
    if (valid) {
      digitalWrite(REMOTE_GPIO_OUT2, HIGH);
      gpio_out2_timer_expiry = futureMillis(seconds * 1000UL);
      gpio_out2_timer_contact = from;
      gpio_out2_timer_contact_valid = true;
      snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT2 = ON (TIMER %luS)", seconds);
      gpio_reply = gpio_reply_buf;
    } else {
      gpio_reply = "OUT2 TIMER: USE 1-3600S";
    }
  }
#endif

  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {
    const char* out1 = "NA";
    const char* out2 = "NA";
    const char* in1 = "NA";
    const char* in2 = "NA";
#ifdef REMOTE_GPIO_OUT1
    out1 = digitalRead(REMOTE_GPIO_OUT1) == HIGH ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_OUT2
    out2 = digitalRead(REMOTE_GPIO_OUT2) == HIGH ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_IN1
    in1 = gpio_in1_stable == LOW ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_IN2
    in2 = gpio_in2_stable == LOW ? "ON" : "OFF";
#endif
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf),
             "OUT1=%s | OUT2=%s | IN1=%s | IN2=%s", out1, out2, in1, in2);
    gpio_reply = gpio_reply_buf;
    gpio_command_recognized = true;
  }

  if (gpio_command_recognized) {
    gpio_notify_contact = from;
    gpio_notify_contact_valid = true;
  }

  if (gpio_reply) {
    uint32_t expected_ack = 0;
    uint32_t est_timeout = 0;
    sendMessage(from, getRTCClock()->getCurrentTimeUnique(), 0,
                gpio_reply, expected_ack, est_timeout);
  }

  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);
}'''
if old not in s:
    raise SystemExit("onMessageRecv anchor not found")
s = s.replace(old, new, 1)

old = '''void MyMesh::begin(bool has_display) {
  BaseChatMesh::begin();'''
new = '''void MyMesh::begin(bool has_display) {
#ifdef REMOTE_GPIO_OUT1
  digitalWrite(REMOTE_GPIO_OUT1, LOW);
  pinMode(REMOTE_GPIO_OUT1, OUTPUT);
  gpio_out1_timer_expiry = 0;
  gpio_out1_timer_contact_valid = false;
#endif
#ifdef REMOTE_GPIO_OUT2
  digitalWrite(REMOTE_GPIO_OUT2, LOW);
  pinMode(REMOTE_GPIO_OUT2, OUTPUT);
  gpio_out2_timer_expiry = 0;
  gpio_out2_timer_contact_valid = false;
#endif
#ifdef REMOTE_GPIO_IN1
  pinMode(REMOTE_GPIO_IN1, INPUT_PULLUP);
  gpio_in1_stable = digitalRead(REMOTE_GPIO_IN1);
  gpio_in1_raw = gpio_in1_stable;
  gpio_in1_debounce_expiry = 0;
#endif
#ifdef REMOTE_GPIO_IN2
  pinMode(REMOTE_GPIO_IN2, INPUT_PULLUP);
  gpio_in2_stable = digitalRead(REMOTE_GPIO_IN2);
  gpio_in2_raw = gpio_in2_stable;
  gpio_in2_debounce_expiry = 0;
#endif
  gpio_notify_contact_valid = false;
  BaseChatMesh::begin();'''
if old not in s:
    raise SystemExit("begin anchor not found")
s = s.replace(old, new, 1)

old = '''void MyMesh::loop() {
  BaseChatMesh::loop();

  if (_cli_rescue) {'''
new = '''void MyMesh::loop() {
  BaseChatMesh::loop();

#ifdef REMOTE_GPIO_OUT1
  if (gpio_out1_timer_expiry && millisHasNowPassed(gpio_out1_timer_expiry)) {
    digitalWrite(REMOTE_GPIO_OUT1, LOW);
    gpio_out1_timer_expiry = 0;
    if (gpio_out1_timer_contact_valid) {
      uint32_t expected_ack = 0;
      uint32_t est_timeout = 0;
      sendMessage(gpio_out1_timer_contact, getRTCClock()->getCurrentTimeUnique(), 0,
                  "OUT1 = OFF (TIMER DONE)", expected_ack, est_timeout);
      gpio_out1_timer_contact_valid = false;
    }
  }
#endif
#ifdef REMOTE_GPIO_OUT2
  if (gpio_out2_timer_expiry && millisHasNowPassed(gpio_out2_timer_expiry)) {
    digitalWrite(REMOTE_GPIO_OUT2, LOW);
    gpio_out2_timer_expiry = 0;
    if (gpio_out2_timer_contact_valid) {
      uint32_t expected_ack = 0;
      uint32_t est_timeout = 0;
      sendMessage(gpio_out2_timer_contact, getRTCClock()->getCurrentTimeUnique(), 0,
                  "OUT2 = OFF (TIMER DONE)", expected_ack, est_timeout);
      gpio_out2_timer_contact_valid = false;
    }
  }
#endif

#ifdef REMOTE_GPIO_IN1
  {
    int raw = digitalRead(REMOTE_GPIO_IN1);
    if (raw != gpio_in1_raw) {
      gpio_in1_raw = raw;
      gpio_in1_debounce_expiry = futureMillis(50);
    }
    if (gpio_in1_debounce_expiry && millisHasNowPassed(gpio_in1_debounce_expiry)) {
      gpio_in1_debounce_expiry = 0;
      if (gpio_in1_stable != gpio_in1_raw) {
        gpio_in1_stable = gpio_in1_raw;
        if (gpio_notify_contact_valid) {
          uint32_t expected_ack = 0;
          uint32_t est_timeout = 0;
          sendMessage(gpio_notify_contact, getRTCClock()->getCurrentTimeUnique(), 0,
                      gpio_in1_stable == LOW ? "IN1 = ON" : "IN1 = OFF",
                      expected_ack, est_timeout);
        }
      }
    }
  }
#endif
#ifdef REMOTE_GPIO_IN2
  {
    int raw = digitalRead(REMOTE_GPIO_IN2);
    if (raw != gpio_in2_raw) {
      gpio_in2_raw = raw;
      gpio_in2_debounce_expiry = futureMillis(50);
    }
    if (gpio_in2_debounce_expiry && millisHasNowPassed(gpio_in2_debounce_expiry)) {
      gpio_in2_debounce_expiry = 0;
      if (gpio_in2_stable != gpio_in2_raw) {
        gpio_in2_stable = gpio_in2_raw;
        if (gpio_notify_contact_valid) {
          uint32_t expected_ack = 0;
          uint32_t est_timeout = 0;
          sendMessage(gpio_notify_contact, getRTCClock()->getCurrentTimeUnique(), 0,
                      gpio_in2_stable == LOW ? "IN2 = ON" : "IN2 = OFF",
                      expected_ack, est_timeout);
        }
      }
    }
  }
#endif

  if (_cli_rescue) {'''
if old not in s:
    raise SystemExit("loop anchor not found")
s = s.replace(old, new, 1)
p.write_text(s)

p = Path("variants/heltec_v3/platformio.ini")
s = p.read_text()
for env in ("Heltec_v3_companion_radio_usb", "Heltec_v3_companion_radio_ble"):
    anchor = f"[env:{env}]\nextends = Heltec_lora32_v3\nbuild_flags =\n  ${{Heltec_lora32_v3.build_flags}}\n"
    replacement = anchor + (
        "  -D REMOTE_GPIO_OUT1=4\n"
        "  -D REMOTE_GPIO_OUT2=5\n"
        "  -D REMOTE_GPIO_IN1=6\n"
        "  -D REMOTE_GPIO_IN2=7\n"
    )
    if anchor not in s:
        raise SystemExit(f"{env} anchor not found")
    s = s.replace(anchor, replacement, 1)
p.write_text(s)

print("Heltec V3 GPIO V3 patch: OUT1=4 OUT2=5 IN1=6 IN2=7 STATUS + input change notifications")
