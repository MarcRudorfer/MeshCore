from pathlib import Path

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# Add OUT5..OUT10 timer globals after OUT4 globals from the V4/V5 base.
anchor = '''#ifdef REMOTE_GPIO_OUT4
static unsigned long gpio_out4_timer_expiry = 0;
static ContactInfo gpio_out4_timer_contact;
static bool gpio_out4_timer_contact_valid = false;
#endif
'''
extra = anchor
for n in range(5, 11):
    extra += f'''#ifdef REMOTE_GPIO_OUT{n}\nstatic unsigned long gpio_out{n}_timer_expiry = 0;\nstatic ContactInfo gpio_out{n}_timer_contact;\nstatic bool gpio_out{n}_timer_contact_valid = false;\n#endif\n'''
if anchor not in s:
    raise SystemExit("OUT4 globals anchor not found")
s = s.replace(anchor, extra, 1)

# Add manual ON/OFF/TIMER commands for OUT5..OUT10 before STATUS.
status_anchor = '  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {\n'
commands = ''
for n in range(5, 11):
    commands += f'''#ifdef REMOTE_GPIO_OUT{n}\n  if (strcmp(text, "OUT{n} ON") == 0) {{\n    gpio_out{n}_timer_expiry = 0; gpio_out{n}_timer_contact_valid = false;\n    digitalWrite(REMOTE_GPIO_OUT{n}, HIGH); gpio_reply = "OUT{n} = ON"; gpio_command_recognized = true;\n  }} else if (strcmp(text, "OUT{n} OFF") == 0) {{\n    gpio_out{n}_timer_expiry = 0; gpio_out{n}_timer_contact_valid = false;\n    digitalWrite(REMOTE_GPIO_OUT{n}, LOW); gpio_reply = "OUT{n} = OFF"; gpio_command_recognized = true;\n  }} else if (strncmp(text, "OUT{n} TIMER", {10 if n < 10 else 11}) == 0 && (text[{10 if n < 10 else 11}] == 0 || text[{10 if n < 10 else 11}] == ' ')) {{\n    unsigned long seconds = 5; bool valid = true;\n    if (text[{10 if n < 10 else 11}] == ' ') {{ char *endptr = nullptr; seconds = strtoul(text + {11 if n < 10 else 12}, &endptr, 10); valid = (endptr != text + {11 if n < 10 else 12} && *endptr == 0 && seconds >= 1 && seconds <= 3600); }}\n    gpio_command_recognized = true;\n    if (valid) {{ digitalWrite(REMOTE_GPIO_OUT{n}, HIGH); gpio_out{n}_timer_expiry = futureMillis(seconds * 1000UL); gpio_out{n}_timer_contact = from; gpio_out{n}_timer_contact_valid = true; snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT{n} = ON (TIMER %luS)", seconds); gpio_reply = gpio_reply_buf; }}\n    else gpio_reply = "OUT{n} TIMER: USE 1-3600S";\n  }}\n#endif\n'''
if status_anchor not in s:
    raise SystemExit("STATUS anchor not found")
s = s.replace(status_anchor, commands + '\n' + status_anchor, 1)

# Expand STATUS to include OUT5..OUT10 while preserving IN1..IN4.
old_status = '''    const char* out1 = "NA"; const char* out2 = "NA"; const char* out3 = "NA"; const char* out4 = "NA";
    const char* in1 = "NA"; const char* in2 = "NA"; const char* in3 = "NA"; const char* in4 = "NA";
'''
new_status = '''    const char* out1 = "NA"; const char* out2 = "NA"; const char* out3 = "NA"; const char* out4 = "NA";
    const char* out5 = "NA"; const char* out6 = "NA"; const char* out7 = "NA"; const char* out8 = "NA"; const char* out9 = "NA"; const char* out10 = "NA";
    const char* in1 = "NA"; const char* in2 = "NA"; const char* in3 = "NA"; const char* in4 = "NA";
'''
if old_status not in s:
    raise SystemExit("STATUS declarations anchor not found")
s = s.replace(old_status, new_status, 1)

