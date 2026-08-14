from pathlib import Path

p = Path("examples/companion_radio/MyMesh.cpp")
s = p.read_text()

anchor = "  bool gpio_command_recognized = false;\n\n"
block = '''  bool gpio_command_recognized = false;\n\n  if (strcmp(text, "LINK STATUS") == 0 || strcmp(text, "LINK STATUS?") == 0) {\n    gpio_reply = "LINK = UNPAIRED";\n    gpio_command_recognized = true;\n  }\n\n'''

if anchor not in s:
    raise SystemExit("LINK STATUS anchor not found")
s = s.replace(anchor, block, 1)
p.write_text(s)

print("Applied LINK STATUS-only diagnostic patch")
