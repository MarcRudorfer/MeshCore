from pathlib import Path

# XIAO nRF52840 GPIO V4
# D6 = IN1, D7 = IN2, both INPUT_PULLUP.
# Commands: IN1, IN2, STATUS.
# Automatic debounced HIGH/LOW notification for both inputs to the most recently interacting contact.

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = '#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n'
globals_block = '''#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n\n#ifdef REMOTE_GPIO_IN1\nstatic int gpio_in1_stable_state = HIGH;\nstatic int gpio_in1_last_raw_state = HIGH;\nstatic unsigned long gpio_in1_last_change_ms = 0;\n#endif\n#ifdef REMOTE_GPIO_IN2\nstatic int gpio_in2_stable_state = HIGH;\nstatic int gpio_in2_last_raw_state = HIGH;\nstatic unsigned long gpio_in2_last_change_ms = 0;\n#endif\nstatic ContactInfo gpio_input_notify_contact;\nstatic bool gpio_input_notify_contact_valid = false;\nstatic const unsigned long GPIO_INPUT_DEBOUNCE_MS = 60;\n'''
if anchor not in s:
    raise SystemExit('globals anchor not found')
s = s.replace(anchor, globals_block, 1)

old = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,\n                           const char *text) {\n  markConnectionActive(from); // in case this is from a server, and we have a connection\n  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);\n}'''
new = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,\n                           const char *text) {\n  markConnectionActive(from); // in case this is from a server, and we have a connection\n\n  gpio_input_notify_contact = from;\n  gpio_input_notify_contact_valid = true;\n\n  const char* gpio_reply = nullptr;\n  char gpio_reply_buf[128];\n\n#ifdef REMOTE_GPIO_IN1\n  if (strcmp(text, "IN1") == 0 || strcmp(text, "IN1?") == 0 || strcmp(text, "IN1 ?") == 0) {\n    gpio_reply = digitalRead(REMOTE_GPIO_IN1) == HIGH ? "IN1 = HIGH" : "IN1 = LOW";\n  }\n#endif\n#ifdef REMOTE_GPIO_IN2\n  if (strcmp(text, "IN2") == 0 || strcmp(text, "IN2?") == 0 || strcmp(text, "IN2 ?") == 0) {\n    gpio_reply = digitalRead(REMOTE_GPIO_IN2) == HIGH ? "IN2 = HIGH" : "IN2 = LOW";\n  }\n#endif\n\n  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {\n    const char* in1 = "NA";\n    const char* in2 = "NA";\n#ifdef REMOTE_GPIO_IN1\n    in1 = digitalRead(REMOTE_GPIO_IN1) == HIGH ? "HIGH" : "LOW";\n#endif\n#ifdef REMOTE_GPIO_IN2\n    in2 = digitalRead(REMOTE_GPIO_IN2) == HIGH ? "HIGH" : "LOW";\n#endif\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "IN1=%s | IN2=%s", in1, in2);\n    gpio_reply = gpio_reply_buf;\n  }\n\n  if (gpio_reply) {\n    uint32_t expected_ack = 0, est_timeout = 0;\n    sendMessage(from, getRTCClock()->getCurrentTimeUnique(), 0, gpio_reply, expected_ack, est_timeout);\n  }\n\n  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);\n}'''
if old not in s:
    raise SystemExit('onMessageRecv anchor not found')
s = s.replace(old, new, 1)

old = '''void MyMesh::begin(bool has_display) {\n  BaseChatMesh::begin();'''
new = '''void MyMesh::begin(bool has_display) {\n#ifdef REMOTE_GPIO_IN1\n  pinMode(REMOTE_GPIO_IN1, INPUT_PULLUP);\n  gpio_in1_stable_state = digitalRead(REMOTE_GPIO_IN1);\n  gpio_in1_last_raw_state = gpio_in1_stable_state;\n  gpio_in1_last_change_ms = millis();\n#endif\n#ifdef REMOTE_GPIO_IN2\n  pinMode(REMOTE_GPIO_IN2, INPUT_PULLUP);\n  gpio_in2_stable_state = digitalRead(REMOTE_GPIO_IN2);\n  gpio_in2_last_raw_state = gpio_in2_stable_state;\n  gpio_in2_last_change_ms = millis();\n#endif\n  BaseChatMesh::begin();'''
if old not in s:
    raise SystemExit('begin anchor not found')
s = s.replace(old, new, 1)

service_method = '''\nvoid MyMesh::processGpioInputs() {\n  const unsigned long now = millis();\n#ifdef REMOTE_GPIO_IN1\n  const int raw1 = digitalRead(REMOTE_GPIO_IN1);\n  if (raw1 != gpio_in1_last_raw_state) { gpio_in1_last_raw_state = raw1; gpio_in1_last_change_ms = now; }\n  if (raw1 != gpio_in1_stable_state && (unsigned long)(now - gpio_in1_last_change_ms) >= GPIO_INPUT_DEBOUNCE_MS) {\n    gpio_in1_stable_state = raw1;\n    if (gpio_input_notify_contact_valid) {\n      uint32_t expected_ack = 0, est_timeout = 0;\n      sendMessage(gpio_input_notify_contact, getRTCClock()->getCurrentTimeUnique(), 0,\n                  gpio_in1_stable_state == HIGH ? "IN1 = HIGH" : "IN1 = LOW", expected_ack, est_timeout);\n    }\n  }\n#endif\n#ifdef REMOTE_GPIO_IN2\n  const int raw2 = digitalRead(REMOTE_GPIO_IN2);\n  if (raw2 != gpio_in2_last_raw_state) { gpio_in2_last_raw_state = raw2; gpio_in2_last_change_ms = now; }\n  if (raw2 != gpio_in2_stable_state && (unsigned long)(now - gpio_in2_last_change_ms) >= GPIO_INPUT_DEBOUNCE_MS) {\n    gpio_in2_stable_state = raw2;\n    if (gpio_input_notify_contact_valid) {\n      uint32_t expected_ack = 0, est_timeout = 0;\n      sendMessage(gpio_input_notify_contact, getRTCClock()->getCurrentTimeUnique(), 0,\n                  gpio_in2_stable_state == HIGH ? "IN2 = HIGH" : "IN2 = LOW", expected_ack, est_timeout);\n    }\n  }\n#endif\n}\n'''
s += service_method
p.write_text(s)

p = Path('examples/companion_radio/MyMesh.h')
s = p.read_text()
anchor = '  void loop();\n'
if anchor not in s: raise SystemExit('MyMesh.h loop anchor not found')
s = s.replace(anchor, anchor + '  void processGpioInputs();\n', 1)
p.write_text(s)

p = Path('examples/companion_radio/main.cpp')
s = p.read_text()
if '  sensors.begin();\n' not in s: raise SystemExit('sensors.begin anchor not found')
s = s.replace('  sensors.begin();\n', '#ifndef XIAO_GPIO_VARIANT\n  sensors.begin();\n#endif\n', 1)
if '  sensors.loop();\n' not in s: raise SystemExit('sensors.loop anchor not found')
s = s.replace('  sensors.loop();\n', '#ifndef XIAO_GPIO_VARIANT\n  sensors.loop();\n#else\n  the_mesh.processGpioInputs();\n#endif\n', 1)
p.write_text(s)

print('XIAO GPIO V4: D6=IN1, D7=IN2, INPUT_PULLUP, debounce=60ms, automatic notifications')
