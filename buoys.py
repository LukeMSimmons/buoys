import plotly.express as px
import pandas as pd
import requests
import io


vertical = False

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

    def __init__(self, station: str | int = None):

        if isinstance(station, int):
            self.station_id = station
            self.station_name = str(station)
        else:
            self.station_id = stations[station]
            self.station_name = station or list(default_station.keys())[0]

        self.x = 'Datetime'
        self.wtmp = 'Temp (F)'

        df = get_df(id=self.station_id)
        df[self.x] = df['YY'] + '-' + df['MM'] + '-' + df['DD']
        df[self.x] += ' ' + df['hh'] + ':' + df['mm'] + ':00'
        df[self.wtmp] = df['WTMP'] * 9/5 + 32

        self.df = df
        self.config()

    def config(
            self,
            title_x=.45,
            days: int = 10,
            dark: bool = True,
            heat: bool = True,
            min_temp: int = 60,
            max_temp: int = 75,
            palette: str = 'jet',
            vertical: bool = vertical):

        self.template = f"plotly_{'dark' if dark else 'white'}"
        self.start = self.df.loc[2 * 24 * days, self.x]
        self.end = self.df.loc[0, self.x]
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.vertical = vertical
        self.palette = palette
        self.title_x = title_x
        self.heat = heat

    def water_temp(self, heat=True):

        xy = dict(x=self.x, y=self.wtmp)
        yx = dict(x=self.wtmp, y=self.x)
        plot_args = yx if self.vertical else xy

        plot_args.update(dict(
            color=self.wtmp,
            color_continuous_scale=self.palette,
            range_color=[self.min_temp, self.max_temp]
            ) if heat else dict())

        title = f'Water Temp at {self.station_name}'
        fig = px.scatter(self.df, **plot_args)
        
        fig.update_layout(
            template=self.template,
            title=title, title_x=self.title_x)
        
        axis_range = fig.update_yaxes if self.vertical else fig.update_xaxes
        axis_range(range=[self.start, self.end])
        
        fig.show()
