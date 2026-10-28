import sys
base=sys.argv[1]+"/drivers/aic8800/aic8800_fdrv/"
# 1) Makefile: enable MON_XMIT
mk=base+"Makefile"; s=open(mk).read()
assert "CONFIG_RWNX_MON_XMIT ?= n" in s, "MON_XMIT flag not found"
s=s.replace("CONFIG_RWNX_MON_XMIT ?= n","CONFIG_RWNX_MON_XMIT ?= y",1); open(mk,"w").write(s)
# 2) rwnx_tx.c: harden radiotap validation (shenmintao 81b8b33), drop tmp_len
tx=base+"rwnx_tx.c"; s=open(tx).read()
s=s.replace("    int rtap_len, ret, idx, tmp_len;\n    struct ieee80211_radiotap_header *rtap_hdr;",
            "    int rtap_len, ret, idx;\n    struct ieee80211_radiotap_header *rtap_hdr;",1)
old="""    rtap_hdr = (struct ieee80211_radiotap_header*)(rtap_buf);
    rtap_len = ieee80211_get_radiotap_len(rtap_buf);//max_length
    frame_len = skb->len;

    AICWFDBG(LOGINFO, "rwnx_start_monitor_if_xmit, skb_len=%d, rtap_len=%d\\n", skb->len, rtap_len);
//rwnx_data_dump((char*)__func__, skb->data, skb->len);
    if((g_rwnx_plat->usbdev->chipid == PRODUCT_ID_AIC8801) ||
        ((g_rwnx_plat->usbdev->chipid == PRODUCT_ID_AIC8800DC ||
        g_rwnx_plat->usbdev->chipid == PRODUCT_ID_AIC8800DW) && chip_id < 3)){
            nx_off_chan_txq_idx = NX_OFF_CHAN_TXQ_IDX_FOR_OLD_IC;
    }


    if (unlikely(rtap_hdr->it_version)){
        AICWFDBG(LOGERROR, "%s itv \\r\\n", __func__);
        goto free_tag;
        }

    if (unlikely(skb->len < rtap_len)){
        AICWFDBG(LOGERROR, "%s skb->len < rtap_len \\r\\n", __func__);
        goto free_tag;
        }

    if (unlikely(rtap_len < sizeof(struct ieee80211_radiotap_header))){
        AICWFDBG(LOGERROR, "%s rtap_len < sizeof(struct ieee80211_radiotap_header) \\r\\n", __func__);
        goto free_tag;
        }
"""
new="""    frame_len = skb->len;

    if (unlikely(skb->len < sizeof(*rtap_hdr))) {
        AICWFDBG(LOGERROR, "%s radiotap header is truncated\\n", __func__);
        goto free_tag;
    }

    rtap_hdr = (struct ieee80211_radiotap_header*)(rtap_buf);
    if (unlikely(rtap_hdr->it_version)) {
        AICWFDBG(LOGERROR, "%s itv \\r\\n", __func__);
        goto free_tag;
    }

    rtap_len = ieee80211_get_radiotap_len(rtap_buf);//max_length
    if (unlikely(rtap_len < sizeof(struct ieee80211_radiotap_header))) {
        AICWFDBG(LOGERROR, "%s rtap_len < sizeof(struct ieee80211_radiotap_header) \\r\\n", __func__);
        goto free_tag;
    }

    if (unlikely(skb->len < rtap_len)) {
        AICWFDBG(LOGERROR, "%s skb->len < rtap_len \\r\\n", __func__);
        goto free_tag;
    }

    AICWFDBG(LOGINFO, "rwnx_start_monitor_if_xmit, skb_len=%d, rtap_len=%d\\n", skb->len, rtap_len);
//rwnx_data_dump((char*)__func__, skb->data, skb->len);
    if((g_rwnx_plat->usbdev->chipid == PRODUCT_ID_AIC8801) ||
        ((g_rwnx_plat->usbdev->chipid == PRODUCT_ID_AIC8800DC ||
        g_rwnx_plat->usbdev->chipid == PRODUCT_ID_AIC8800DW) && chip_id < 3)){
            nx_off_chan_txq_idx = NX_OFF_CHAN_TXQ_IDX_FOR_OLD_IC;
    }
"""
assert s.count(old)==1, "tx block anchor not unique/found"
s=s.replace(old,new,1); open(tx,"w").write(s)
print("inject patch applied", base)
