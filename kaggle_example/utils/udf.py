import pandas as pd

def algo_lists(field, size):
    series = field[:size].tolist()
    s = []
    for i in range(0, len(series)-1):
        if series[i] == 0 and series[i+1] != 1:
            j = 1
            sub = []
            while series[i+j] != 0:
                sub.append(series[i+j])
                j += 1
                if i+j == len(series):
                    break
            if len(sub) > 0:    
                s.append(sub)
                
    df_series = pd.DataFrame(s).transpose()
    col_list = df_series.columns.tolist()
    clist = []
    for i in col_list:
        clist.append('algo'+ str(i))
    df_series.columns = clist
    
    return df_series


def pos_format(df_position, df_md_rtbars):
    # check if the time match
#     if df_position.index.min() - df_md_rtbars.index.min() > pd.Timedelta('1h'):
#         print('Warning! over 1 hour different between start time in df_position (%s) and df_md_rtbars (%s)'%(str(df_position.index.min()), str(df_md_rtbars.index.min())))     
#     if df_position.index.max() - df_md_rtbars.index.max() > pd.Timedelta('1h'):
#         print('Warning! over 1 hour different between end time in df_position (%s) and df_md_rtbars (%s)'%(str(df_position.index.min()), str(df_md_rtbars.index.min())))
    df_position2 = df_position.resample('30s').copy()
    df_position2['MarketPrice'] = df_md_rtbars.last_MidClose
    for i in range(len(df_position2)): # fill in the NaN from the above data point
        
        if pd.isnull(df_position2.AverageCost[i]):
            df_position2.AverageCost[i] = df_position2.AverageCost[i-1]
        
        if pd.notnull(df_position2.MarketPrice[i]): # when market price data is available
            
            if pd.isnull(df_position2.Quantity[i]): # follow the above quantity data
                df_position2.Quantity[i] = df_position2.Quantity[i-1]
        
            if pd.isnull(df_position2.RealizedPnL[i]):
                df_position2.RealizedPnL[i] = df_position2.RealizedPnL[i-1]
                #df_position2.RealizedPnlUsd[i] = df_position2.RealizedPnlUsd[i-1]
            
        # Calculate based on the above data
        if pd.isnull(df_position2.MarketValue[i]):
            df_position2.MarketValue[i] = df_position2.Quantity[i]*df_position2.MarketPrice[i]
            
        if pd.isnull(df_position2.UnrealizedPnL[i]):    
            df_position2.UnrealizedPnL[i] = df_position2.Quantity[i]*(df_position2.MarketPrice[i]-df_position2.AverageCost[i])
            
        if df_position2.Quantity[i] == 0:
            df_position2.UnrealizedPnL[i] = 0
            #df_position2.UnrealizedPnlUsd[i] = 0
                   
    return df_position2
