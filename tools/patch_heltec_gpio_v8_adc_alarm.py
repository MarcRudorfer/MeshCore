from pathlib import Path

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# V8 ADC alarm configuration/state. Preferences is already included by the persistent LINK patch.
anchor = '#ifdef REMOTE_ADC_IN1\nstatic uint16_t readAdc1Raw() {'
insert = '''#ifdef REMOTE_ADC_IN1
static bool adc1_alarm_enabled = false;
static bool adc1_alarm_active = false;
static uint16_t adc1_low_mv = 1200;
static uint16_t adc1_high_mv = 0;       // 0 = disabled
static uint16_t adc1_hyst_mv = 50;
static uint32_t adc1_repeat_sec = 0;    // 0 = edge notification only
static unsigned long adc1_last_check_ms = 0;
static unsigned long adc1_last_alarm_ms = 0;
static bool adc1_settings_loaded = false;
static Preferences adc1Prefs;

static void saveAdc1Settings() {
  adc1Prefs.begin("meshadc1", false);
  adc1Prefs.putBool("enabled", adc1_alarm_enabled);
  adc1Prefs.putUShort("low", adc1_low_mv);
  adc1Prefs.putUShort("high", adc1_high_mv);
  adc1Prefs.putUShort("hyst", adc1_hyst_mv);
  adc1Prefs.putUInt("repeat", adc1_repeat_sec);
  adc1Prefs.end();
}

static void loadAdc1Settings() {
  adc1Prefs.begin("meshadc1", true);
  adc1_alarm_enabled = adc1Prefs.getBool("enabled", false);
  adc1_low_mv = adc1Prefs.getUShort("low", 1200);
  adc1_high_mv = adc1Prefs.getUShort("high", 0);
  adc1_hyst_mv = adc1Prefs.getUShort("hyst", 50);
  adc1_repeat_sec = adc1Prefs.getUInt("repeat", 0);
  adc1Prefs.end();
  adc1_settings_loaded = true;
}

static uint16_t readAdc1Raw() {'''
if anchor not in s:
    raise SystemExit("ADC read anchor not found")
s = s.replace(anchor, insert, 1)

# Add commands before STATUS.
status_anchor = '  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {\n'
cmds = '''#ifdef REMOTE_ADC_IN1
  if (strcmp(text, "ADC1 ALARM ON") == 0) {
    adc1_alarm_enabled = true; adc1_alarm_active = false; saveAdc1Settings(); gpio_reply = "ADC1 ALARM = ON"; gpio_command_recognized = true;
  } else if (strcmp(text, "ADC1 ALARM OFF") == 0) {
    adc1_alarm_enabled = false; adc1_alarm_active = false; saveAdc1Settings(); gpio_reply = "ADC1 ALARM = OFF"; gpio_command_recognized = true;
  } else if (strcmp(text, "ADC1 STATUS") == 0 || strcmp(text, "ADC1 STATUS?") == 0) {
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "ADC1 %umV | ALARM=%s %s | LOW=%umV HIGH=%umV HYST=%umV REPEAT=%lus", readAdc1Mv(), adc1_alarm_enabled?"ON":"OFF", adc1_alarm_active?"ACTIVE":"OK", adc1_low_mv, adc1_high_mv, adc1_hyst_mv, (unsigned long)adc1_repeat_sec);
    gpio_reply = gpio_reply_buf; gpio_command_recognized = true;
  } else if (strncmp(text, "ADC1 LOW ", 9) == 0) {
    char *e=nullptr; long v=strtol(text+9,&e,10); if(e!=text+9 && *e==0 && v>=0 && v<=3300){adc1_low_mv=(uint16_t)v;saveAdc1Settings();snprintf(gpio_reply_buf,sizeof(gpio_reply_buf),"ADC1 LOW = %ldmV",v);gpio_reply=gpio_reply_buf;}else gpio_reply="ADC1 LOW: USE 0-3300"; gpio_command_recognized=true;
  } else if (strncmp(text, "ADC1 HIGH ", 10) == 0) {
    char *e=nullptr; long v=strtol(text+10,&e,10); if(e!=text+10 && *e==0 && v>=0 && v<=3300){adc1_high_mv=(uint16_t)v;saveAdc1Settings();snprintf(gpio_reply_buf,sizeof(gpio_reply_buf),"ADC1 HIGH = %ldmV",v);gpio_reply=gpio_reply_buf;}else gpio_reply="ADC1 HIGH: USE 0-3300 (0=OFF)"; gpio_command_recognized=true;
  } else if (strncmp(text, "ADC1 HYST ", 10) == 0) {
    char *e=nullptr; long v=strtol(text+10,&e,10); if(e!=text+10 && *e==0 && v>=0 && v<=1000){adc1_hyst_mv=(uint16_t)v;saveAdc1Settings();snprintf(gpio_reply_buf,sizeof(gpio_reply_buf),"ADC1 HYST = %ldmV",v);gpio_reply=gpio_reply_buf;}else gpio_reply="ADC1 HYST: USE 0-1000"; gpio_command_recognized=true;
  } else if (strncmp(text, "ADC1 REPEAT ", 12) == 0) {
    char *e=nullptr; long v=strtol(text+12,&e,10); if(e!=text+12 && *e==0 && (v==0 || (v>=10 && v<=86400))){adc1_repeat_sec=(uint32_t)v;saveAdc1Settings();snprintf(gpio_reply_buf,sizeof(gpio_reply_buf),"ADC1 REPEAT = %lds",v);gpio_reply=gpio_reply_buf;}else gpio_reply="ADC1 REPEAT: 0 OR 10-86400"; gpio_command_recognized=true;
  }
#endif

'''
if status_anchor not in s:
    raise SystemExit("STATUS anchor not found")
