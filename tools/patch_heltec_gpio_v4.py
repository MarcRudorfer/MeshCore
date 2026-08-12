from pathlib import Path

# First apply the already hardware-tested V3 patch.
exec(Path("tools/patch_heltec_gpio.py").read_text(), {"__name__": "__main__"})

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# Add OUT3/OUT4 timer state after OUT2.
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
#ifdef REMOTE_GPIO_OUT4
static unsigned long gpio_out4_timer_expiry = 0;
static ContactInfo gpio_out4_timer_contact;
static bool gpio_out4_timer_contact_valid = false;
#endif
'''
if anchor not in s: raise SystemExit("OUT2 globals anchor not found")
s = s.replace(anchor, extra, 1)

# Add IN3/IN4 state after IN2.
anchor = '''#ifdef REMOTE_GPIO_IN2
static int gpio_in2_stable = HIGH;
static int gpio_in2_raw = HIGH;
static unsigned long gpio_in2_debounce_expiry = 0;
#endif
'''
extra = anchor + '''#ifdef REMOTE_GPIO_IN3
static int gpio_in3_stable = HIGH;
static int gpio_in3_raw = HIGH;
static unsigned long gpio_in3_debounce_expiry = 0;
#endif
#ifdef REMOTE_GPIO_IN4
static int gpio_in4_stable = HIGH;
static int gpio_in4_raw = HIGH;
static unsigned long gpio_in4_debounce_expiry = 0;
#endif
'''
if anchor not in s: raise SystemExit("IN2 globals anchor not found")
s = s.replace(anchor, extra, 1)

status_anchor = '  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {\n'
commands = r'''
#ifdef REMOTE_GPIO_OUT3
  if (strcmp(text, "OUT3 ON") == 0) {
    gpio_out3_timer_expiry = 0; gpio_out3_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT3, HIGH); gpio_reply = "OUT3 = ON"; gpio_command_recognized = true;
  } else if (strcmp(text, "OUT3 OFF") == 0) {
    gpio_out3_timer_expiry = 0; gpio_out3_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT3, LOW); gpio_reply = "OUT3 = OFF"; gpio_command_recognized = true;
  } else if (strncmp(text, "OUT3 TIMER", 10) == 0 && (text[10] == 0 || text[10] == ' ')) {
    unsigned long seconds = 5; bool valid = true;
    if (text[10] == ' ') { char *endptr = nullptr; seconds = strtoul(text + 11, &endptr, 10); valid = (endptr != text + 11 && *endptr == 0 && seconds >= 1 && seconds <= 3600); }
    gpio_command_recognized = true;
    if (valid) { digitalWrite(REMOTE_GPIO_OUT3, HIGH); gpio_out3_timer_expiry = futureMillis(seconds * 1000UL); gpio_out3_timer_contact = from; gpio_out3_timer_contact_valid = true; snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT3 = ON (TIMER %luS)", seconds); gpio_reply = gpio_reply_buf; }
    else gpio_reply = "OUT3 TIMER: USE 1-3600S";
  }
#endif
#ifdef REMOTE_GPIO_OUT4
  if (strcmp(text, "OUT4 ON") == 0) {
    gpio_out4_timer_expiry = 0; gpio_out4_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT4, HIGH); gpio_reply = "OUT4 = ON"; gpio_command_recognized = true;
  } else if (strcmp(text, "OUT4 OFF") == 0) {
    gpio_out4_timer_expiry = 0; gpio_out4_timer_contact_valid = false;
    digitalWrite(REMOTE_GPIO_OUT4, LOW); gpio_reply = "OUT4 = OFF"; gpio_command_recognized = true;
  } else if (strncmp(text, "OUT4 TIMER", 10) == 0 && (text[10] == 0 || text[10] == ' ')) {
    unsigned long seconds = 5; bool valid = true;
    if (text[10] == ' ') { char *endptr = nullptr; seconds = strtoul(text + 11, &endptr, 10); valid = (endptr != text + 11 && *endptr == 0 && seconds >= 1 && seconds <= 3600); }
    gpio_command_recognized = true;
    if (valid) { digitalWrite(REMOTE_GPIO_OUT4, HIGH); gpio_out4_timer_expiry = futureMillis(seconds * 1000UL); gpio_out4_timer_contact = from; gpio_out4_timer_contact_valid = true; snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT4 = ON (TIMER %luS)", seconds); gpio_reply = gpio_reply_buf; }
    else gpio_reply = "OUT4 TIMER: USE 1-3600S";
  }
#endif

'''
if status_anchor not in s: raise SystemExit("STATUS anchor not found")
s = s.replace(status_anchor, commands + status_anchor, 1)
s = s.replace('  char gpio_reply_buf[96];', '  char gpio_reply_buf[192];', 1)
old = '''    const char* out1 = "NA";
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
             "OUT1=%s | OUT2=%s | IN1=%s | IN2=%s", out1, out2, in1, in2);'''
new = '''    const char* out1 = "NA"; const char* out2 = "NA"; const char* out3 = "NA"; const char* out4 = "NA";
    const char* in1 = "NA"; const char* in2 = "NA"; const char* in3 = "NA"; const char* in4 = "NA";
