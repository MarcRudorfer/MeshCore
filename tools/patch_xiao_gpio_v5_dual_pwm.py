from pathlib import Path

# XIAO nRF52840 GPIO V5
# D6 = PWM1, D7 = PWM2 for external MOSFET drivers.
# Mesh commands use percentages 0..100.

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = '#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n'
block = '''#define MAX_SIGN_DATA_LEN               (8 * 1024) // 8K\n\n#ifdef REMOTE_PWM_OUT1\nstatic uint8_t gpio_pwm1_percent = 0;\n#endif\n#ifdef REMOTE_PWM_OUT2\nstatic uint8_t gpio_pwm2_percent = 0;\n#endif\n\nstatic void setGpioPwmPercent(uint8_t pin, uint8_t percent) {\n  if (percent > 100) percent = 100;\n  // Arduino nRF52 analogWrite: 8-bit duty cycle.\n  const uint8_t duty = (uint8_t)(((uint16_t)percent * 255U + 50U) / 100U);\n  analogWrite(pin, duty);\n}\n'''
if anchor not in s: raise SystemExit('globals anchor not found')
s = s.replace(anchor, block, 1)

old = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,\n                           const char *text) {\n  markConnectionActive(from); // in case this is from a server, and we have a connection\n  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);\n}'''
new = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,\n                           const char *text) {\n  markConnectionActive(from); // in case this is from a server, and we have a connection\n\n  const char* gpio_reply = nullptr;\n  char gpio_reply_buf[128];\n  int pwm_value = -1;\n\n#ifdef REMOTE_PWM_OUT1\n  if (strcmp(text, "PWM1 OFF") == 0) {\n    gpio_pwm1_percent = 0; setGpioPwmPercent(REMOTE_PWM_OUT1, 0); gpio_reply = "PWM1 = 0%";\n  } else if (strcmp(text, "PWM1 ON") == 0) {\n    gpio_pwm1_percent = 100; setGpioPwmPercent(REMOTE_PWM_OUT1, 100); gpio_reply = "PWM1 = 100%";\n  } else if (sscanf(text, "PWM1 %d", &pwm_value) == 1 && pwm_value >= 0 && pwm_value <= 100) {\n    gpio_pwm1_percent = (uint8_t)pwm_value; setGpioPwmPercent(REMOTE_PWM_OUT1, gpio_pwm1_percent);\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM1 = %u%%", gpio_pwm1_percent); gpio_reply = gpio_reply_buf;\n  } else if (strcmp(text, "PWM1") == 0 || strcmp(text, "PWM1?") == 0) {\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM1 = %u%%", gpio_pwm1_percent); gpio_reply = gpio_reply_buf;\n  }\n#endif\n#ifdef REMOTE_PWM_OUT2\n  if (strcmp(text, "PWM2 OFF") == 0) {\n    gpio_pwm2_percent = 0; setGpioPwmPercent(REMOTE_PWM_OUT2, 0); gpio_reply = "PWM2 = 0%";\n  } else if (strcmp(text, "PWM2 ON") == 0) {\n    gpio_pwm2_percent = 100; setGpioPwmPercent(REMOTE_PWM_OUT2, 100); gpio_reply = "PWM2 = 100%";\n  } else if (sscanf(text, "PWM2 %d", &pwm_value) == 1 && pwm_value >= 0 && pwm_value <= 100) {\n    gpio_pwm2_percent = (uint8_t)pwm_value; setGpioPwmPercent(REMOTE_PWM_OUT2, gpio_pwm2_percent);\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM2 = %u%%", gpio_pwm2_percent); gpio_reply = gpio_reply_buf;\n  } else if (strcmp(text, "PWM2") == 0 || strcmp(text, "PWM2?") == 0) {\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM2 = %u%%", gpio_pwm2_percent); gpio_reply = gpio_reply_buf;\n  }\n#endif\n\n  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {\n#ifdef REMOTE_PWM_OUT1\n#ifdef REMOTE_PWM_OUT2\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM1=%u%% | PWM2=%u%%", gpio_pwm1_percent, gpio_pwm2_percent);\n#else\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM1=%u%%", gpio_pwm1_percent);\n#endif\n#else\n#ifdef REMOTE_PWM_OUT2\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM2=%u%%", gpio_pwm2_percent);\n#else\n    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM unavailable");\n#endif\n#endif\n    gpio_reply = gpio_reply_buf;\n  }\n\n  if (gpio_reply) {\n    uint32_t expected_ack = 0, est_timeout = 0;\n    sendMessage(from, getRTCClock()->getCurrentTimeUnique(), 0, gpio_reply, expected_ack, est_timeout);\n  }\n\n  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);\n}'''
if old not in s: raise SystemExit('onMessageRecv anchor not found')
s = s.replace(old, new, 1)

old = '''void MyMesh::begin(bool has_display) {\n  BaseChatMesh::begin();'''
new = '''void MyMesh::begin(bool has_display) {\n#ifdef REMOTE_PWM_OUT1\n  pinMode(REMOTE_PWM_OUT1, OUTPUT);\n  setGpioPwmPercent(REMOTE_PWM_OUT1, 0);\n#endif\n#ifdef REMOTE_PWM_OUT2\n  pinMode(REMOTE_PWM_OUT2, OUTPUT);\n  setGpioPwmPercent(REMOTE_PWM_OUT2, 0);\n#endif\n  BaseChatMesh::begin();'''
if old not in s: raise SystemExit('begin anchor not found')
s = s.replace(old, new, 1)
p.write_text(s)

# Disable sensors on this GPIO variant because D6/D7 are reclaimed from Wire.
p = Path('examples/companion_radio/main.cpp')
s = p.read_text()
if '  sensors.begin();\n' not in s: raise SystemExit('sensors.begin anchor not found')
s = s.replace('  sensors.begin();\n', '#ifndef XIAO_GPIO_VARIANT\n  sensors.begin();\n#endif\n', 1)
if '  sensors.loop();\n' not in s: raise SystemExit('sensors.loop anchor not found')
s = s.replace('  sensors.loop();\n', '#ifndef XIAO_GPIO_VARIANT\n  sensors.loop();\n#endif\n', 1)
p.write_text(s)

print('XIAO GPIO V5: D6=PWM1, D7=PWM2, commands PWM1/PWM2 0..100, ON/OFF, STATUS')
