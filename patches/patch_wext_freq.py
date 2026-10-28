#!/usr/bin/env python3
# Fix aicwf_get_freq: in monitor mode report the real channel from the vif's
# chanctx instead of hardcoding 2412/ch1, so aireplay-ng reads the right channel.
import sys, io
root = sys.argv[1]
f = root + "/drivers/aic8800/aic8800_fdrv/aicwf_wext_linux.c"
src = io.open(f, encoding="utf-8").read()

old = (
"\t}else{\n"
"\t\twrqu->freq.m = 2412 * 100000;\n"
"\t\twrqu->freq.e = 1;\n"
"\t\twrqu->freq.i = 1;\n"
"\t}\n"
)
new = (
"\t}else{\n"
"\t\tstruct rwnx_hw *rwnx_hw = rwnx_vif->rwnx_hw;\n"
"\t\tint _freq = 2412;\n"
"\t\tif (rwnx_chanctx_valid(rwnx_hw, rwnx_vif->ch_index)) {\n"
"\t\t\tstruct cfg80211_chan_def *_cd = &rwnx_hw->chanctx_table[rwnx_vif->ch_index].chan_def;\n"
"\t\t\tif (_cd->chan)\n"
"\t\t\t\t_freq = _cd->chan->center_freq;\n"
"\t\t}\n"
"\t\twrqu->freq.m = _freq * 100000;\n"
"\t\twrqu->freq.e = 1;\n"
"\t\twrqu->freq.i = ieee80211_frequency_to_channel(_freq);\n"
"\t}\n"
)

if new.split("\n")[1] in src:
    print("already patched"); sys.exit(0)
if old not in src:
    print("PATTERN NOT FOUND"); sys.exit(2)
src = src.replace(old, new, 1)
io.open(f, "w", encoding="utf-8").write(src)
print("patched", f)
