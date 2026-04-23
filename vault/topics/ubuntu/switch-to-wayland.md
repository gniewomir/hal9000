# Permanently use Wayland instead of X11 (Ubuntu 24.04 LTS, 2025/2026)

Context: **default Ubuntu Desktop** uses **GDM 3** and **GNOME**. Steps differ on other flavors (e.g. Kubuntu uses SDDM, Xubuntu uses LightDM). Below assumes stock **ubuntu-desktop** (GNOME on Wayland by default for many setups).

## 1. Enable Wayland in GDM

Edit the display manager config:

```bash
sudo nano /etc/gdm3/custom.conf
```

In the `[daemon]` section:

- Ensure Wayland is **not** disabled. Set explicitly: `WaylandEnable=true`, or if the only line is `WaylandEnable=false`, **remove it or comment it out** (leading `#`) so GDM is not told to use X11 only.

Ubuntu’s schema default for GDM is Wayland-capable; this file is the main switch people/X11 toggles use to turn Wayland off entirely.

Then reboot (or at least restart GDM, which logs you out):

```bash
sudo systemctl restart gdm3
```

## 2. Pick the Wayland **session** at login (and make it stick)

GDM can remember **“Ubuntu on Xorg”** if that was selected once (gear on the password screen).

- On the **login screen**, open the **session menu (gear)** and choose **“Ubuntu”** or **“Ubuntu on Wayland”**, **not** **“Ubuntu on Xorg”**.

Session definitions live under:

- `/usr/share/wayland-sessions/` (e.g. `ubuntu.desktop`, `ubuntu-wayland.desktop`)
- `/usr/share/xsessions/` (e.g. `ubuntu-xorg.desktop`)

If the session keeps reverting, check **per-user** settings (as root) under `/var/lib/AccountsService/users/<username>` for a **session** that pins X11, and align it with a Wayland-capable `ubuntu` session, or clear the override—exact keys vary slightly by release; the login chooser is the normal fix.

## 3. Intel / AMD (typical case)

With **GDM** allowing Wayland and the **Wayland** session selected, you should get:

```bash
echo "$XDG_SESSION_TYPE"   # wayland
```

If it still says `x11`, re-check steps 1 and 2 before chasing drivers.

## 4. NVIDIA (often why you still get X11)

On Ubuntu, **`/usr/lib/udev/rules.d/61-gdm.rules`** runs **`gdm-runtime-config`** to set GDM’s **preferred display server** (Xorg vs Wayland) and related flags based on **GPU, driver, modesetting, hybrid graphics**, and (on current trees) some **OEM** cases. In practice, **many systems with the proprietary NVIDIA driver** end up with **Xorg preferred** or Wayland **disabled** unless conditions for Wayland (e.g. `nvidia-drm` **modeset**) are met.

**Baseline for Wayland on NVIDIA (when the stack supports it):**

- Enable **DRM KMS** for the NVIDIA stack, e.g. `/etc/modprobe.d/nvidia.conf`:
  - `options nvidia-drm modeset=1`
- Rebuild initramfs if your distro documents it: `sudo update-initramfs -u`, then reboot.

If you are **still** forced to X11 because of udev’s **“prefer Xorg”** path, fixes seen in the wild are **version-specific and invasive** (overriding or masking udev rules, or using downstream docs for “force Wayland on NVIDIA”). Treat those as **last resort**: they can break GDM on upgrade and are not a single stable recipe for all 24.04 point releases—re-check `61-gdm.rules` after **gdm3** / driver updates (2025/2026 SRUs have changed this area).

**Hybrid (Intel + NVIDIA) laptops** add extra udev branches; expect more variability.

## 5. Verify after reboot

```bash
echo "$XDG_SESSION_TYPE"
# expect: wayland
```

Useful when debugging:

```bash
loginctl show-session "$XDG_SESSION_ID" -p Type
```

Optional:

```bash
echo "$XDG_CURRENT_DESKTOP"
```

## 6. If Wayland is missing entirely

- **VM / simple framebuffer / `nomodeset`**: udev and kernel cmdline can **disable Wayland**; fix guest drivers, **remove `nomodeset`**, and ensure a real **KMS** path for your GPU.
- **Extensions / tools** that only support X11: they do not “switch the compositor”; they only affect what runs **inside** your session.

## Summary

| Goal | Action |
|------|--------|
| System allows Wayland | `/etc/gdm3/custom.conf` → `WaylandEnable=true` (and not `false`) |
| You actually log into Wayland | GDM **gear** → **Ubuntu** / **Ubuntu on Wayland**, not **Ubuntu on Xorg** |
| NVIDIA still on X11 | `nvidia-drm` **modeset**, then (if still stuck) udev/GDM + driver specifics—**expect churn** in 24.04.x |
| Confirm | `XDG_SESSION_TYPE=wayland` |