anchor = '''#ifdef REMOTE_GPIO_OUT4
    out4 = digitalRead(REMOTE_GPIO_OUT4) == HIGH ? "ON" : "OFF";
#endif
'''
extra = anchor
for n in range(5, 11):
    extra += f'''#ifdef REMOTE_GPIO_OUT{n}\n    out{n} = digitalRead(REMOTE_GPIO_OUT{n}) == HIGH ? "ON" : "OFF";\n#endif\n'''
if anchor not in s:
    raise SystemExit("STATUS OUT4 anchor not found")
s = s.replace(anchor, extra, 1)

old_fmt = '    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "OUT1=%s | OUT2=%s | OUT3=%s | OUT4=%s | IN1=%s | IN2=%s | IN3=%s | IN4=%s", out1,out2,out3,out4,in1,in2,in3,in4);'
new_fmt = '    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "O1=%s O2=%s O3=%s O4=%s O5=%s O6=%s O7=%s O8=%s O9=%s O10=%s | I1=%s I2=%s I3=%s I4=%s", out1,out2,out3,out4,out5,out6,out7,out8,out9,out10,in1,in2,in3,in4);'
if old_fmt not in s:
    raise SystemExit("STATUS format anchor not found")
s = s.replace(old_fmt, new_fmt, 1)
s = s.replace('  char gpio_reply_buf[192];', '  char gpio_reply_buf[256];', 1)

# Initialize OUT5..OUT10 LOW at boot.
begin_anchor = '''#ifdef REMOTE_GPIO_IN1
  pinMode(REMOTE_GPIO_IN1, INPUT_PULLUP);'''
begin_extra = ''
for n in range(5, 11):
    begin_extra += f'''#ifdef REMOTE_GPIO_OUT{n}\n  digitalWrite(REMOTE_GPIO_OUT{n}, LOW); pinMode(REMOTE_GPIO_OUT{n}, OUTPUT); gpio_out{n}_timer_expiry = 0; gpio_out{n}_timer_contact_valid = false;\n#endif\n'''
if begin_anchor not in s:
    raise SystemExit("begin input anchor not found")
s = s.replace(begin_anchor, begin_extra + begin_anchor, 1)

# Timer expiry handling for OUT5..OUT10.
loop_anchor = '#ifdef REMOTE_GPIO_IN1\n  {\n    int raw = digitalRead(REMOTE_GPIO_IN1);'
loop_extra = ''
for n in range(5, 11):
    loop_extra += f'''#ifdef REMOTE_GPIO_OUT{n}\n  if (gpio_out{n}_timer_expiry && millisHasNowPassed(gpio_out{n}_timer_expiry)) {{ digitalWrite(REMOTE_GPIO_OUT{n}, LOW); gpio_out{n}_timer_expiry = 0; if (gpio_out{n}_timer_contact_valid) {{ uint32_t expected_ack=0, est_timeout=0; sendMessage(gpio_out{n}_timer_contact,getRTCClock()->getCurrentTimeUnique(),0,"OUT{n} = OFF (TIMER DONE)",expected_ack,est_timeout); gpio_out{n}_timer_contact_valid=false; }} }}\n#endif\n'''
if loop_anchor not in s:
    raise SystemExit("loop input anchor not found")
s = s.replace(loop_anchor, loop_extra + '\n' + loop_anchor, 1)

p.write_text(s)

# Heltec V3 additional outputs only. Existing OUT1..OUT4 + IN1..IN4 stay unchanged.
p = Path("variants/heltec_v3/platformio.ini")
s = p.read_text()
needle = '  -D REMOTE_GPIO_IN4=34\n'
flags = (
    '  -D REMOTE_GPIO_OUT5=1\n'
    '  -D REMOTE_GPIO_OUT6=2\n'
    '  -D REMOTE_GPIO_OUT7=39\n'
    '  -D REMOTE_GPIO_OUT8=40\n'
    '  -D REMOTE_GPIO_OUT9=41\n'
    '  -D REMOTE_GPIO_OUT10=42\n'
)
count = s.count(needle)
if count < 2:
    raise SystemExit(f"expected Heltec V3 GPIO flags twice, found {count}")
s = s.replace(needle, needle + flags)
p.write_text(s)

print("Heltec V3 GPIO V6: V5 Link Persistent + OUT5=1 OUT6=2 OUT7=39 OUT8=40 OUT9=41 OUT10=42")
