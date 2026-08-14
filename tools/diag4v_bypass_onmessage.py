from pathlib import Path
p=Path('examples/companion_radio/MyMesh.cpp')
s=p.read_text()
old='''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,\n                           const char *text) {\n  markConnectionActive(from); // in case this is from a server, and we have a connection\n  queueMessage(from, TXT_TYPE_PLAIN, pkt, sender_timestamp, NULL, 0, text);\n}\n'''
new='''void MyMesh::onMessageRecv(const ContactInfo &from, mesh::Packet *pkt, uint32_t sender_timestamp,\n                           const char *text) {\n  // DIAG4V: bypass all normal received-contact-message handling.\n  // If a received text still reboots the node, the fault is before this callback.\n  (void)from;\n  (void)pkt;\n  (void)sender_timestamp;\n  (void)text;\n  return;\n}\n'''
if old not in s: raise SystemExit('onMessageRecv anchor missing')
s=s.replace(old,new,1)
p.write_text(s)
print('DIAG4V: onMessageRecv fully bypassed')
