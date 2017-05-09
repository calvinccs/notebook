
# Create a user define function to visualise algo trade in 3D plot

from influxdb import DataFrameClient
import pandas as pd
from utils.libs import *
from utils.udf import *
from utils.user import *

import warnings
warnings.filterwarnings('ignore')

import plotly.graph_objs as go
from datetime import date, timedelta

# Influxdb
host = 'influxdb.gsg.capital'
port = 8086
db_fxtrading = DataFrameClient(host, port, influx_id['user'], influx_id['pw'], ssl = True, database='fxtrading')
db_fxtrading_md = DataFrameClient(host, port, influx_id['user'], influx_id['pw'], ssl = True, database='fxtrading_md')
              
def plot_trades(d1, d2, cross = 'EURUSD' , null_ratio = 0.7, awp_ratio_outliner = 5):
    # d1 is the original date (e.g. org = date(2016,10,1))
    # d2 is the end of the period (e.g. org = date(2016,12,31))
    if d1 >= d2:
        print('The end of period must be bigger than the original date!')
    # cross is the pair, default is EURUSD
    # null_ratio is used to filter out trade records with too many nan, default value is 0.7
    # awp_ratio_outliner is used to remove trade records with extremely high awp_ratio, default is 5
    
    # Average Walkpath (db_fxtrading_md)
    df_md_avg_wp = pd.DataFrame()
    avg_period = date(2017,1,22)
    for d in range(7):
        start = avg_period + timedelta(days=d)
        end = start + timedelta(days=1)
        qline1 = "SELECT %s FROM %s WHERE Cross = '%s' AND time >= '%sT22:00:00Z' AND time < '%sT22:00:00Z' GROUP BY TIME(%s)" %('LAST(*)', 'md_avg_wp', cross, str(start), str(end), '30s')
        if len(db_fxtrading_md.query(qline1)) != 0:
            df_part = list(db_fxtrading_md.query(qline1).values())[0]
            df_part['dt_week'] = df_part.index - pd.to_datetime(str(avg_period)+ 'T22:00:00Z', utc=True)
            df_md_avg_wp = pd.concat([df_md_avg_wp, df_part], axis = 0)
      
    # Walkpath during trade (db_fxtrading_md)
    df_md_rtbars = pd.DataFrame()
    days = (d2 - d1).days # the length of period (e.g. days = 7)
    for d in range(days):
        start = d1 + timedelta(days=d)
        end = start + timedelta(days=1)
        sunday = start if pd.to_datetime(start).dayofweek == 6 else start - timedelta(days = (pd.to_datetime(start).dayofweek + 1)) # dt_week is based on the starting date of the week, which is sunday!
        qline2 = "SELECT %s FROM %s WHERE Cross = '%s' AND time >= '%sT22:00:00Z' AND time < '%sT22:00:00Z' GROUP BY TIME(%s)" %('LAST(*)', 'md_rtbars', cross, str(start), str(end), '30s')
        if len(db_fxtrading_md.query(qline2)) != 0:
            df_part = list(db_fxtrading_md.query(qline2).values())[0]
            df_part = df_part[['last_AskWalkedPath90m', 'last_BidWalkedPath90m']]
            df_part['dt_week'] = df_part.index - pd.to_datetime(str(sunday)+ 'T22:00:00Z', utc=True)
            df_md_rtbars = pd.concat([df_md_rtbars, df_part], axis = 0)
            
    if len(df_md_rtbars) != 0:
        df_wp = df_md_rtbars.reset_index()
        df_wp = df_wp.rename(columns={'index': 'time'})
        df_wp = pd.merge(df_wp, df_md_avg_wp, on='dt_week')
        df_wp['awp_ratio'] = df_wp.last_AskWalkedPath90m/df_wp.last_AvgAskWp90m
        df_wp['bwp_ratio'] = df_wp.last_BidWalkedPath90m/df_wp.last_AvgBidWp90m
    
    # Trade orders (db_fxtrading)
    
    df_position = []
    for d in range(days):
        start = d1 + timedelta(days=d)
        end = start + timedelta(days=1)
        sunday = start if pd.to_datetime(start).dayofweek == 6 else start - timedelta(days = (pd.to_datetime(start).dayofweek + 1)) 
        qline3 = "SELECT %s FROM %s WHERE Cross = '%s' AND time >= '%sT22:00:00Z' AND time < '%sT22:00:00Z'" %('*', 'positions', 'EURUSD', str(start), str(end))
        if (len(db_fxtrading.query(qline3)) != 0):
            df_q3 = list(db_fxtrading.query(qline3).values())[0]  
            if np.count_nonzero(df_q3.Quantity) != 0:
                if start < date(2017, 1, 10): # convert the fxtrading table to regular timestamp (30s)
                    df_position_part = df_q3
                    qline4 = "SELECT %s FROM %s WHERE Cross = '%s' AND time >= '%sT22:00:00Z' AND time < '%sT22:00:00Z' GROUP BY TIME(%s)" %('LAST(*)', 'md_rtbars', 'EURUSD', str(start), str(end), '30s')
                    if (len(db_fxtrading_md.query(qline4)) != 0):
                        df_q4 = list(db_fxtrading_md.query(qline4).values())[0]
                        df_md_rtbars_part = df_q4
                        df_part = pos_format(df_position_part, df_md_rtbars_part)
                        df_part = df_part[['Quantity', 'UnrealizedPnL']]
                        df_part['dt_week'] = df_part.index - pd.to_datetime(str(sunday)+ 'T22:00:00Z', utc=True)            
                        df_position.append(df_part)
                    else: 
                        print('Warning! Note that there is no md_rtbars data on %s and therefore cannot match with fxtrading data!' %str(start))
                else: 
                    df_part = df_q3
                    df_part = df_part[['Quantity', 'UnrealizedPnL']]
                    df_part['dt_week'] = df_part.index - pd.to_datetime(str(sunday)+ 'T22:00:00Z', utc=True)
                    df_position.append(df_part)

    # Extract each trade based on that they start with 0 Quantity and end with 0 Quantity (except the first one!)
    trades = []
    for p in range(len(df_position)):
        df = df_position[p]
        series = df.Quantity.tolist()
        for i in range(0, len(series)-1):
            if i == 0 and series[i] != 0: # find [x,x,x,x,x,....0]
                j = 1
                sub = [(df.index[i], df.UnrealizedPnL[i])]
                while series[i+j] != 0:
                    sub.append((df.index[i+j], df.UnrealizedPnL[i+j]))
                    #sub.append((df.index[i+j], series[i+j], df.AskWalkedPath90m[i+j], df.BidWalkedPath90m[i+j], df.MidWalkedPath90m[i+j]]))
                    j += 1
                    if i+j == len(series):
                        break
                if len(sub) > 0:
                    df_sub = pd.DataFrame(sub)
                    df_sub.columns = ['time', 'PnL']
                    df_sub['t_delta'] = df_sub.time - df_sub.time[0]
                    df_sub['t_int'] = df_sub.set_index('time').index.asi8
                    df_sub = df_sub.set_index('t_delta')
                    df_sub2 = df_sub.resample('30S').copy()
                    df_sub2['PnLi'] = df_sub2.PnL.interpolate() # Use pandas interpolation method to fill in the missing gap!
                    df_sub2['t_inti'] = df_sub2.t_int.interpolate()
                    df_sub2['awp_ratio'] = df_wp[(df_wp.time >= df_sub.time.min()) & (df_wp.time <= df_sub.time.max())].awp_ratio.tolist()
                    df_sub2 = df_sub2.drop('PnL', 1)
                    df_sub2 = df_sub2.drop('t_int', 1)
                    trades.append(df_sub2)
                
            if series[i] == 0 and series[i+1] != 1: # find [0,x,x,x,x,x,....0]
                j = 1
                sub = []
                while series[i+j] != 0:
                    sub.append((df.index[i+j], df.UnrealizedPnL[i+j]))
                    #sub.append((df.index[i+j], series[i+j], df.AskWalkedPath90m[i+j], df.BidWalkedPath90m[i+j], df.MidWalkedPath90m[i+j]]))
                    j += 1
                    if i+j == len(series):
                        break                        
                if len(sub) > 0:
                    df_sub = pd.DataFrame(sub)
                    df_sub.columns = ['time', 'PnL']
                    df_sub['t_delta'] = df_sub.time - df_sub.time[0]
                    df_sub['t_int'] = df_sub.set_index('time').index.asi8
                    df_sub = df_sub.set_index('t_delta')
                    df_sub2 = df_sub.resample('30S').copy()
                    df_sub2['PnLi'] = df_sub2.PnL.interpolate() # Use pandas interpolation method to fill in the missing gap!
                    df_sub2['t_inti'] = df_sub2.t_int.interpolate()
                    df_sub2['awp_ratio'] = df_wp[(df_wp.time >= df_sub.time.min()) & (df_wp.time <= df_sub.time.max())].awp_ratio.tolist()
                    df_sub2 = df_sub2.drop('PnL', 1)
                    df_sub2 = df_sub2.drop('t_int', 1)
                    trades.append(df_sub2)

    # Filter out trades with too much non number and outliner
    good_trades = []
    for i in range(len(trades)):
        if (trades[i].awp_ratio.isnull().sum()/len(trades[i]) < null_ratio) and (trades[i].PnLi.isnull().sum()/len(trades[i]) < null_ratio):
            if trades[i].awp_ratio.max() < awp_ratio_outliner:
                good_trades.append(trades[i])
                
    print('%d trades were fround from %s to %s' %(len(good_trades), str(d1), str(d2)))                
    # Plotting trade records in 3d lines
    data = []
    for i in range(len(good_trades)):
        r = 'rgb' + str(tuple([int(x) for x in np.random.rand(3)*255])) #random color generator
        trace = go.Scatter3d(
            name = str(pd.to_datetime(good_trades[i].t_inti[0])),
            x = good_trades[i].index.asi8/60000000000, y = np.array(good_trades[i].awp_ratio), z = np.array(good_trades[i].PnLi), 
            marker=dict(
                size=1, colorscale='Viridis'),
            line=dict(
                color=r,width=1)
            )
        data.append(trace)

    layout = dict(
        width=1000,
        height=1000,
        margin=dict(l=25, r=25, b=40, t=40),
        autosize=True,
        title='Algo(%s) 3D plot' %cross,
        scene = dict(
            xaxis = dict(
                title = 'time_delta (min)',
                backgroundcolor = 'rgb(230, 230, 230)', 
                showbackground=True),
            yaxis = dict(
                title = 'awp_ratio',            
                backgroundcolor = 'rgb(230, 230, 230)', 
                showbackground=True),
            zaxis = dict(
                title = 'PnL',
                backgroundcolor = 'rgb(230, 230, 230)', 
                showbackground=True),
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=0.1, y=-2, z=0.1)
             ),
           aspectratio = dict( x=1, y=1, z=0.7 ),
           aspectmode = 'manual'
       ),
    )
    fig = dict(data=data, layout=layout)
    iplot(fig)