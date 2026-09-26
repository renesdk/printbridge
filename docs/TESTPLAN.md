# Physical acceptance plan before a public stable release

Record the TrueNAS version, printer model, connection type, client version, and
result for each case. Passing software unit tests does not count as a physical
print test.

| Test | Action | Pass condition |
|---|---|---|
| First queue | Add an HL-2035 and send the test page | Correct page comes out |
| Additional queue | Add printer 2 | Both queues print after an app restart |
| Persistence | Recreate container with the same volumes | Queues and settings remain |
| Windows 11 | Add by IPP and print a PDF | Output is legible and A4 |
| Android PDF page | Open `/mobile` on Pixel over Wi-Fi | PDF physically prints |
| Android native Print | Print from Photos or a document app | Queue appears and job prints |
| Network | Test the intended Wi-Fi/VLAN | IPP and, if needed, mDNS are reachable |
| USB | Unplug, reconnect, reboot NAS | The same queue works again |
| Load | Print a large PDF | No out-of-memory kill or stuck queue |
| Upgrade | Switch image tag after backup | Queues remain and printing works |

Mark Android native Print as **unverified** until it is physically tested.
CUPS alone does not confer Mopria certification.
