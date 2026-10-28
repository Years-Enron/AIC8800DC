import sys
p=sys.argv[1]+"/drivers/aic8800/aic8800_fdrv/rwnx_main.c"; s=open(p).read()
old="""#endif /* CONFIG_BR_SUPPORT */

    netif_carrier_off(dev);
    netif_start_queue(dev);

    return error;"""
new="""#endif /* CONFIG_BR_SUPPORT */

    /* keep carrier ON for monitor so the qdisc delivers injected frames */
    if (RWNX_VIF_TYPE(rwnx_vif) != NL80211_IFTYPE_MONITOR)
        netif_carrier_off(dev);
    netif_start_queue(dev);

    return error;"""
assert s.count(old)==1, "carrier block anchor not found/unique"
s=s.replace(old,new,1); open(p,"w").write(s); print("carrier patch applied",p)
