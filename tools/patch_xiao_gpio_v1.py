from pathlib import Path

# XIAO nRF52840 GPIO V1: D6/D7 are repurposed from I2C to two remote-controlled outputs.
# Commands: OUT1 ON/OFF, OUT2 ON/OFF, STATUS. Replies are sent back as normal MeshCore messages.
# Build 5 keeps the normal board Wire startup, then explicitly releases the I2C peripheral with Wire.end().

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = '#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n'
globals_block = '''#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n\n#ifdef REMOTE_GPIO_OUT1\nstatic unsigned long gpio_out1_timer_expiry = 0;\nstatic ContactInfo gpio_out1_timer_contact;\nstatic bool gpio_out1_timer_contact_valid = false;\n#endif\n#ifdef REMOTE_GPIO_OUT2\nstatic unsigned long gpio_out2_timer_expiry = 0;\nstatic ContactInfo gpio_out2_timer_contact;\nstatic bool gpio_out2_timer_contact_valid = false;\n#endif\n'''
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
  char gpio_reply_buf[96];

#ifdef REMOTE_GPIO_OUT1
  if (strcmp(text, "OUT1 ON") == 0) {
    digitalWrite(REMOTE_GPIO_OUT1, HIGH);
    gpio_reply = "OUT1 = ON";
  } else if (strcmp(text, "OUT1 OFF") == 0) {
    digitalWrite(REMOTE_GPIO_OUT1, LOW);
    gpio_reply = "OUT1 = OFF";
  }
#endif

#ifdef REMOTE_GPIO_OUT2
  if (strcmp(text, "OUT2 ON") == 0) {
    digitalWrite(REMOTE_GPIO_OUT2, HIGH);
    gpio_reply = "OUT2 = ON";
  } else if (strcmp(text, "OUT2 OFF") == 0) {
    digitalWrite(REMOTE_GPIO_OUT2, LOW);
    gpio_reply = "OUT2 = OFF";
  }
#endif

  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {
    const char* out1 = "NA";
    const char* out2 = "NA";
#ifdef REMOTE_GPIO_OUT1
    out1 = digitalRead(REMOTE_GPIO_OUT1) == HIGH ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_OUT2
    out2 = digitalRead(REMOTE_GPIO_OUT2) == HIGH ? "ON" : "OFF";
#endif
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT1=%s | OUT2=%s", out1, out2);
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
#ifdef REMOTE_GPIO_OUT1
  digitalWrite(REMOTE_GPIO_OUT1, LOW);
  pinMode(REMOTE_GPIO_OUT1, OUTPUT);
#endif
#ifdef REMOTE_GPIO_OUT2
  digitalWrite(REMOTE_GPIO_OUT2, LOW);
  pinMode(REMOTE_GPIO_OUT2, OUTPUT);
#endif
  BaseChatMesh::begin();'''
if old not in s:
    raise SystemExit('begin anchor not found')
s = s.replace(old, new, 1)
p.write_text(s)

# Keep the stock board.begin() path (including Wire.begin), then release TWIM so D6/D7
# are no longer owned by the I2C peripheral before MeshCore configures them as GPIO outputs.
p = Path('examples/companion_radio/main.cpp')
s = p.read_text()
inc = '#include <Mesh.h>\n'
if inc not in s:
    raise SystemExit('main include anchor not found')
s = s.replace(inc, inc + '#ifdef XIAO_GPIO_VARIANT\n#include <Wire.h>\n#endif\n', 1)
anchor = '  board.begin();\n'
if anchor not in s:
    raise SystemExit('board.begin anchor not found')
s = s.replace(anchor, anchor + '#ifdef XIAO_GPIO_VARIANT\n  Wire.end();  // release D6/D7 after normal board startup\n#endif\n', 1)

# Prevent sensor code from reinitialising I2C later.
if '  sensors.begin();\n' not in s:
    raise SystemExit('sensors.begin anchor not found')
s = s.replace('  sensors.begin();\n', '#ifndef XIAO_GPIO_VARIANT\n  sensors.begin();\n#endif\n', 1)
if '  sensors.loop();\n' not in s:
    raise SystemExit('sensors.loop anchor not found')
s = s.replace('  sensors.loop();\n', '#ifndef XIAO_GPIO_VARIANT\n  sensors.loop();\n#endif\n', 1)
p.write_text(s)

print('XIAO GPIO V1 Build 5: normal Wire startup, then Wire.end(); D6=OUT1 D7=OUT2')
