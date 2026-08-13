from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = 'static uint32_t gpio_link_out4_expiry = 0;\n'
helper = anchor + '''\nstatic bool diag4i_out4_timer_handler(const char* text, const char*& reply) {\n  if (strncmp(text, "LINK OUT4 TIMER", 15) == 0 && (text[15] == 0 || text[15] == ' ')) {\n    reply = "LINK ACK OUT4 TIMER HANDLER";\n    return true;\n  }\n  return false;\n}\n'''
if anchor not in s:
    raise SystemExit('DIAG4I helper anchor not found')
s = s.replace(anchor, helper, 1)

anchor = '  if (gpio_link_sender_ok) {\n'
insert = anchor + '''    if (diag4i_out4_timer_handler(text, gpio_reply)) {\n      gpio_command_recognized = true;\n    }\n'''
if anchor not in s:
    raise SystemExit('DIAG4I call anchor not found')
s = s.replace(anchor, insert, 1)

p.write_text(s)
print('DIAG4I separate OUT4 timer handler call applied')
