#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import anvil.server
import pandas as pd
import torch
import numpy as np
from torch.utils.data import Dataset
import datetime
if __name__ == "__main__":
    from utils.backtesting import gen_pnl
else:
    from .utils.backtesting import gen_pnl


# In[ ]:


ANVIL_CLIENT_KEY="FMQBTGZ2T6DRDZISLDZ3XMIH-BRX4OESLV4HADBHN-CLIENT"
# anvil.server.connect(ANVIL_CLIENT_KEY)


# In[ ]:


class NuminDataset(Dataset):
    def __init__(self, samples, targets):
        self.samples = samples
        self.targets = targets

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        # Perform any necessary transformations here
        x = torch.tensor(self.samples[idx]).float()
        y = torch.tensor(self.targets[idx]).long()
        return x, y


# In[ ]:


class Numin2API():
    def __init__(self, api_key: str = None):
        """
        Initializes the Numin2API instance.

        Parameters:
        - api_key (str, optional): The API key for authenticating requests.
        """
        
        print("importing numin2")

        self.api_key = api_key
        self.uplink_key = ANVIL_CLIENT_KEY # trader uplink key
        
        anvil.server.connect(self.uplink_key) 

    def get_data_for_month(self,year,month,batch_size=4,window_size=100,target_type='rank',features='returns'):
        XR,YR=anvil.server.call('get_data_for_month',year=year,month=month,batch_size=batch_size,window_size=window_size,target_type=target_type,features=features)
        # numin_dataset = NuminDataset(XR, YR)
        return XR,YR
    
    def download_data(self,outfile=None,type='daily',features='returns'):
        file_media=anvil.server.call('download_raw_data',type=type,features=features)
        if outfile is None:
            outfile=f'/tmp/consolidated_{type}_{features}.parquet'
        with open(outfile,'wb') as f:
            f.write(file_media.get_bytes())

    def backtest_positions(self,positions,targets,txn_cost=.1,prev_position=None):
        if hasattr(positions, 'detach'): positions = positions.detach().cpu().numpy()
        if hasattr(targets, 'detach'): targets = targets.detach().cpu().numpy()
        positions = np.asarray(positions)
        targets = np.asarray(targets)
        if positions.shape[-1] != targets.shape[-1]+1:
            raise ValueError("Positions must have one more column than targets (returns), i.e., for cash")
        return gen_pnl(positions,targets,txn_cost,prev_position=prev_position)  

    def fetch_intraday_raw_data(self,start_hour=None,start_minute=None,end_hour=None,end_minute=None,date=None,features='returns',delta=50):
        if date is None:
            date=datetime.datetime.today().strftime('%Y-%m-%d')
        if start_hour is None or start_minute is None:
            now = datetime.datetime.now() - datetime.timedelta(minutes=delta)
            start_hour, start_minute = now.hour, now.minute
        dR=anvil.server.call('get_intraday_raw_data',start_hour=start_hour,start_minute=start_minute,date=date,features=features)
        # dR=get_intraday_raw_data(start_hour=start_hour,start_minute=start_minute,date=date,features=features)
        df = pd.DataFrame.from_dict(dR, orient='tight')
        df.drop(columns=['timestamp'], inplace=True)
        return df   


# In[ ]:


if __name__ == "__main__":
    client=Numin2API()
    positions = np.array([[1,1,0,-1,-1]*10,[1,1,0,-1,-1]*10]).astype(np.float32)
    # targets = torch.tensor([[1,1,0,-1,-.1]*10,[.1,1,0,-1,-.1]*10])
    # print(positions,targets)
    print(client.backtest_positions(positions,positions))


# In[ ]:




