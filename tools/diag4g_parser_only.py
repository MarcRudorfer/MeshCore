from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

old = '''    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {
      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);
      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";
      gpio_command_recognized = true;
    }
'''

new = '''    } else if (strcmp(text, "LINK OUT4 OFF") == 0) {
      pinMode((uint8_t)gpio_link_out4_runtime_pin, OUTPUT);
      digitalWrite((uint8_t)gpio_link_out4_runtime_pin, LOW);
      gpio_reply = "LINK ACK OUT4 OFF ISOLATED GPIO45";
      gpio_command_recognized = true;
    } else if (strncmp(text, "LINK OUT4 TIMER", 15) == 0 && (text[15] == 0 || text[15] == ' ')) {
      gpio_reply = "LINK ACK OUT4 TIMER PARSER";
      gpio_command_recognized = true;
    }
'''

if old not in s:
    raise SystemExit('OUT4 OFF parser anchor not found')
s = s.replace(old, new, 1)
p.write_text(s)
print('DIAG4G parser-only patch applied')
