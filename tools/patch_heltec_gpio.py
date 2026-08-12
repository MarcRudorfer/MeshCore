from pathlib import Path

# Patch Companion message handling, safe boot state and configurable non-blocking timers.
p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

anchor = '#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n'
timer_globals = '''#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n\n#ifdef REMOTE_GPIO_OUT1\nstatic unsigned long gpio_out1_timer_expiry = 0;\nstatic ContactInfo* gpio_out1_timer_contact = nullptr;\n#endif\n#ifdef REMOTE_GPIO_OUT2\nstatic unsigned long gpio_out2_timer_expiry = 0;\nstatic ContactInfo* gpio_out2_timer_contact = nullptr;\n#endif\n'''
if anchor not in s:
    raise SystemExit("timer globals anchor not found")
s = s.replace(anchor, timer_globals, 1)

old = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,
                           const char *text) {
  markConnectionActive(from); // in case this is from a server, and we have a connection
  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);
}'''
new = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,
                           const char *text) {
  markConnectionActive(from); // in case this is from a server, and we have a connection

  const char* gpio_reply = nullptr;
  char gpio_reply_buf[48];

#ifdef REMOTE_GPIO_OUT1
  if (strcmp(text, "OUT1 ON") == 0) {
    gpio_out1_timer_expiry = 0;
    gpio_out1_timer_contact = nullptr;
    digitalWrite(REMOTE_GPIO_OUT1, HIGH);
    gpio_reply = "OUT1 = ON";
  } else if (strcmp(text, "OUT1 OFF") == 0) {
    gpio_out1_timer_expiry = 0;
    gpio_out1_timer_contact = nullptr;
    digitalWrite(REMOTE_GPIO_OUT1, LOW);
    gpio_reply = "OUT1 = OFF";
  } else if (strncmp(text, "OUT1 TIMER", 10) == 0 && (text[10] == 0 || text[10] == ' ')) {
    unsigned long seconds = 5;
    bool valid = true;
    if (text[10] == ' ') {
      char *endptr = nullptr;
      seconds = strtoul(text + 11, &endptr, 10);
      valid = (endptr != text + 11 && *endptr == 0 && seconds >= 1 && seconds <= 3600);
    }
    if (valid) {
      digitalWrite(REMOTE_GPIO_OUT1, HIGH);
      gpio_out1_timer_expiry = futureMillis(seconds * 1000UL);
      gpio_out1_timer_contact = const_cast<ContactInfo*>(&from);
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
    gpio_out2_timer_contact = nullptr;
    digitalWrite(REMOTE_GPIO_OUT2, HIGH);
    gpio_reply = "OUT2 = ON";
  } else if (strcmp(text, "OUT2 OFF") == 0) {
    gpio_out2_timer_expiry = 0;
    gpio_out2_timer_contact = nullptr;
    digitalWrite(REMOTE_GPIO_OUT2, LOW);
    gpio_reply = "OUT2 = OFF";
  } else if (strncmp(text, "OUT2 TIMER", 10) == 0 && (text[10] == 0 || text[10] == ' ')) {
    unsigned long seconds = 5;
    bool valid = true;
    if (text[10] == ' ') {
      char *endptr = nullptr;
      seconds = strtoul(text + 11, &endptr, 10);
      valid = (endptr != text + 11 && *endptr == 0 && seconds >= 1 && seconds <= 3600);
    }
    if (valid) {
      digitalWrite(REMOTE_GPIO_OUT2, HIGH);
      gpio_out2_timer_expiry = futureMillis(seconds * 1000UL);
      gpio_out2_timer_contact = const_cast<ContactInfo*>(&from);
      snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT2 = ON (TIMER %luS)", seconds);
      gpio_reply = gpio_reply_buf;
    } else {
      gpio_reply = "OUT2 TIMER: USE 1-3600S";
    }
  }
#endif

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
  gpio_out1_timer_contact = nullptr;
#endif
#ifdef REMOTE_GPIO_OUT2
  digitalWrite(REMOTE_GPIO_OUT2, LOW);
  pinMode(REMOTE_GPIO_OUT2, OUTPUT);
  gpio_out2_timer_expiry = 0;
  gpio_out2_timer_contact = nullptr;
#endif
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
    if (gpio_out1_timer_contact) {
      uint32_t expected_ack = 0;
      uint32_t est_timeout = 0;
      sendMessage(*gpio_out1_timer_contact, getRTCClock()->getCurrentTimeUnique(), 0,
                  "OUT1 = OFF (TIMER DONE)", expected_ack, est_timeout);
      gpio_out1_timer_contact = nullptr;
    }
  }
#endif
#ifdef REMOTE_GPIO_OUT2
  if (gpio_out2_timer_expiry && millisHasNowPassed(gpio_out2_timer_expiry)) {
    digitalWrite(REMOTE_GPIO_OUT2, LOW);
    gpio_out2_timer_expiry = 0;
    if (gpio_out2_timer_contact) {
      uint32_t expected_ack = 0;
      uint32_t est_timeout = 0;
      sendMessage(*gpio_out2_timer_contact, getRTCClock()->getCurrentTimeUnique(), 0,
                  "OUT2 = OFF (TIMER DONE)", expected_ack, est_timeout);
      gpio_out2_timer_contact = nullptr;
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
    replacement = anchor + "  -D REMOTE_GPIO_OUT1=4\n  -D REMOTE_GPIO_OUT2=5\n"
    if anchor not in s:
        raise SystemExit(f"{env} anchor not found")
    s = s.replace(anchor, replacement, 1)
p.write_text(s)

print("Heltec V3 GPIO V2 patch: OUT1=GPIO4, OUT2=GPIO5, TIMER default=5s, configurable=1..3600s")
