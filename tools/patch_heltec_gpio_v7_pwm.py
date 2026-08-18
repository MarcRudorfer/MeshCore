from pathlib import Path

# Heltec V3 GPIO V7 PWM extension
# Base: tested V6 7OUT Link Persistent
# PWM1 = GPIO19, PWM2 = GPIO20

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# Add PWM state + ESP32 Arduino LEDC helpers before existing GPIO globals.
anchor = '#ifdef REMOTE_GPIO_OUT1\nstatic unsigned long gpio_out1_timer_expiry = 0;'
block = '''#ifdef REMOTE_PWM_OUT1
static uint8_t gpio_pwm1_percent = 0;
#endif
#ifdef REMOTE_PWM_OUT2
static uint8_t gpio_pwm2_percent = 0;
#endif

static void setGpioPwmPercent(uint8_t pin, uint8_t percent) {
  if (percent > 100) percent = 100;
  // Arduino-ESP32 analogWrite uses LEDC PWM on supported output pins.
  const uint8_t duty = (uint8_t)(((uint16_t)percent * 255U + 50U) / 100U);
  analogWrite(pin, duty);
}

#ifdef REMOTE_GPIO_OUT1
static unsigned long gpio_out1_timer_expiry = 0;'''
if anchor not in s:
    raise SystemExit("GPIO globals anchor not found")
s = s.replace(anchor, block, 1)

# Add PWM commands immediately before STATUS so existing V6 GPIO commands stay unchanged.
status_anchor = '  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {\n'
pwm_commands = '''#ifdef REMOTE_PWM_OUT1
  if (strcmp(text, "PWM1 OFF") == 0) {
    gpio_pwm1_percent = 0; setGpioPwmPercent(REMOTE_PWM_OUT1, 0); gpio_reply = "PWM1 = 0%"; gpio_command_recognized = true;
  } else if (strcmp(text, "PWM1 ON") == 0) {
    gpio_pwm1_percent = 100; setGpioPwmPercent(REMOTE_PWM_OUT1, 100); gpio_reply = "PWM1 = 100%"; gpio_command_recognized = true;
  } else if (strcmp(text, "PWM1") == 0 || strcmp(text, "PWM1?") == 0) {
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM1 = %u%%", gpio_pwm1_percent); gpio_reply = gpio_reply_buf; gpio_command_recognized = true;
  } else if (strncmp(text, "PWM1 ", 5) == 0) {
    char *endptr = nullptr; long value = strtol(text + 5, &endptr, 10);
    if (endptr != text + 5 && *endptr == 0 && value >= 0 && value <= 100) {
      gpio_pwm1_percent = (uint8_t)value; setGpioPwmPercent(REMOTE_PWM_OUT1, gpio_pwm1_percent);
      snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM1 = %u%%", gpio_pwm1_percent); gpio_reply = gpio_reply_buf;
    } else gpio_reply = "PWM1: USE 0-100";
    gpio_command_recognized = true;
  }
#endif
#ifdef REMOTE_PWM_OUT2
  if (strcmp(text, "PWM2 OFF") == 0) {
    gpio_pwm2_percent = 0; setGpioPwmPercent(REMOTE_PWM_OUT2, 0); gpio_reply = "PWM2 = 0%"; gpio_command_recognized = true;
  } else if (strcmp(text, "PWM2 ON") == 0) {
    gpio_pwm2_percent = 100; setGpioPwmPercent(REMOTE_PWM_OUT2, 100); gpio_reply = "PWM2 = 100%"; gpio_command_recognized = true;
  } else if (strcmp(text, "PWM2") == 0 || strcmp(text, "PWM2?") == 0) {
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM2 = %u%%", gpio_pwm2_percent); gpio_reply = gpio_reply_buf; gpio_command_recognized = true;
  } else if (strncmp(text, "PWM2 ", 5) == 0) {
    char *endptr = nullptr; long value = strtol(text + 5, &endptr, 10);
    if (endptr != text + 5 && *endptr == 0 && value >= 0 && value <= 100) {
      gpio_pwm2_percent = (uint8_t)value; setGpioPwmPercent(REMOTE_PWM_OUT2, gpio_pwm2_percent);
      snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "PWM2 = %u%%", gpio_pwm2_percent); gpio_reply = gpio_reply_buf;
    } else gpio_reply = "PWM2: USE 0-100";
    gpio_command_recognized = true;
  }
#endif

'''
if status_anchor not in s:
    raise SystemExit("STATUS anchor not found")
s = s.replace(status_anchor, pwm_commands + status_anchor, 1)

# Extend V6 STATUS line with PWM values.
old = '    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "O1=%s O2=%s O3=%s O4=%s O5=%s O6=%s O7=%s | I1=%s I2=%s I3=%s I4=%s", out1,out2,out3,out4,out5,out6,out7,in1,in2,in3,in4);'
new = '''#ifdef REMOTE_PWM_OUT1
#ifdef REMOTE_PWM_OUT2
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "O1=%s O2=%s O3=%s O4=%s O5=%s O6=%s O7=%s | I1=%s I2=%s I3=%s I4=%s | P1=%u%% P2=%u%%", out1,out2,out3,out4,out5,out6,out7,in1,in2,in3,in4,gpio_pwm1_percent,gpio_pwm2_percent);
#else
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "O1=%s O2=%s O3=%s O4=%s O5=%s O6=%s O7=%s | I1=%s I2=%s I3=%s I4=%s | P1=%u%%", out1,out2,out3,out4,out5,out6,out7,in1,in2,in3,in4,gpio_pwm1_percent);
#endif
#else
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "O1=%s O2=%s O3=%s O4=%s O5=%s O6=%s O7=%s | I1=%s I2=%s I3=%s I4=%s", out1,out2,out3,out4,out5,out6,out7,in1,in2,in3,in4);
#endif'''
if old not in s:
    raise SystemExit("V6 STATUS line not found")
s = s.replace(old, new, 1)

# Initialize PWM pins OFF at boot before existing GPIO initialization.
begin_anchor = '#ifdef REMOTE_GPIO_OUT1\n  digitalWrite(REMOTE_GPIO_OUT1, LOW);'
begin_block = '''#ifdef REMOTE_PWM_OUT1
  pinMode(REMOTE_PWM_OUT1, OUTPUT);
  setGpioPwmPercent(REMOTE_PWM_OUT1, 0);
#endif
#ifdef REMOTE_PWM_OUT2
  pinMode(REMOTE_PWM_OUT2, OUTPUT);
  setGpioPwmPercent(REMOTE_PWM_OUT2, 0);
#endif
#ifdef REMOTE_GPIO_OUT1
  digitalWrite(REMOTE_GPIO_OUT1, LOW);'''
if begin_anchor not in s:
    raise SystemExit("begin GPIO anchor not found")
s = s.replace(begin_anchor, begin_block, 1)
p.write_text(s)

# Add PWM pins to both Heltec V3 companion build environments.
p = Path("variants/heltec_v3/platformio.ini")
s = p.read_text()
needle = '  -D REMOTE_GPIO_OUT7=42\n'
flags = '  -D REMOTE_PWM_OUT1=19\n  -D REMOTE_PWM_OUT2=20\n'
count = s.count(needle)
if count < 2:
    raise SystemExit(f"expected V6 OUT7 flag twice, found {count}")
s = s.replace(needle, needle + flags)
p.write_text(s)

print("Heltec V3 GPIO V7: V6 7OUT Link Persistent + PWM1=GPIO19 PWM2=GPIO20")
