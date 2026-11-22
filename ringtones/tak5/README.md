# TAK5 Ringtones

**Author:** SECT0101
**Version:** 1.0.0

Eight ringtones to go with the TAK5 theme: a DOOM-style metal riff crossed with TAK radio traffic and SIGINT. Most of them carry the same three-hit **TAK . 5** sting (two low hits and a tritone), and three send Morse code like a radio operator.

| Slot | File | What you hear |
|---|---|---|
| Boot | `TAK5_Boot.rtttl` | Scan sweep, Morse **T-A-K**, the riff, the sting |
| Alert | `TAK5_Alert.rtttl` | Intercept burst, Morse **K** (go ahead), the sting |
| Payload Complete | `TAK5_Payload_Complete.rtttl` | SA chirp, the sting resolving up |
| Error | `TAK5_Error.rtttl` | Jammed-signal stutter, then a grind to the floor |
| Battery Low | `TAK5_Battery_Low.rtttl` | Slow heartbeat stepping down |
| Battery Critical | `TAK5_Battery_Critical.rtttl` | Chainsaw buzz, Morse **SOS**, the sting |
| Power Connected | `TAK5_Power_Connected.rtttl` | Quick rise to a high lock tone |
| Power Disconnected | `TAK5_Power_Disconnected.rtttl` | Scan down, signal lost |

## Install

1. Copy the `.rtttl` files to `/root/ringtones/` on the Pager. In the Pager web UI that is **Files > /mmc/root > ringtones > Upload**, or from a terminal:
   `scp TAK5_*.rtttl root@172.16.52.1:/root/ringtones/`
2. On the Pager, assign each file to its slot in the ringtone settings.

Each file holds only the RTTTL line, with no trailing newline, as Hak5's ringtone repo expects.

## Credits

All melodies are original. No game or film music is used.

Unofficial community ringtones. Not affiliated with Hak5 LLC, id Software or the TAK Product Center.
