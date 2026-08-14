from pathlib import Path

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

# Pairing state only. Intentionally RAM-only for this diagnostic step.
anchor = "static bool gpio_notify_contact_valid = false;\n"
extra = anchor + "\nstatic ContactInfo gpio_link_peer;\nstatic bool gpio_link_peer_valid = false;\n"
if anchor not in s:
    raise SystemExit("LINK PAIR globals anchor not found")
s = s.replace(anchor, extra, 1)

anchor = "  bool gpio_command_recognized = false;\n\n"
block = r'''  bool gpio_command_recognized = false;

  if (strcmp(text, "LINK PAIR") == 0) {
    gpio_link_peer = from;
    gpio_link_peer_valid = true;
    gpio_reply = "LINK PAIRED";
    gpio_command_recognized = true;
  }

  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {
    gpio_reply = gpio_link_peer_valid ? "LINK = PAIRED" : "LINK = UNPAIRED";
    gpio_command_recognized = true;
  }

'''
if anchor not in s:
    raise SystemExit("LINK PAIR command anchor not found")
s = s.replace(anchor, block, 1)

p.write_text(s)
print("Applied isolated LINK PAIR + STATUS diagnostic patch")
