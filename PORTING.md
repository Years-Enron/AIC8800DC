# Porting / build notes — AIC8800DC on modern kernels

Reference notes for building and running this driver on current kernels. Status: managed
Wi-Fi, monitor capture, and 802.11 injection all verified on an AIC8800DC `a69c:88de` dongle
(chip `chip_id=7, chip_sub_id=1`, the "MCU1" variant).

## Mode switching (storage → Wi-Fi)

The dongle enumerates first as a USB mass-storage device ("driver disk", `a69c:5721/5722`).
It only presents the Wi-Fi interface (`a69c:88de`) after that storage device is **ejected**.

- The `tools/aic.rules` udev rule handles this automatically (`eject` on the storage node).
- Manually: `eject /dev/aicudisk` (or the device's `sd*` node).
- After a *failed* probe the chip can hang as `a69c:88dc`; clear it with a physical replug.

In a VM, do the eject/mode-switch on the **host** and then attach the `88de` device to the
guest. Switching mode from inside the guest tends to upset virtual xHCI (enumeration
`error -71`); if that happens, detach and reattach the USB device once.

Host-side USB check (macOS example):

```bash
ioreg -p IOUSB -l | grep -i -A12 'Aic MSC\|AIC8800DC' | grep '"idProduct"'
# 22306 = 0x5722 (storage mode), 35038 = 0x88de (Wi-Fi mode)
```

## Driver / firmware

- DKMS package `aic8800-ref/1.0` builds `aic_load_fw.ko` + `aic8800_fdrv.ko` into
  `/lib/modules/$(uname -r)/updates/dkms/` and rebuilds on kernel upgrade.
- Firmware lives at `/lib/firmware/aic8800DC/` (vendor `_u02` blobs), RAM-loaded each probe.
- On a fresh (non-hung) `88de` device, `modprobe aic8800_fdrv` loads cleanly with no USB cycle.
- An unrelated `aic8800-usb/5.0` DKMS package (radxa-pkg) does **not** work with this dongle
  (`cmd_mgr_queue cmd timed-out` at `rwnx_ic_system_init`). Use this `aic8800-ref` package.

## Kernel 7.1 build port (`patches/patch_linux71.py`)

The vendor driver targets roughly kernel ≤ 6.1. For kernel ≥ 7.1 the cfg80211 ops changed
shape. The patch adds, under `#if LINUX_VERSION_CODE >= KERNEL_VERSION(7,1,0)`, wrapper ops
that take `struct wireless_dev *wdev` and forward to the existing net_device versions via
`wdev->netdev`, with `#define` renames placed before `rwnx_cfg80211_ops`:

- add/get/del_key, set_default_mgmt_key
- add/del/change/get/dump_station
- set_wiphy_params (gains `int radio_idx`)
- set_tx_power (gains `int radio_idx`)
- `cfg80211_new_sta` / `cfg80211_del_sta` pass `&rwnx_vif->wdev`

Plus: `in_irq()` → `in_hardirq()`; `cfg80211_rx_spurious_frame` /
`cfg80211_rx_unexpected_4addr_frame` gain a `link_id` (-1) argument; TDLS discover-response
field moves (`u.action.u.tdls_discover_resp` → `u.action.tdls_discover_resp`, `skb_put` size
`1 +` → `2 +`). This is what makes the module compile on 7.1.

## Monitor mode and injection

These are standard 802.11 driver capabilities; the vendor source shipped them disabled or
broken on this variant. The fixes are small and documented per-script in the README table.
Key ones:

- `CONFIG_RWNX_MON_XMIT=y` to compile and wire the monitor `ndo_start_xmit` handler
  (`patch_inject.py`).
- Don't call `netif_carrier_off()` on monitor interfaces, or the qdisc drops every injected
  frame while the interface sits at NO-CARRIER (`patch_carrier.py`). This was the decisive fix.
- Report the real mode/channel to legacy Wireless-Extensions ioctls so userspace tools
  recognize monitor mode (`patch_wext.py`, `patch_wext_freq.py`).

The chip is the MCU1 variant that upstream leaves injection disabled on "pending validation";
no firmware change was needed — the blockers were the driver bugs above.

## Test results (kernel 7.1.5 arm64)

- `iw list`: managed, AP, monitor, mesh, P2P supported; 2.4 GHz band only.
- Managed scan: APs enumerated normally.
- Monitor capture: `tcpdump`/`airodump-ng` on the monitor interface see beacons and data.
- Injection: `aireplay-ng -9` self-test passes ("Injection is working!").
- No kernel oops across the above; stopping monitor and restarting NetworkManager restores
  managed mode.

## Build gotchas

- Only 2.4 GHz is available on this unit.
- After a failed probe, a physical replug is required (detach/reattach alone won't clear the
  hung `88dc` state).
- The `monitor xmit: netif_carrier_on` dmesg line fires once per interface `open`, not per
  frame — don't use it as a TX counter.

## References

- [shenmintao/aic8800d80](https://github.com/shenmintao/aic8800d80) — related D80/MCU0 driver;
  `CONFIG_RWNX_MON_XMIT` and radiotap-validation fixes originate here.
- [idawnlight/AIC8800DC](https://github.com/idawnlight/AIC8800DC) — the base kernel-port of the
  UGREEN vendor driver this repo builds on.