#ifdef REMOTE_GPIO_OUT1
    out1 = digitalRead(REMOTE_GPIO_OUT1) == HIGH ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_OUT2
    out2 = digitalRead(REMOTE_GPIO_OUT2) == HIGH ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_OUT3
    out3 = digitalRead(REMOTE_GPIO_OUT3) == HIGH ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_OUT4
    out4 = digitalRead(REMOTE_GPIO_OUT4) == HIGH ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_IN1
    in1 = gpio_in1_stable == LOW ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_IN2
    in2 = gpio_in2_stable == LOW ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_IN3
    in3 = gpio_in3_stable == LOW ? "ON" : "OFF";
#endif
#ifdef REMOTE_GPIO_IN4
    in4 = gpio_in4_stable == LOW ? "ON" : "OFF";
#endif
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT1=%s | OUT2=%s | OUT3=%s | OUT4=%s | IN1=%s | IN2=%s | IN3=%s | IN4=%s", out1,out2,out3,out4,in1,in2,in3,in4);'''
if old not in s: raise SystemExit("STATUS block anchor not found")
s = s.replace(old, new, 1)
anchor = '''#ifdef REMOTE_GPIO_IN1
  pinMode(REMOTE_GPIO_IN1, INPUT_PULLUP);'''
extra = '''#ifdef REMOTE_GPIO_OUT3
  digitalWrite(REMOTE_GPIO_OUT3, LOW); pinMode(REMOTE_GPIO_OUT3, OUTPUT); gpio_out3_timer_expiry = 0; gpio_out3_timer_contact_valid = false;
#endif
#ifdef REMOTE_GPIO_OUT4
  digitalWrite(REMOTE_GPIO_OUT4, LOW); pinMode(REMOTE_GPIO_OUT4, OUTPUT); gpio_out4_timer_expiry = 0; gpio_out4_timer_contact_valid = false;
#endif
''' + anchor
if anchor not in s: raise SystemExit("begin OUT extension anchor not found")
s = s.replace(anchor, extra, 1)
anchor = '  gpio_notify_contact_valid = false;\n  BaseChatMesh::begin();'
extra = '''#ifdef REMOTE_GPIO_IN3
  pinMode(REMOTE_GPIO_IN3, INPUT_PULLUP); gpio_in3_stable = digitalRead(REMOTE_GPIO_IN3); gpio_in3_raw = gpio_in3_stable; gpio_in3_debounce_expiry = 0;
#endif
#ifdef REMOTE_GPIO_IN4
  pinMode(REMOTE_GPIO_IN4, INPUT_PULLUP); gpio_in4_stable = digitalRead(REMOTE_GPIO_IN4); gpio_in4_raw = gpio_in4_stable; gpio_in4_debounce_expiry = 0;
#endif
''' + anchor
if anchor not in s: raise SystemExit("begin IN extension anchor not found")
s = s.replace(anchor, extra, 1)
anchor = '#ifdef REMOTE_GPIO_IN1\n  {\n    int raw = digitalRead(REMOTE_GPIO_IN1);'
extra = r'''#ifdef REMOTE_GPIO_OUT3
  if (gpio_out3_timer_expiry && millisHasNowPassed(gpio_out3_timer_expiry)) { digitalWrite(REMOTE_GPIO_OUT3, LOW); gpio_out3_timer_expiry = 0; if (gpio_out3_timer_contact_valid) { uint32_t expected_ack=0, est_timeout=0; sendMessage(gpio_out3_timer_contact,getRTCClock()->getCurrentTimeUnique(),0,"OUT3 = OFF (TIMER DONE)",expected_ack,est_timeout); gpio_out3_timer_contact_valid=false; } }
#endif
#ifdef REMOTE_GPIO_OUT4
  if (gpio_out4_timer_expiry && millisHasNowPassed(gpio_out4_timer_expiry)) { digitalWrite(REMOTE_GPIO_OUT4, LOW); gpio_out4_timer_expiry = 0; if (gpio_out4_timer_contact_valid) { uint32_t expected_ack=0, est_timeout=0; sendMessage(gpio_out4_timer_contact,getRTCClock()->getCurrentTimeUnique(),0,"OUT4 = OFF (TIMER DONE)",expected_ack,est_timeout); gpio_out4_timer_contact_valid=false; } }
#endif

''' + anchor
if anchor not in s: raise SystemExit("loop OUT extension anchor not found")
s = s.replace(anchor, extra, 1)
anchor = '  if (_cli_rescue) {\n'
inputs = r'''#ifdef REMOTE_GPIO_IN3
  { int raw=digitalRead(REMOTE_GPIO_IN3); if(raw!=gpio_in3_raw){gpio_in3_raw=raw;gpio_in3_debounce_expiry=futureMillis(50);} if(gpio_in3_debounce_expiry&&millisHasNowPassed(gpio_in3_debounce_expiry)){gpio_in3_debounce_expiry=0;if(gpio_in3_stable!=gpio_in3_raw){gpio_in3_stable=gpio_in3_raw;if(gpio_notify_contact_valid){uint32_t expected_ack=0,est_timeout=0;sendMessage(gpio_notify_contact,getRTCClock()->getCurrentTimeUnique(),0,gpio_in3_stable==LOW?"IN3 = ON":"IN3 = OFF",expected_ack,est_timeout);}}} }
#endif
#ifdef REMOTE_GPIO_IN4
  { int raw=digitalRead(REMOTE_GPIO_IN4); if(raw!=gpio_in4_raw){gpio_in4_raw=raw;gpio_in4_debounce_expiry=futureMillis(50);} if(gpio_in4_debounce_expiry&&millisHasNowPassed(gpio_in4_debounce_expiry)){gpio_in4_debounce_expiry=0;if(gpio_in4_stable!=gpio_in4_raw){gpio_in4_stable=gpio_in4_raw;if(gpio_notify_contact_valid){uint32_t expected_ack=0,est_timeout=0;sendMessage(gpio_notify_contact,getRTCClock()->getCurrentTimeUnique(),0,gpio_in4_stable==LOW?"IN4 = ON":"IN4 = OFF",expected_ack,est_timeout);}}} }
#endif

''' + anchor
if anchor not in s: raise SystemExit("loop IN extension anchor not found")
s = s.replace(anchor, inputs, 1)
p.write_text(s)

p = Path("variants/heltec_v3/platformio.ini")
s = p.read_text()
needle = '  -D REMOTE_GPIO_IN2=7\n'
replacement = needle + '  -D REMOTE_GPIO_OUT3=47\n  -D REMOTE_GPIO_OUT4=48\n  -D REMOTE_GPIO_IN3=33\n  -D REMOTE_GPIO_IN4=34\n'
count = s.count(needle)
if count < 2: raise SystemExit(f"expected V3 flags twice, found {count}")
s = s.replace(needle, replacement)
p.write_text(s)

print("Heltec V3 GPIO V4 corrected: OUT3=47 OUT4=48 IN3=33 IN4=34")
