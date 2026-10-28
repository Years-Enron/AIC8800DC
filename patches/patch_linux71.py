import re, sys
d=sys.argv[1]+"/drivers/aic8800/aic8800_fdrv/"
G="#if LINUX_VERSION_CODE >= KERNEL_VERSION(7, 1, 0)\n"
# rx.c
p=d+"rwnx_rx.c"; s=open(p).read()
s=s.replace("(int)in_irq()","(int)in_hardirq()")
s=s.replace("cfg80211_rx_spurious_frame(rwnx_vif->ndev, hdr->addr2, GFP_ATOMIC);",
            G+"            cfg80211_rx_spurious_frame(rwnx_vif->ndev, hdr->addr2, -1, GFP_ATOMIC);\n#else\n            cfg80211_rx_spurious_frame(rwnx_vif->ndev, hdr->addr2, GFP_ATOMIC);\n#endif")
m=re.search(r"cfg80211_rx_unexpected_4addr_frame\(rwnx_vif->ndev,\s*([^;]*?),\s*GFP_ATOMIC\);", s)
assert m, "4addr not found"
old=m.group(0); new=G+old.replace(", GFP_ATOMIC);", ", -1, GFP_ATOMIC);")+"\n#else\n"+old+"\n#endif"
s=s.replace(old,new,1); open(p,"w").write(s)
# tdls
p=d+"rwnx_tdls.c"; s=open(p).read()
old="""        skb_put(skb, 1 + sizeof(mgmt->u.action.u.tdls_discover_resp));
        mgmt->u.action.category = WLAN_CATEGORY_PUBLIC;
        mgmt->u.action.u.tdls_discover_resp.action_code = WLAN_PUB_ACTION_TDLS_DISCOVER_RES;
        mgmt->u.action.u.tdls_discover_resp.dialog_token = dialog_token;
        mgmt->u.action.u.tdls_discover_resp.capability =
            cpu_to_le16(rwnx_get_tdls_sta_capab(rwnx_vif, status_code));
"""
assert s.count(old)==1
new=G+"""        skb_put(skb, 2 + sizeof(mgmt->u.action.tdls_discover_resp));
        mgmt->u.action.category = WLAN_CATEGORY_PUBLIC;
        mgmt->u.action.action_code = WLAN_PUB_ACTION_TDLS_DISCOVER_RES;
        mgmt->u.action.tdls_discover_resp.dialog_token = dialog_token;
        mgmt->u.action.tdls_discover_resp.capability =
            cpu_to_le16(rwnx_get_tdls_sta_capab(rwnx_vif, status_code));
#else
"""+old+"#endif\n"
s=s.replace(old,new); open(p,"w").write(s)
# main.c
p=d+"rwnx_main.c"; s=open(p).read()
o1="\t\t        cfg80211_new_sta(rwnx_vif->ndev, sta->mac_addr, &sinfo, GFP_KERNEL);\n"; assert s.count(o1)==1
s=s.replace(o1,G+"\t\t        cfg80211_new_sta(&rwnx_vif->wdev, sta->mac_addr, &sinfo, GFP_KERNEL);\n#else\n"+o1+"#endif\n")
o2="                \t\tcfg80211_del_sta(rwnx_vif->ndev, cur->mac_addr, GFP_KERNEL);\n"; assert s.count(o2)==1
s=s.replace(o2,G+"                \t\tcfg80211_del_sta(&rwnx_vif->wdev, cur->mac_addr, GFP_KERNEL);\n#else\n"+o2+"#endif\n")
block=G+r'''/* Linux >= 7.1 cfg80211 op signature adapters */
static int rwnx_cfg80211_add_key_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        int link_id, u8 key_index, bool pairwise, const u8 *mac_addr, struct key_params *params)
{ return rwnx_cfg80211_add_key(wiphy, wdev->netdev, link_id, key_index, pairwise, mac_addr, params); }
static int rwnx_cfg80211_get_key_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        int link_id, u8 key_index, bool pairwise, const u8 *mac_addr, void *cookie,
        void (*callback)(void *cookie, struct key_params *))
{ return rwnx_cfg80211_get_key(wiphy, wdev->netdev, link_id, key_index, pairwise, mac_addr, cookie, callback); }
static int rwnx_cfg80211_del_key_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        int link_id, u8 key_index, bool pairwise, const u8 *mac_addr)
{ return rwnx_cfg80211_del_key(wiphy, wdev->netdev, link_id, key_index, pairwise, mac_addr); }
static int rwnx_cfg80211_set_default_mgmt_key_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        int link_id, u8 key_index)
{ return rwnx_cfg80211_set_default_mgmt_key(wiphy, wdev->netdev, link_id, key_index); }
static int rwnx_cfg80211_add_station_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        const u8 *mac, struct station_parameters *params)
{ return rwnx_cfg80211_add_station(wiphy, wdev->netdev, mac, params); }
static int rwnx_cfg80211_del_station_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        struct station_del_parameters *params)
{ return rwnx_cfg80211_del_station_compat(wiphy, wdev->netdev, params); }
static int rwnx_cfg80211_change_station_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        const u8 *mac, struct station_parameters *params)
{ return rwnx_cfg80211_change_station(wiphy, wdev->netdev, mac, params); }
static int rwnx_cfg80211_get_station_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        const u8 *mac, struct station_info *sinfo)
{ return rwnx_cfg80211_get_station(wiphy, wdev->netdev, mac, sinfo); }
static int rwnx_cfg80211_dump_station_wdev(struct wiphy *wiphy, struct wireless_dev *wdev,
        int idx, u8 *mac, struct station_info *sinfo)
{ return rwnx_cfg80211_dump_station(wiphy, wdev->netdev, idx, mac, sinfo); }
static int rwnx_cfg80211_set_wiphy_params_radio(struct wiphy *wiphy, int radio_idx, u32 changed)
{ return rwnx_cfg80211_set_wiphy_params(wiphy, changed); }
static int rwnx_cfg80211_set_tx_power_radio(struct wiphy *wiphy, struct wireless_dev *wdev,
        int radio_idx, enum nl80211_tx_power_setting type, int mbm)
{ return rwnx_cfg80211_set_tx_power(wiphy, wdev, type, mbm); }
#define rwnx_cfg80211_add_key rwnx_cfg80211_add_key_wdev
#define rwnx_cfg80211_get_key rwnx_cfg80211_get_key_wdev
#define rwnx_cfg80211_del_key rwnx_cfg80211_del_key_wdev
#define rwnx_cfg80211_set_default_mgmt_key rwnx_cfg80211_set_default_mgmt_key_wdev
#define rwnx_cfg80211_add_station rwnx_cfg80211_add_station_wdev
#define rwnx_cfg80211_del_station_compat rwnx_cfg80211_del_station_wdev
#define rwnx_cfg80211_change_station rwnx_cfg80211_change_station_wdev
#define rwnx_cfg80211_get_station rwnx_cfg80211_get_station_wdev
#define rwnx_cfg80211_dump_station rwnx_cfg80211_dump_station_wdev
#define rwnx_cfg80211_set_wiphy_params rwnx_cfg80211_set_wiphy_params_radio
#define rwnx_cfg80211_set_tx_power rwnx_cfg80211_set_tx_power_radio
#endif

'''
a="static struct cfg80211_ops rwnx_cfg80211_ops = {"; assert s.count(a)==1
s=s.replace(a,block+a); open(p,"w").write(s); print("ref patched")