s = s.replace(status_anchor, cmds + status_anchor, 1)

# Load persisted settings at startup after ADC pin setup.
begin_anchor = '#ifdef REMOTE_ADC_IN1\n  pinMode(REMOTE_ADC_IN1, INPUT);\n#endif'
begin_new = '''#ifdef REMOTE_ADC_IN1
  pinMode(REMOTE_ADC_IN1, INPUT);
  loadAdc1Settings();
#endif'''
if begin_anchor not in s:
    raise SystemExit("ADC begin anchor not found")
s = s.replace(begin_anchor, begin_new, 1)

# Insert periodic alarm handling before existing GPIO timer processing in loop.
loop_anchor = '#ifdef REMOTE_GPIO_OUT1\n  if (gpio_out1_timer_expiry != 0 && (long)(millis() - gpio_out1_timer_expiry) >= 0) {'
loop_code = '''#ifdef REMOTE_ADC_IN1
  if (adc1_alarm_enabled && millis() - adc1_last_check_ms >= 1000UL) {
    adc1_last_check_ms = millis();
    const uint16_t mv = readAdc1Mv();
    const bool lowTrip = (adc1_low_mv > 0 && mv < adc1_low_mv);
    const bool highTrip = (adc1_high_mv > 0 && mv > adc1_high_mv);
    const bool trip = lowTrip || highTrip;

    if (!adc1_alarm_active && trip) {
      adc1_alarm_active = true;
      adc1_last_alarm_ms = millis();
      char msg[96];
      if (lowTrip) snprintf(msg, sizeof(msg), "ADC1 ALARM LOW: %umV < %umV", mv, adc1_low_mv);
      else snprintf(msg, sizeof(msg), "ADC1 ALARM HIGH: %umV > %umV", mv, adc1_high_mv);
      sendSelfAdvertToMesh(); // keep mesh awake/active before alarm delivery
      sendTextToLastContact(msg);
    } else if (adc1_alarm_active) {
      const bool lowRecovered = (adc1_low_mv == 0 || mv >= (uint16_t)min(3300U, (unsigned int)adc1_low_mv + adc1_hyst_mv));
      const bool highRecovered = (adc1_high_mv == 0 || mv <= (adc1_high_mv > adc1_hyst_mv ? adc1_high_mv - adc1_hyst_mv : 0));
      if (lowRecovered && highRecovered) {
        adc1_alarm_active = false;
        char msg[64]; snprintf(msg, sizeof(msg), "ADC1 OK: %umV", mv); sendTextToLastContact(msg);
      } else if (adc1_repeat_sec > 0 && millis() - adc1_last_alarm_ms >= adc1_repeat_sec * 1000UL) {
        adc1_last_alarm_ms = millis();
        char msg[96]; snprintf(msg, sizeof(msg), "ADC1 ALARM STILL ACTIVE: %umV", mv); sendTextToLastContact(msg);
      }
    }
  }
#endif

#ifdef REMOTE_GPIO_OUT1
  if (gpio_out1_timer_expiry != 0 && (long)(millis() - gpio_out1_timer_expiry) >= 0) {'''
if loop_anchor not in s:
    raise SystemExit("loop timer anchor not found")
s = s.replace(loop_anchor, loop_code, 1)

p.write_text(s)
print("Added V8 persistent ADC1 alarm settings and monitoring")
