> **English** · [中文](README.md)

# AIC8800DC / FC Linux driver (UGREEN CM760-35262)

Out-of-tree Linux driver for the **AIC8800DC/FC** USB Wi-Fi chip, as shipped in the
**UGREEN CM760-35262** adapter (USB ID `a69c:88de`). This is the vendor (UGREEN / AICSemi)
driver with patches to build and run on modern kernels, including the cfg80211 API changes
up to **kernel 7.1**.

Verified on **Linux 7.1.5 (arm64)** on Kali, and previously on kernel 6.16 (openSUSE Tumbleweed).
Managed-mode Wi-Fi, monitor mode, and 802.11 frame injection all work on this hardware.

> **Provenance / credit.** I did not write this driver. The code comes from the UGREEN
> CM760-35262 vendor driver (originally from <https://www.lulian.cn/download/122.html>).
> My changes only adapt it to newer kernels and fix a few driver bugs. Some fixes are adapted
> from [shenmintao/aic8800d80](https://github.com/shenmintao/aic8800d80) and the base port from
> [idawnlight/AIC8800DC](https://github.com/idawnlight/AIC8800DC). Credit to the original authors.
> Apart from build/compatibility issues I can't offer support.

## Hardware

- Chip: AIC8800DC/FC, reported as `chip_id=7, chip_sub_id=1` (the "MCU1" variant).
- USB identities of the dongle:
  - `a69c:5721` / `a69c:5722` — virtual CD / mass-storage ("driver disk") mode.
  - `a69c:88de` — Wi-Fi mode, appears after the storage device is ejected.
- Band: 2.4 GHz only on this unit (no 5 GHz).
- Firmware is RAM-loaded from `/lib/firmware/aic8800DC/` on every probe (not flashed).

The included `tools/aic.rules` udev rule ejects the storage device automatically so the chip
switches into Wi-Fi mode.

## Install

```bash
# 1. install firmware + udev rule (ejects the "driver disk" to switch to Wi-Fi mode)
chmod +x install_setup.sh
sudo ./install_setup.sh

# 2. build the kernel modules
cd drivers/aic8800
make
sudo make install

# 3. load
sudo modprobe aic_load_fw
sudo modprobe aic8800_fdrv
```

`wlan0` (or a predictable name) should appear; `iw dev` lists the interface.

### DKMS (rebuild automatically on kernel upgrade)

```bash
sudo cp -r . /usr/src/aic8800-ref-1.0
sudo dkms add    aic8800-ref/1.0
sudo dkms build  aic8800-ref/1.0
sudo dkms install aic8800-ref/1.0 --force
```

## Uninstall

```bash
sudo ./uninstall_setup.sh                 # remove firmware + udev rule
sudo dkms remove aic8800-ref/1.0 --all    # if installed via DKMS
```

## `patches/` — how the port was produced

The `drivers/` tree here is **already patched** and builds as-is. The scripts in `patches/`
are kept as a record of the individual changes applied on top of the original UGREEN vendor
source; each takes the repo root as its argument and edits
`drivers/aic8800/aic8800_fdrv/*`. They are meant to be replayed against the *pristine vendor
tree*, not this one.

| script | what it does |
| --- | --- |
| `patch_linux71.py` | cfg80211 / nl80211 API port for kernel ≥ 7.1 (wdev-based key & station ops, `radio_idx` params, `in_hardirq`, TDLS field moves). This is what makes it build on 7.1. |
| `patch_monitor.py`, `patch_monitor2.py`, `patch_monitor3.py` | let `iw ... set type monitor` succeed (stop counting the auto-created P2P-device vif as a conflicting data interface; fix a vif/vif_el typo). |
| `patch_wext.py` | make the legacy Wireless-Extensions `SIOCGIWMODE` report the real interface mode, so tools that read it recognize monitor mode. |
| `patch_wext_freq.py` | report the real monitor channel from the vif chanctx instead of a hardcoded value. |
| `patch_inject.py` | enable the monitor TX path (`CONFIG_RWNX_MON_XMIT=y`) and bounds-check the radiotap header before parsing. |
| `patch_carrier.py` | keep carrier ON for monitor interfaces (vendor code did an unconditional `netif_carrier_off`, so the qdisc dropped injected frames). |
| `patch_rxcnt_leak.py` | keep `rx_cnt` balanced on the "no msg buffer" error path so the busrx thread keeps getting woken. |
| `patch_mondata_null.py` | guard a monitor-forward path that could dereference a NULL `skb_monitor` when `CONFIG_RWNX_MON_DATA` is off. |

## Notes

See [`PORTING.md`](PORTING.md) for detailed build/compatibility notes and test results.

## License

The kernel modules declare `MODULE_LICENSE("GPL")`. See [`LICENSE`](LICENSE) (GPL-2.0).
Firmware blobs under `fw/` are redistributable vendor firmware and are not covered by the GPL.
