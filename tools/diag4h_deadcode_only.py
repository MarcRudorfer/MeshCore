from pathlib import Path

p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()

anchor = 'static uint32_t gpio_link_out4_expiry = 0;\n'
extra = anchor + '''
__attribute__((used,noinline)) static const char* diag4h_out4_timer_deadcode(const char* text) {
  if (text && text[0] == 'X') {
    return "LINK ACK OUT4 TIMER PARSER";
  }
  return nullptr;
}
'''

if anchor not in s:
    raise SystemExit('DIAG4H anchor not found')
s = s.replace(anchor, extra, 1)
p.write_text(s)
print('DIAG4H dead-code-only helper applied')
