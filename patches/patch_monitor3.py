import sys
p=sys.argv[1]+"/drivers/aic8800/aic8800_fdrv/rwnx_main.c"; s=open(p).read()
o="""        if (RWNX_VIF_TYPE(vif) == NL80211_IFTYPE_P2P_DEVICE || !vif->up)
            continue;
        if ((RWNX_VIF_TYPE(vif) == NL80211_IFTYPE_MONITOR) ||
           (type == NL80211_IFTYPE_MONITOR)) {"""
n="""        /* relaxed: airmon-ng adds the new vif before deleting the old one; fw vif is only created on open */
        if (1)
            continue;
        if ((RWNX_VIF_TYPE(vif) == NL80211_IFTYPE_MONITOR) ||
           (type == NL80211_IFTYPE_MONITOR)) {"""
assert s.count(o)==1; s=s.replace(o,n); open(p,"w").write(s); print("monitor3 patched",p)
