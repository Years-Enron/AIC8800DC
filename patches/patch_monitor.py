import sys
p=sys.argv[1]+"/drivers/aic8800/aic8800_fdrv/rwnx_main.c"; s=open(p).read()
o1="""            if ((vif_el != vif) &&
               (RWNX_VIF_TYPE(vif) != NL80211_IFTYPE_MONITOR)) {"""
n1="""            if ((vif_el != vif) &&
               (RWNX_VIF_TYPE(vif_el) != NL80211_IFTYPE_P2P_DEVICE) &&
               (RWNX_VIF_TYPE(vif_el) != NL80211_IFTYPE_MONITOR)) {"""
o2="""        if ((RWNX_VIF_TYPE(vif) == NL80211_IFTYPE_MONITOR) ||
           (type == NL80211_IFTYPE_MONITOR)) {"""
n2="""        if (RWNX_VIF_TYPE(vif) == NL80211_IFTYPE_P2P_DEVICE)
            continue;
        if ((RWNX_VIF_TYPE(vif) == NL80211_IFTYPE_MONITOR) ||
           (type == NL80211_IFTYPE_MONITOR)) {"""
assert s.count(o1)==1 and s.count(o2)==1
s=s.replace(o1,n1).replace(o2,n2); open(p,"w").write(s); print("monitor patched", p)
