from pathlib import Path
p = Path('examples/companion_radio/MyMesh.cpp')
s = p.read_text()
start = s.find('void MyMesh::onMessageRecv(')
if start < 0:
    raise SystemExit('onMessageRecv start missing')
brace = s.find('{', start)
if brace < 0:
    raise SystemExit('onMessageRecv opening brace missing')
depth = 0
end = None
for i in range(brace, len(s)):
    if s[i] == '{':
        depth += 1
    elif s[i] == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
if end is None:
    raise SystemExit('onMessageRecv closing brace missing')
new = '''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,
                           const char *text) {
  // DIAG4W: isolate markConnectionActive(). Keep queueMessage() active.
  // markConnectionActive(from);  // intentionally skipped
  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);
}'''
s = s[:start] + new + s[end:]
p.write_text(s)
print('DIAG4W: markConnectionActive skipped, queueMessage retained')
