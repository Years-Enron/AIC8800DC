import sys
p=sys.argv[1]+"/drivers/aic8800/aic8800_fdrv/aicwf_txrxif.c"; s=open(p).read()
old="""                msg = kmalloc(aggr_len+4, GFP_KERNEL);
                if(msg == NULL){
                    txrx_err("no more space for msg!\\n");
                    aicwf_prealloc_rxbuff_free(buffer, &rx_priv->rxbuff_lock);
                    return -EBADE;
                }
                memcpy(msg, data, aggr_len + 4);"""
new="""                msg = kmalloc(aggr_len+4, GFP_KERNEL);
                if(msg == NULL){
                    txrx_err("no more space for msg!\\n");
                    aicwf_prealloc_rxbuff_free(buffer, &rx_priv->rxbuff_lock);
                    /* keep rx_cnt symmetric with the URB completion's atomic_inc,
                       otherwise it never returns to 0 and busrx_thread is never
                       woken again (the ==1 wakeup edge is permanently missed) */
                    atomic_dec(&rx_priv->rx_cnt);
                    continue;
                }
                memcpy(msg, data, aggr_len + 4);"""
assert s.count(old)==1, "rx_cnt leak anchor not found/unique"
s=s.replace(old,new,1); open(p,"w").write(s); print("rx_cnt leak patch applied",p)
