# Learnings — cpx-usb-bridge

Personal log of concepts learned/reintroduced and bugs hit while building this project. Written for future-me, not for the README.

## Concepts learned / reintroduced

- **USB CDC dual interfaces.** CircuitPython boards can expose a second USB
  serial endpoint (`usb_cdc.data`) separate from the console/REPL serial
  port. Needed for any project where a program — not a human — is talking
  to the board, because the console echoes input (built for terminal use)
  and will corrupt a data protocol.
  Enabled via `boot.py`, which only runs on an actual power cycle, not on
  `code.py` auto-reload — a physical unplug/replug is required after
  editing it.
  - https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html
  - https://learn.adafruit.com/customizing-usb-devices-in-circuitpython/circuitpython-usb-devices#cdc-devices-3-3

- **`boot.py` vs `code.py` vs `boot_out.txt`.**
  - `code.py` — your main program, re-runs on every save (auto-reload).
  - `boot.py` — runs once, before USB initializes; the only place to
    configure `usb_cdc`, drive mode, etc. Requires a real reboot to take effect.
  - `boot_out.txt` — auto-generated log, read-only, confirms what boot.py did.
  - https://docs.circuitpython.org/en/latest/docs/supervisors.html
  - https://learn.adafruit.com/circuitpython-essentials/circuitpython-uart-serial

- **Manual byte-stream framing.** When reading serial data in arbitrary-sized
  chunks, a complete "line" isn't guaranteed per read — you accumulate into
  a buffer and split off complete units (`\n`-terminated) as they appear.
  - `bytes.partition(sep)` returns `(before, sep, after)` and is the right
    tool here — explicitly reassign the buffer to `after` or consumed data
    silently lingers and corrupts the next read.
  - `bytes.split(sep)` returns a list and discards nothing, but doesn't
    hand you back "the remainder" in a form you can reuse as the new
    buffer without manually rejoining — wrong tool for streaming framing.
  - https://docs.python.org/3/library/stdtypes.html#bytes.partition
  - https://docs.python.org/3/library/stdtypes.html#bytes.split

- **`bytes` indexing returns `int`, not a sub-`bytes` object.**
  `b'cool'[0]` is `99` (the int value of `'c'`), not `b'c'`. Slicing
  (`b'cool'[0:1]`) returns `bytes`; indexing does not. This is a real
  source of bugs when porting logic between a list-of-bytes (`split()`
  result) and a single `bytes` object (`partition()` result) — `[0]` means
  something different depending on which you're holding.
  - https://docs.python.org/3/library/stdtypes.html#bytes-and-bytearray-operations

- **`read(n)` vs `readline(n)` on a serial object.**
  `read(n)` reads exactly `n` raw bytes, no newline-seeking — correct for
  "drain everything currently buffered."
  `readline(n)` reads up to `n` bytes *or* stops early at the first `\n`,
  whichever comes first — wrong tool if multiple messages may already be
  queued, since it silently leaves bytes behind.
  - https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial.read
  - https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial.readline

- **USB CDC ignores the configured baud rate.** Unlike physical UART (where
  a baud mismatch produces garbage), USB serial is virtual — CircuitPython
  doesn't enforce the baud value Windows/pyserial displays or sets. Don't
  debug baud mismatches on a USB CDC connection; it's not the failure mode
  this channel can have.
  - https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial

- **Python's pass-by-object-reference.** No syntax-level pass-by-value vs
  pass-by-reference choice exists. Behavior depends on the object's
  mutability: immutables (str, int, tuple) behave like pass-by-value from
  the caller's perspective; mutables (list, dict) behave like
  pass-by-reference. `global` (used for `buf` here) is a separate
  mechanism entirely — shared module-level state, not argument passing.
  - https://docs.python.org/3/faq/programming.html#how-do-i-write-a-function-with-output-parameters-call-by-reference

## Bugs hit and what they taught me

- **Symptom:** CPX responses were garbled, incomplete, or duplicated; state
  changes worked intermittently.
  **Root cause:** Using console serial (`input()`/`print()`) for protocol
  data. Console echoes every byte received, so echo and actual response
  text interleaved unpredictably in the read buffer.
  **Lesson:** Separate the human-debug channel from the machine-protocol
  channel as a default, not an optimization — applies beyond CircuitPython
  to any system with a REPL/console alongside a programmatic interface.

