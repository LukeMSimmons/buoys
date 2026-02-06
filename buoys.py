from datetime import datetime
import io

import plotly.express as px
import pandas as pd
import requests


default_station = {
    'Leucadia Nearshore': 46274}

additional_stations = {
    'Del Mar Nearshore': 46266,
    'SCRIPPS Nearshore': 46254}

stations = default_station | additional_stations | {
    None: list(default_station.values())[0]}


def get_df(id: str):

    r = requests.get(f'https://ndbc.noaa.gov/data/realtime2/{id}.txt')
    dtypes = dict(YY=str, MM=str, DD=str, hh=str, mm=str, WTMP=float)
    raw = r.text.strip('#').split('\n')
    data = '\n'.join(raw[2:])
    columns = raw[0].split()

    df = pd.read_csv(
        io.StringIO(data),
        usecols=dtypes.keys(),
        names=columns,
        dtype=dtypes,
        sep=r'\s+')

    return df


class Buoy:

    days = 10
    dark = True
    heat = True
    min_temp = 60
    max_temp = 75
    palette = 'jet'
    vertical = False
    test_attribute = 'thingy'

    def __init__(self, station: str | int = None):

        if isinstance(station, int):
            self.station_id = station
            self.station_name = str(station)
        else:
            self.station_id = stations[station]
            self.station_name = station or list(default_station.keys())[0]

        self.x = 'Datetime'
        self.wtmp = 'Temp'

        now = datetime.now()
        df = get_df(id=self.station_id)
        dst_start = datetime(now.year, 3, 8)
        dst_end = datetime(now.year, 11, 1)
        dst = dst_start < now < dst_end
        offset = 7 if dst else 8

        df[self.x] = df['YY'] + '-' + df['MM'] + '-' + df['DD']
        df[self.x] += ' ' + df['hh'] + ':' + df['mm'] + ':00'
        df[self.x] = pd.to_datetime(df[self.x])
        df[self.x] -= pd.Timedelta(hours=offset)
        df[self.x] = df[self.x].astype(str)
        
        df[self.wtmp] = df['WTMP'] * 9/5 + 32

        self.df = df
        self.config()

    def config(
            self,
            title_x=.45,
            days: int = None,
            dark: bool = None,
            heat: bool = None,
            palette: str = None,
            min_temp: int = None,
            max_temp: int = None,
            vertical: bool = None):

        self.days = days or self.days
        self.dark = dark or self.dark
        self.heat = heat or self.heat
        self.palette = palette or self.palette
        self.vertical = vertical or self.vertical
        self.min_temp = min_temp or self.min_temp
        self.max_temp = max_temp or self.max_temp
        self.template = f"plotly_{'dark' if self.dark else 'white'}"
        self.start = self.df.loc[2 * 24 * self.days, self.x]
        self.end = self.df.loc[0, self.x]
        self.title_x = title_x

    def water_temp(self):

        xy = dict(x=self.x, y=self.wtmp)
        yx = dict(x=self.wtmp, y=self.x)
        plot_args = yx if self.vertical else xy

        plot_args.update(dict(
            color=self.wtmp,
            color_continuous_scale=self.palette,
            range_color=[self.min_temp, self.max_temp]
            ) if self.heat else dict())

        title = f'Water Temp at {self.station_name} '
        title += f'- {round(self.df.at[0, self.wtmp], 1)}°F'
        fig = px.scatter(self.df, **plot_args)

        fig.update_layout(
            title=title,
            title_x=self.title_x,
            template=self.template,
            margin_t=50 if self.vertical else None,
            xaxis_side='top' if self.vertical else None,
            xaxis_title=None if self.vertical else self.x,
            yaxis_title=None if self.vertical else self.wtmp)

        axis_range = fig.update_yaxes if self.vertical else fig.update_xaxes
        axis_range(range=[self.start, self.end])

        fig.show()
