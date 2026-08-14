from pathlib import Path

# XIAO nRF52840 GPIO V2
# D6 = IN1 (INPUT_PULLUP), D7 = OUT1.
# Stable V1/Build-10 hardware approach is retained: Wire is remapped by workflow to 16/17.
# Commands: IN1, STATUS, OUT1 ON/OFF, OUT1 <1..86400 seconds>.

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = '#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n'
globals_block = '''#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n\n#ifdef REMOTE_GPIO_OUT1\nstatic unsigned long gpio_out1_timer_expiry = 0;\nstatic ContactInfo gpio_out1_timer_contact;\nstatic bool gpio_out1_timer_contact_valid = false;\n#endif\n'''
if anchor not in s:
    raise SystemExit('globals anchor not found')
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
  char gpio_reply_buf[128];

#ifdef REMOTE_GPIO_OUT1
  if (strcmp(text, "OUT1 ON") == 0) {
    gpio_out1_timer_expiry = 0;
    gpio_out1_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT1, HIGH);
    gpio_reply = "OUT1 = ON";
  } else if (strcmp(text, "OUT1 OFF") == 0) {
    gpio_out1_timer_expiry = 0;
    gpio_out1_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT1, LOW);
    gpio_reply = "OUT1 = OFF";
  } else if (strncmp(text, "OUT1 ", 5) == 0) {
    const char* p = text + 5;
    char* endp = nullptr;
    unsigned long sec = strtoul(p, &endp, 10);
    if (endp != p && *endp == '\\0' && sec > 0 && sec <= 86400UL) {
      digitalWrite(REMOTE_GPIO_OUT1, HIGH);
      gpio_out1_timer_expiry = millis() + sec * 1000UL;
      gpio_out1_timer_contact = from;
      gpio_out1_timer_contact_valid = true;
      snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT1 = ON (%lus Timer)", sec);
      gpio_reply = gpio_reply_buf;
    }
  }
#endif

#ifdef REMOTE_GPIO_IN1
  if (strcmp(text, "IN1") == 0 || strcmp(text, "IN1?") == 0 || strcmp(text, "IN1 ?") == 0) {
    gpio_reply = digitalRead(REMOTE_GPIO_IN1) == HIGH ? "IN1 = HIGH" : "IN1 = LOW";
  }
#endif

  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {
    const char* in1 = "NA";
    char out1[40] = "NA";
#ifdef REMOTE_GPIO_IN1
    in1 = digitalRead(REMOTE_GPIO_IN1) == HIGH ? "HIGH" : "LOW";
#endif
#ifdef REMOTE_GPIO_OUT1
    if (digitalRead(REMOTE_GPIO_OUT1) == HIGH && gpio_out1_timer_expiry != 0) {
      unsigned long rem = ((long)(gpio_out1_timer_expiry - millis()) > 0) ? (gpio_out1_timer_expiry - millis() + 999UL) / 1000UL : 0;
      snprintf(out1, sizeof(out1), "ON(%lus)", rem);
    } else strcpy(out1, digitalRead(REMOTE_GPIO_OUT1) == HIGH ? "ON" : "OFF");
#endif
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "IN1=%s | OUT1=%s", in1, out1);
    gpio_reply = gpio_reply_buf;
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
    raise SystemExit('onMessageRecv anchor not found')
s = s.replace(old, new, 1)

old = '''void MyMesh::begin(bool has_display) {
  BaseChatMesh::begin();'''
new = '''void MyMesh::begin(bool has_display) {
#ifdef REMOTE_GPIO_IN1
  pinMode(REMOTE_GPIO_IN1, INPUT_PULLUP);
#endif
#ifdef REMOTE_GPIO_OUT1
  digitalWrite(REMOTE_GPIO_OUT1, LOW);
  pinMode(REMOTE_GPIO_OUT1, OUTPUT);
#endif
  BaseChatMesh::begin();'''
if old not in s:
    raise SystemExit('begin anchor not found')
s = s.replace(old, new, 1)

# Timer service remains fully inside MyMesh.
timer_method = '''\nvoid MyMesh::processGpioTimers() {\n#ifdef REMOTE_GPIO_OUT1\n  if (gpio_out1_timer_expiry != 0 && (long)(millis() - gpio_out1_timer_expiry) >= 0) {\n    digitalWrite(REMOTE_GPIO_OUT1, LOW);\n    gpio_out1_timer_expiry = 0;\n    if (gpio_out1_timer_contact_valid) {\n      uint32_t expected_ack = 0, est_timeout = 0;\n      sendMessage(gpio_out1_timer_contact, getRTCClock()->getCurrentTimeUnique(), 0,\n                  "OUT1 = OFF (Timer beendet)", expected_ack, est_timeout);\n      gpio_out1_timer_contact_valid = false;\n    }\n  }\n#endif\n}\n'''
s += timer_method
p.write_text(s)

p = Path('examples/companion_radio/MyMesh.h')
s = p.read_text()
anchor = '  void loop();\n'
if anchor not in s:
    raise SystemExit('MyMesh.h loop anchor not found')
s = s.replace(anchor, anchor + '  void processGpioTimers();\n', 1)
p.write_text(s)

# Disable sensor polling for this GPIO build and service output timer instead.
p = Path('examples/companion_radio/main.cpp')
s = p.read_text()
if '  sensors.begin();\n' not in s:
    raise SystemExit('sensors.begin anchor not found')
s = s.replace('  sensors.begin();\n', '#ifndef XIAO_GPIO_VARIANT\n  sensors.begin();\n#endif\n', 1)
if '  sensors.loop();\n' not in s:
    raise SystemExit('sensors.loop anchor not found')
s = s.replace('  sensors.loop();\n', '#ifndef XIAO_GPIO_VARIANT\n  sensors.loop();\n#else\n  the_mesh.processGpioTimers();\n#endif\n', 1)
p.write_text(s)

print('XIAO GPIO V2: D6=IN1 INPUT_PULLUP, D7=OUT1, timer 1..86400s')
