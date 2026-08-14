from pathlib import Path

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# ESP32 NVS helper for persistent link peer storage.
inc_anchor = '#include <Arduino.h> // needed for PlatformIO\n'
if inc_anchor not in s:
    raise SystemExit('Arduino include anchor not found')
s = s.replace(inc_anchor, inc_anchor + '#include <Preferences.h>\n', 1)

anchor = 'static bool gpio_link_peer_valid = false;\n'
helpers = anchor + r'''
static bool gpio_link_peer_load_attempted = false;

static void gpio_link_save_peer() {
  Preferences prefs;
  if (prefs.begin("meshgpio", false)) {
    prefs.putBytes("linkpeer", &gpio_link_peer, sizeof(gpio_link_peer));
    prefs.putBool("linkvalid", true);
    prefs.end();
  }
}

static void gpio_link_load_peer() {
  if (gpio_link_peer_load_attempted) return;
  gpio_link_peer_load_attempted = true;
  Preferences prefs;
  if (!prefs.begin("meshgpio", true)) return;
  bool valid = prefs.getBool("linkvalid", false);
  size_t n = prefs.getBytesLength("linkpeer");
  if (valid && n == sizeof(gpio_link_peer)) {
    if (prefs.getBytes("linkpeer", &gpio_link_peer, sizeof(gpio_link_peer)) == sizeof(gpio_link_peer)) {
      gpio_link_peer_valid = true;
    }
  }
  prefs.end();
}
'''
if anchor not in s:
    raise SystemExit('link peer globals anchor not found')
s = s.replace(anchor, helpers, 1)

# Ensure saved peer is loaded before STATUS / sender validation.
anchor = '  bool gpio_link_sender_ok = gpio_link_peer_valid &&\n'
if anchor not in s:
    raise SystemExit('link sender anchor not found')
s = s.replace(anchor, '  gpio_link_load_peer();\n\n' + anchor, 1)

# Save the paired contact immediately when LINK PAIR succeeds.
anchor = '''    gpio_link_peer = from;\n    gpio_link_peer_valid = true;\n    gpio_link_sender_ok = true;\n'''
replacement = '''    gpio_link_peer = from;\n    gpio_link_peer_valid = true;\n    gpio_link_peer_load_attempted = true;\n    gpio_link_save_peer();\n    gpio_link_sender_ok = true;\n'''
if anchor not in s:
    raise SystemExit('LINK PAIR save anchor not found')
s = s.replace(anchor, replacement, 1)

# Load once before autonomous input mirroring too, so link works after reboot
# even if no LINK STATUS command was sent first.
anchor = '#ifdef REMOTE_GPIO_IN1\n  if (gpio_in1_stable != gpio_link_in1_last) {'
if anchor not in s:
    raise SystemExit('IN1 loop anchor not found')
s = s.replace(anchor, '  gpio_link_load_peer();\n\n' + anchor, 1)

p.write_text(s)
print('Applied persistent LINK peer storage using ESP32 Preferences/NVS')
