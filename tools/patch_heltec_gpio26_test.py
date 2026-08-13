from pathlib import Path

# Apply the already hardware-tested V3 patch first.
exec(Path("tools/patch_heltec_gpio.py").read_text(), {"__name__": "__main__"})

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

anchor = '''#ifdef REMOTE_GPIO_OUT2
static unsigned long gpio_out2_timer_expiry = 0;
static ContactInfo gpio_out2_timer_contact;
static bool gpio_out2_timer_contact_valid = false;
#endif
'''
extra = anchor + '''#ifdef REMOTE_GPIO_OUT3
static unsigned long gpio_out3_timer_expiry = 0;
static ContactInfo gpio_out3_timer_contact;
static bool gpio_out3_timer_contact_valid = false;
#endif
'''
if anchor not in s: raise SystemExit("OUT2 globals anchor not found")
s = s.replace(anchor, extra, 1)

status_anchor = '  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {\n'
commands = r'''#ifdef REMOTE_GPIO_OUT3
  if (strcmp(text, "OUT3 ON") == 0) {
    gpio_out3_timer_expiry = 0;
    gpio_out3_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT3, HIGH);
    gpio_reply = "OUT3 = ON";
    gpio_command_recognized = true;
  } else if (strcmp(text, "OUT3 OFF") == 0) {
    gpio_out3_timer_expiry = 0;
    gpio_out3_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT3, LOW);
    gpio_reply = "OUT3 = OFF";
    gpio_command_recognized = true;
  } else if (strncmp(text, "OUT3 TIMER", 10) == 0 && (text[10] == 0 || text[10] == ' ')) {
    unsigned long seconds = 5;
    bool valid = true;
    if (text[10] == ' ') {
      char *endptr = nullptr;
      seconds = strtoul(text + 11, &endptr, 10);
      valid = (endptr != text + 11 && *endptr == 0 && seconds >= 1 && seconds <= 3600);
    }
    gpio_command_recognized = true;
    if (valid) {
      digitalWrite(REMOTE_GPIO_OUT3, HIGH);
      gpio_out3_timer_expiry = futureMillis(seconds * 1000UL);
      gpio_out3_timer_contact = from;
      gpio_out3_timer_contact_valid = true;
      snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT3 = ON (TIMER %luS)", seconds);
      gpio_reply = gpio_reply_buf;
    } else {
      gpio_reply = "OUT3 TIMER: USE 1-3600S";
    }
  }
#endif

'''
if status_anchor not in s: raise SystemExit("STATUS anchor not found")
s = s.replace(status_anchor, commands + status_anchor, 1)

# Initialize GPIO26 safely LOW on boot.
anchor = '''#ifdef REMOTE_GPIO_IN1
  pinMode(REMOTE_GPIO_IN1, INPUT_PULLUP);'''
extra = '''#ifdef REMOTE_GPIO_OUT3
  digitalWrite(REMOTE_GPIO_OUT3, LOW);
  pinMode(REMOTE_GPIO_OUT3, OUTPUT);
  gpio_out3_timer_expiry = 0;
  gpio_out3_timer_contact_valid = false;
#endif
''' + anchor
if anchor not in s: raise SystemExit("begin anchor not found")
s = s.replace(anchor, extra, 1)

# Timer completion logic.
anchor = '#ifdef REMOTE_GPIO_IN1\n  {\n    int raw = digitalRead(REMOTE_GPIO_IN1);'
extra = r'''#ifdef REMOTE_GPIO_OUT3
  if (gpio_out3_timer_expiry && millisHasNowPassed(gpio_out3_timer_expiry)) {
    digitalWrite(REMOTE_GPIO_OUT3, LOW);
    gpio_out3_timer_expiry = 0;
    if (gpio_out3_timer_contact_valid) {
      uint32_t expected_ack = 0;
      uint32_t est_timeout = 0;
      sendMessage(gpio_out3_timer_contact, getRTCClock()->getCurrentTimeUnique(), 0,
                  "OUT3 = OFF (TIMER DONE)", expected_ack, est_timeout);
      gpio_out3_timer_contact_valid = false;
    }
  }
#endif

''' + anchor
if anchor not in s: raise SystemExit("loop anchor not found")
s = s.replace(anchor, extra, 1)
p.write_text(s)

# Enable only one additional test output: GPIO26.
p = Path("variants/heltec_v3/platformio.ini")
s = p.read_text()
needle = '  -D REMOTE_GPIO_IN2=7\n'
replacement = needle + '  -D REMOTE_GPIO_OUT3=26\n'
count = s.count(needle)
if count < 2: raise SystemExit(f"expected V3 flags twice, found {count}")
s = s.replace(needle, replacement)
p.write_text(s)

print("Heltec V3 isolated GPIO26 test: OUT3=GPIO26; V3 OUT1/OUT2 + IN1/IN2 retained")
