import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests

class timelib(object):
    @staticmethod
    def nextday(date):
        if type(date) == str:
            nd = str((pd.to_datetime(date) + pd.Timedelta('1 days')).date())
        elif type(date) == pd.tslib.Timestamp:
            nd = date + pd.Timedelta('1 days')
        else:
            nd = np.NaN
        return nd
    
    def ts_list(start, end, step, influxdb = False):
        # input 2 time and return a list of intervals
        t_start = pd.to_datetime(start)
        t_end = pd.to_datetime(end)
        t_delta = pd.to_timedelta(step)
        num_steps = int((t_end - t_start) / t_delta)
        t_list = [t_start]

        for i in range(1,num_steps):
            t_list.append(t_list[i-1] + t_delta)

        if influxdb:
            return ['%sT%sZ' %(str(i)[:10], str(i)[11:]) for i in t_list]
        if influxdb == False:
            return t_list
        
    def tsrange_list(start, end, step, t_range, influxdb = False):
        # input 2 time and return a list of intervals range as list of lists
        t_start = pd.to_datetime(start)
        t_end = pd.to_datetime(end)
        t_delta = pd.to_timedelta(step)
        num_steps = int((t_end - t_start) / t_delta)
        t_list = [(t_start - pd.to_timedelta(t_range), t_start)]

        for i in range(1,num_steps):
            t_step = (t_list[i-1][1] + t_delta - pd.to_timedelta(t_range), t_list[i-1][1] + t_delta)
            t_list.append(t_step)
    
        if influxdb:
            return [('%sT%sZ' %(str(i[0])[:10], str(i[0])[11:]), '%sT%sZ' %(str(i[1])[:10], str(i[1])[11:])) for i in t_list]    
        else:         
            return t_list

    def last_halfpast():
        # return the timestamp of last half past in string, e.g. 4:30
        now = pd.to_datetime('now')
        if now.minute > 30:
            x = (now.minute - 30)*60 + now.second
        else:
            x = (now.minute + 30)*60 + now.second
        return pd.to_datetime('now') - pd.to_timedelta('%ds' %x)
        
    def last_hour_same_min(minutes):
        # return the timestamp of last half past in string, e.g. 4:30
        now = pd.to_datetime('now')
        if now.minute > minutes:
            x = (now.minute - minutes)*60 + now.second
        else:
            x = (now.minute + minutes)*60 + now.second
        return pd.to_datetime('now') - pd.to_timedelta('%ds' %x)
        
class calendar(object):
    # create a calendar using pandas
    def __init__(self, year):
        self.year = year
        days = (pd.to_datetime(str(self.year+1) + '-01-01') - pd.to_datetime(str(self.year) + '-01-01')).days
        self.CAL = pd.DataFrame({'Date': [pd.to_datetime(str(self.year) + '-01-01').date()+pd.to_timedelta('%ddays'%i) for i in range(days)]})
        self.CAL['Weekday'] = self.CAL.Date.apply(lambda x: x.weekday())
        wd_list = self.CAL.Weekday.tolist()
        self.CAL['Week_no'] = [(wd_list[:i].count(6)) for i in range(len(wd_list))]
        self.weekday_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    def show_weekday(self, wd):
        #wd is the string of weekday, e.g. 'Mon'
        wd_index = self.weekday_name.index(wd)
        return self.CAL[self.CAL.Weekday == wd_index][['Date', 'Week_no']]
    
class dst(object):
    # Scrap the day light saving data from https://www.timeanddate.com
    @staticmethod
    def dst_ny(year):
        # given year and return start and end date of daylight saving in NY
        df = pd.DataFrame({'start': [pd.to_datetime('%d-3-%d'%(year, i)) for i in range(8, 15)],
                           'end': [pd.to_datetime('%d-11-%d'%(year, i)) for i in range(1, 8)]})
        df['s_wd'] = df.start.dt.weekday
        df['e_wd'] = df.end.dt.weekday
        return [df[df.s_wd == 6].start.tolist()[0], df[df.e_wd == 6].end.tolist()[0]]

    def isdst(date):
        # given a date and determine it is within daylight saving or not
        Date = pd.to_datetime(date)
        ds_zone = dst.dst_ny(Date.year)
        if (Date >= ds_zone[0]) and (Date < ds_zone[1]):
            return True
        else:
            return False
        
    def cut_time(date):
        # Since FX market cut time is NY time 5pm, due to daylight saving it will affect the UTC time
        Date = pd.to_datetime(date)
        ds_zone = dst.dst_ny(Date.year)
        if (Date >= ds_zone[0]) and (Date < ds_zone[1]): # summer daylight saving
            return 'T21:00:00Z'
        else: # without daylight saving
            return 'T22:00:00Z'    
    
    def dst_date(yr, locations = ['United States', 'Australia', 'United Kingdom', 'Japan', 'Canada', 'New Zealand', 'Switzerland', 'Germany']):
        page = requests.get("https://www.timeanddate.com/time/dst/%d.html" %yr)
        soup = BeautifulSoup(page.content, 'html.parser')
        tablebody = soup.find("tbody")
        countries = tablebody.find_all("tr")
        dst = []
        for i in range(len(countries)):
            try:
                if countries[i].find("a").get_text() in locations:
                    if 'No DST' in countries[i].find_all("td")[1].get_text():
                        item = [countries[i].find("a").get_text(), np.NaN, np.NaN]
                    else:
                        start = str(pd.to_datetime('%s %d'%(countries[i].find_all("td")[1].get_text()[8:], yr)).date())
                        end = str(pd.to_datetime('%s %d'%(countries[i].find_all("td")[2].get_text()[8:], yr)).date())
                        item = [countries[i].find("a").get_text(), start, end]
                    dst.append(item)
            except:
                pass
        df = pd.DataFrame(dst, columns = ['Country', 'DST_start', 'DST_end'])
        return df