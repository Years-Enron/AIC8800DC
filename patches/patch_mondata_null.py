import sys
p=sys.argv[1]+"/drivers/aic8800/aic8800_fdrv/rwnx_rx.c"; s=open(p).read()
old="""        skb_reset_tail_pointer(skb);
        skb->len = 0;
        skb_reset_tail_pointer(skb_monitor);
        skb_monitor->len = 0;
        skb_put(skb_monitor, frm_len);

        if (rwnx_rx_monitor(rwnx_hw, rwnx_vif, skb_monitor, hw_rxhdr, rtap_len))
            dev_kfree_skb(skb_monitor);

        if (status == RX_STAT_MONITOR) {
            if (skb_monitor != skb) {
                dev_kfree_skb(skb);
            }
        }
    }

check_len_update:"""
new="""        /* CONFIG_RWNX_MON_DATA is disabled in this build: when status has
           both RX_STAT_MONITOR and RX_STAT_FORWARD set (frame is on the
           monitor vif AND flagged for upload), the else branch above never
           assigns skb_monitor, which stays NULL here and was unconditionally
           dereferenced below -- a guaranteed NULL-pointer write (observed as
           a kernel oops in the busrx kernel thread under mixed monitor +
           injection traffic). Once that thread dies mid-crash it never frees
           any more rx_buff entries, so the RX buffer pool silently drains to
           0 and capture stops permanently until reboot/replug. Skip monitor
           forwarding instead of crashing; RX_STAT_FORWARD handling further
           down in this function still delivers the frame normally. */
        if (skb_monitor) {
        skb_reset_tail_pointer(skb);
        skb->len = 0;
        skb_reset_tail_pointer(skb_monitor);
        skb_monitor->len = 0;
        skb_put(skb_monitor, frm_len);

        if (rwnx_rx_monitor(rwnx_hw, rwnx_vif, skb_monitor, hw_rxhdr, rtap_len))
            dev_kfree_skb(skb_monitor);

        if (status == RX_STAT_MONITOR) {
            if (skb_monitor != skb) {
                dev_kfree_skb(skb);
            }
        }
        }
    }

check_len_update:"""
assert s.count(old)==1, "mondata null anchor not found/unique"
s=s.replace(old,new,1); open(p,"w").write(s); print("mondata NULL-deref patch applied",p)
