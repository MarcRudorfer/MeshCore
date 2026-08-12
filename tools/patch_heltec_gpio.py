from pathlib import Path

# Patch Companion message handling and safe boot state.
p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

old = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,
                           const char *text) {
  markConnectionActive(from); // in case this is from a server, and we have a connection
  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);
}'''
new = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,
                           const char *text) {
  markConnectionActive(from); // in case this is from a server, and we have a connection

  const char* gpio_reply = nullptr;
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

  if (gpio_reply) {
    uint32_t expected_ack = 0;
    uint32_t est_timeout = 0;
    sendMessage(from, getRTCClock()->getCurrentTimeUnique(), 0,
                gpio_reply, expected_ack, est_timeout);
  }

  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);
}'''
if old not in s:
    raise SystemExit("onMessageRecv anchor not found")
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
    raise SystemExit("begin anchor not found")
s = s.replace(old, new, 1)
p.write_text(s)

# Enable GPIO4/GPIO5 only for Heltec V3 companion BLE/USB builds.
p = Path("variants/heltec_v3/platformio.ini")
s = p.read_text()
for env in ("Heltec_v3_companion_radio_usb", "Heltec_v3_companion_radio_ble"):
    anchor = f"[env:{env}]\nextends = Heltec_lora32_v3\nbuild_flags =\n  ${{Heltec_lora32_v3.build_flags}}\n"
    replacement = anchor + "  -D REMOTE_GPIO_OUT1=4\n  -D REMOTE_GPIO_OUT2=5\n"
    if anchor not in s:
        raise SystemExit(f"{env} anchor not found")
    s = s.replace(anchor, replacement, 1)
p.write_text(s)

print("Heltec V3 GPIO patch applied: OUT1=GPIO4, OUT2=GPIO5")
