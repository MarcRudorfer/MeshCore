from pathlib import Path

# Heltec V3 GPIO V8
# Base: V7 final. Keep PWM1=GPIO19, replace PWM2=GPIO20 with ADC1=GPIO20.

# 1) Remove PWM2 define from Heltec V3 companion environments and add ADC1 on GPIO20.
p = Path("variants/heltec_v3/platformio.ini")
s = p.read_text()
old = '  -D REMOTE_PWM_OUT2=20\n'
new = '  -D REMOTE_ADC_IN1=20\n'
count = s.count(old)
if count < 2:
    raise SystemExit(f"expected PWM2 GPIO20 flag twice, found {count}")
s = s.replace(old, new)
p.write_text(s)

# 2) Add ADC command + STATUS reporting to MyMesh.cpp.
p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# Helper: average 16 calibrated millivolt samples for a steadier reading.
anchor = 'static void setGpioPwmPercent(uint8_t pin, uint8_t percent) {\n'
helper = '''#ifdef REMOTE_ADC_IN1
static uint32_t readGpioAdcMilliVolts(uint8_t pin) {
  uint32_t sum = 0;
  for (int i = 0; i < 16; ++i) {
    sum += analogReadMilliVolts(pin);
  }
  return (sum + 8U) / 16U;
}
#endif

static void setGpioPwmPercent(uint8_t pin, uint8_t percent) {
'''
if anchor not in s:
    raise SystemExit("PWM helper anchor not found")
s = s.replace(anchor, helper, 1)

status_anchor = '  if (strcmp(text, "STATUS") == 0 || strcmp(text, "STATUS?") == 0 || strcmp(text, "STATUS ?") == 0) {\n'
adc_commands = '''#ifdef REMOTE_ADC_IN1
  if (strcmp(text, "ADC1") == 0 || strcmp(text, "ADC1?") == 0) {
    uint32_t mv = readGpioAdcMilliVolts(REMOTE_ADC_IN1);
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "ADC1 = %lumV", (unsigned long)mv);
    gpio_reply = gpio_reply_buf;
    gpio_command_recognized = true;
  } else if (strcmp(text, "ADC1 RAW") == 0 || strcmp(text, "ADC1 RAW?") == 0) {
    uint32_t raw_sum = 0;
    for (int i = 0; i < 16; ++i) raw_sum += analogRead(REMOTE_ADC_IN1);
    uint32_t raw = (raw_sum + 8U) / 16U;
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "ADC1 RAW = %lu", (unsigned long)raw);
    gpio_reply = gpio_reply_buf;
    gpio_command_recognized = true;
  }
#endif

'''
if status_anchor not in s:
    raise SystemExit("STATUS anchor not found")
s = s.replace(status_anchor, adc_commands + status_anchor, 1)

# V7 STATUS has two PWM branches. In V8 REMOTE_PWM_OUT2 is no longer defined, so replace the PWM1-only line with PWM1 + ADC1.
old_status = '    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "O1=%s O2=%s O3=%s O4=%s O5=%s O6=%s O7=%s | I1=%s I2=%s I3=%s I4=%s | P1=%u%%", out1,out2,out3,out4,out5,out6,out7,in1,in2,in3,in4,gpio_pwm1_percent);'
new_status = '''#ifdef REMOTE_ADC_IN1
    uint32_t adc1_mv = readGpioAdcMilliVolts(REMOTE_ADC_IN1);
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "O1=%s O2=%s O3=%s O4=%s O5=%s O6=%s O7=%s | I1=%s I2=%s I3=%s I4=%s | P1=%u%% | A1=%lumV", out1,out2,out3,out4,out5,out6,out7,in1,in2,in3,in4,gpio_pwm1_percent,(unsigned long)adc1_mv);
#else
    snprintf(gpio_reply_buf, sizeof(gpio_reply_buf), "O1=%s O2=%s O3=%s O4=%s O5=%s O6=%s O7=%s | I1=%s I2=%s I3=%s I4=%s | P1=%u%%", out1,out2,out3,out4,out5,out6,out7,in1,in2,in3,in4,gpio_pwm1_percent);
#endif'''
if old_status not in s:
    raise SystemExit("V7 PWM1-only STATUS line not found")
s = s.replace(old_status, new_status, 1)

# Initialize ADC pin explicitly as input.
begin_anchor = '#ifdef REMOTE_PWM_OUT1\n  pinMode(REMOTE_PWM_OUT1, OUTPUT);'
begin_block = '''#ifdef REMOTE_ADC_IN1
  pinMode(REMOTE_ADC_IN1, INPUT);
#endif
#ifdef REMOTE_PWM_OUT1
  pinMode(REMOTE_PWM_OUT1, OUTPUT);'''
if begin_anchor not in s:
    raise SystemExit("begin PWM1 anchor not found")
s = s.replace(begin_anchor, begin_block, 1)

p.write_text(s)
print("Heltec V3 GPIO V8: V7 final with PWM1=GPIO19 and ADC1=GPIO20 (PWM2 removed)")
