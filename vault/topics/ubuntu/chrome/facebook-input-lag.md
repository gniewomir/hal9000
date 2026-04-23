# Facebook input lag in Chrome on Ubuntu 24.04

## What it looks like

- Noticeable typing delay / “rubber banding” while composing posts/comments or using Messenger in `facebook.com`.
- Sometimes correlates with brief UI stalls (e.g., video momentarily freezing while you type / hit backspace).

## Likely causes (most common on 24.04)

### 1) Graphics/compositor path (Wayland vs Xorg/XWayland) + GPU acceleration

There are reports of **input lag on Ubuntu 24.04 under Xorg** that also **momentarily freezes video** and disappears when moving to Wayland. See: `https://askubuntu.com/questions/1522560/ubuntu-24-04-with-keyboard-input-lag`.

Chrome on Linux can also become sluggish in ways tied to **GPU driver / hardware acceleration**, with common mitigations being updating GPU drivers or disabling hardware acceleration. See: `https://askubuntu.com/questions/1426911/sluggish-input-reaction-in-chrome-on-ubuntu-22-04`.

On some Mesa driver stacks, Chrome GPU acceleration can be unstable enough to hang the system; software rendering (SwiftShader) works around it. See: `https://bugs.launchpad.net/bugs/2121301`.

### 2) Wayland text input protocol / IME selection

On Wayland, Chromium has had text input issues depending on which protocol/path is used. Chromium M136 made **Wayland text-input-v3 enabled by default** because GTK IME fallback was “not recommended” and was leading to issues if v3 wasn’t enabled. See: `https://github.com/chromium/chromium/commit/7fbc4efa5f8f395aee29d73f46cdb1302e20c536`.

If you’re on a Chrome/Chromium version older than that change, this can still matter.

## Quick triage checklist (5 minutes)

1) Confirm session type:
   - GNOME: **Settings → About → Windowing System** should say **Wayland** or **X11**.
2) In Chrome:
   - Visit `chrome://gpu` and note whether features are enabled/disabled.
3) Reproduce in a clean profile:
   - Run Chrome with a temporary profile and no extensions (see below).

## Fixes to try (in order)

### A) If you are on Xorg: try Wayland first

- Log out → choose the **Ubuntu (Wayland)** session at the login screen.
- Re-test Facebook typing.

Rationale: Ubuntu 24.04 reports indicate Xorg-specific regressions where “input lag + short video freeze” goes away on Wayland (`https://askubuntu.com/questions/1522560/ubuntu-24-04-with-keyboard-input-lag`).

### B) Force Chrome to run native Wayland (avoid XWayland)

If you’re on Wayland but Chrome is still running through XWayland, force Ozone/Wayland:

```bash
google-chrome --ozone-platform=wayland
```

Sometimes also helps:

```bash
google-chrome --ozone-platform=wayland --enable-features=UseOzonePlatform
```

### C) Toggle hardware acceleration (fastest A/B test)

1) In Chrome, open `chrome://settings/system`.
2) Toggle **Use hardware acceleration when available**.
3) Fully restart Chrome (quit all Chrome processes), then re-test Facebook.

If disabling HW accel fixes it, the next step is usually **driver/Mesa updates** rather than living without acceleration forever.

### D) Try a “no extensions” reproduction run

This isolates extension content scripts (adblockers, privacy tools, password managers) that can cause input latency on heavy SPAs:

```bash
google-chrome --user-data-dir="$(mktemp -d)" --disable-extensions
```

If the lag disappears here, re-enable extensions one by one (or keep Facebook in a profile with minimal extensions).

### E) If the GPU stack is the problem: test SwiftShader/software paths

This is mainly a diagnostic step: if software rendering removes lag/stutter, you’ve narrowed it down to the GPU pipeline.

```bash
google-chrome --use-gl=swiftshader --disable-gpu-rasterization --disable-zero-copy
```

See also a Mesa/Chrome case where SwiftShader is the stable workaround (`https://bugs.launchpad.net/bugs/2121301`).

### F) Wayland text input v3 (if you’re on older Chrome/Chromium)

- Check `chrome://version` (milestone).
- If you’re below the change that enabled it by default (Chromium M136), try enabling:
  - `chrome://flags/#wayland-text-input-v3`

Reference: `https://github.com/chromium/chromium/commit/7fbc4efa5f8f395aee29d73f46cdb1302e20c536`.

## Notes / what to capture for debugging

- Windowing system: Wayland vs X11.
- `chrome://version` and `chrome://gpu` summary.
- GPU model + driver (`lspci -k | rg -i "vga|3d|display|driver"`).
- Whether lag happens only on Facebook or across other SPAs (Gmail, Discord web, etc.).