- **Symptom:** Same response/state bug persisted even after improving
  loop timing.
  **Root cause:** It looked like a timing race at first, but timing was a
  symptom, not the cause — the real problem (console echo) was invisible
  from inside either file read in isolation. Tightening sleep intervals
  narrowed the race window without fixing anything.
  **Lesson:** When two independently-timed loops seem to "almost work,"
  suspect a shared-channel/protocol issue before tuning timing further.
  Timing fixes that only partially help are a signal you're treating a
  symptom.

- **Symptom:** `AttributeError: 'int' object has no attribute 'decode'`,
  CPX crashing on first received command with no LED change.
  **Root cause:** Leftover `line[0]` indexing from an earlier `split()`-based
  version of `read_usb()`, not removed after refactoring to `partition()`.
  `partition()` returns `line` as a complete `bytes` object already;
  indexing `[0]` returned an `int`, which has no `.decode()`.
  **Lesson:** When refactoring a working pattern, re-check every line that
  touches a variable whose *shape* changed — not just the line directly
  edited. The bug hid because each line was individually plausible-looking
  for its respective (different) original context.

- **Symptom:** Responses were inconsistent/incomplete even after fixing
  buffer framing — worked for the first command or two, then degraded.
  **Root cause:** The CPX poll loop (`time.sleep(1)`, later `0.05`) and the
  PC's fixed wait-then-read (`time.sleep(0.5)` before `readline()`) were two
  independently-clocked loops with no synchronization between them. The
  responder (CPX) must check for new input *more frequently* than the
  requester expects a reply, or the requester ends up reading stale/partial
  data left over from a previous cycle while the responder is still
  catching up. A 1-second CPX poll against a 0.5-second PC wait guarantees
  this mismatch — the responder is structurally slower than the requester
  assumes.
  **Lesson:** In any request/response protocol over polled channels, the
  responder's poll interval must be safely faster than the requester's
  timeout/wait assumption — never the same order of magnitude, and never
  guessed. Fixing this with "wait a bit longer" (a bigger fixed sleep) is
  fragile; the more robust fix is **read-until-response-or-timeout** on the
  requester side (PC) combined with a fast, cheap poll on the responder
  side (CPX) — fast-and-cheap is viable here specifically because checking
  `serial.in_waiting`/`supervisor.runtime.serial_bytes_available` is a flag
  check, not a blocking call, so polling it frequently costs ~nothing.

- **Symptom:** Two CPX COM ports appear after enabling `usb_cdc.data`, no
  reliable way to tell which is console and which is data from static
  metadata.
  **Root cause:** Windows reports identical `description` and `hwid` for
  both CDC interfaces (same VID:PID) — port number alone doesn't encode role.
  **Lesson:** Some distinctions are behavioral, not structural. When static
  metadata is ambiguous, design a small empirical probe (write known data,
  check for an expected response) rather than guessing from incidental
  signals (port order, driver install timestamp) alone.

## Decisions I'd make differently next time

- Enable `usb_cdc.data` from project start for any CPX↔PC project, rather
  than discovering the need mid-debug. Default checklist item now.
- Write protocol framing (`read_usb`) once, correctly, with manual buffer
  tests before wiring it into the full state-machine loop — would have
  caught the `partition`/`split` mismatch in isolation rather than inside
  a harder-to-read end-to-end failure.

## Open questions / deferred

- No reconnect/retry handling if CPX is unplugged mid-session (PC side
  raises `SerialException` and exits).
- Auto-detection of console vs. data port (currently manual, see README) —
  revisit if/when this needs to run on an unknown machine.
- Single-keyword commands only; no structured/multi-field message format
  yet (relevant once CV integration sends more than a state name).

## Reference index (everything cited above, deduplicated)

- CircuitPython `usb_cdc`: https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html
- Adafruit guide on USB CDC devices: https://learn.adafruit.com/customizing-usb-devices-in-circuitpython/circuitpython-usb-devices#cdc-devices-3-3
- CircuitPython supervisors / boot.py: https://docs.circuitpython.org/en/latest/docs/supervisors.html
- Adafruit UART/serial essentials: https://learn.adafruit.com/circuitpython-essentials/circuitpython-uart-serial
- Python `bytes` methods (partition/split): https://docs.python.org/3/library/stdtypes.html#bytes.partition
- pyserial API reference: https://pyserial.readthedocs.io/en/latest/pyserial_api.html
- Python pass-by-reference FAQ: https://docs.python.org/3/faq/programming.html#how-do-i-write-a-function-with-output-parameters-call-by-reference
