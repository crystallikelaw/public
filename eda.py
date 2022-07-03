import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_palette("pastel")
sns.set_theme(style="ticks", rc={"axes.spines.right": False, "axes.spines.top": False})


def get_data(week_nums):
    url = "http://web.mta.info/developers/data/nyct/turnstile/turnstile_{}.txt"
    dfs = []
    for week_num in week_nums:
        file_url = url.format(week_num)
        dfs.append(pd.read_csv(file_url))
    temp = pd.concat(dfs).reset_index().drop(['index'], axis=1)
    return temp


class incident:
    def __init__(self, period: list, idate: str, stations: list = 0, lines: list = 0, daily: bool = 1):
        self._rawdata = get_data(period)
        self.incident_date = idate
        self.stations = stations  # stations affected
        self.data = pd.DataFrame()
        self.daily = daily
        self.lines = lines
        self.clean = -1  # boolean for successful cleaning
        if not self.lines and not self.stations:
            print('Warning: No line/station given')

    def cleaner(self):
        df = self._rawdata

        # column names
        df.columns = df.columns.str.lower()
        df.columns = df.columns.str.strip()

        # whitespace
        for col in df.select_dtypes(include='object').columns.tolist():
            df[col].str.strip()

        # entries/exits numeric?
        for num in ['entries', 'exits']:
            try:
                pd.to_numeric(df[num], errors='raise', downcast='integer')
            except ValueError:
                print('Non numeric {}!'.format(num))
                self.clean = 0
                pd.to_numeric(df[num], errors='coerce', downcast='integer')
        try:
            uniqueentry = ['c/a', 'unit', 'scp', 'station', 'date_time']
            uniqueturn = uniqueentry[:-1]

            # only relevant stations/lines
            if self.lines and self.stations:
                df_relevant = df[df.station.isin(self.stations) & df.linename.isin(self.lines)].copy()
            elif self.lines:
                df_relevant = df[df.linename.isin(self.lines)].copy()
            else:
                df_relevant = df[df.station.isin(self.stations)].copy()

            # too much
            if df_relevant.size == 0:
                print('restricted db empty!')
                return self.failedclean()

            if self.daily:  # combining daily entries, max(cumulative)
                df_final = df_relevant.groupby(uniqueturn + ['date'], as_index=False)[['entries', 'exits']].max()
                df_final['date_time'] = pd.to_datetime(df_final.date, format="%m/%d/%Y")
                df_final = df_final.drop(['date'], axis=1)
            else:
                df_final = df_relevant
                df_final['date_time'] = pd.to_datetime(df_final.date + df_final.time, format="%m/%d/%Y%H:%M:%S")
                df_final = df_final.drop(['date', 'time'], axis=1)

            # duplicate check
            if df_final[df_final.duplicated(subset=uniqueentry, keep=False)].size > 0:
                print('Duplicates detected; clean manually')
                return self.failedclean()

            # cumulative into differences; |a|
            df_final[['daily_entries', 'daily_exits']] =\
                np.abs(df_final.groupby(uniqueturn)[['entries', 'exits']].diff())
            pd.to_numeric(df_final.daily_entries, downcast='integer')
            pd.to_numeric(df_final.daily_exits, downcast='integer')

            # v.large entry
            for col in ['daily_entries', 'daily_exits']:
                if df_final[df_final[col] > 10 ** 4].size > 0:
                    print('Some {} values > 10,000 removed; check'.format(col))
                    df_final = df_final[df_final[col] < 10 ** 4]
                    # self.clean = 0
            if not self.daily:
                df_final.rename(columns={'daily_entries': 'hourly_entries', 'daily_exits': 'hourly_exits'})

            # final oops
            if df_final.size == 0:
                print('Something went wrong, db empty')
                return self.failedclean()

            # newcols
            df_final['posti'] = df_final.date_time >= self.incident_date
            df_final['day_of_week'] = df_final.date_time.dt.day

            self.data = df_final.sort_values('date_time').reset_index().drop(['index'], axis=1)
            print('Cleaned!')
            self.clean = self.clean == -1
            return self.clean
        except:
            print('uncaught exception')
            # newcols
            df_final['posti'] = df_final.date_time >= self.incident_date
            df_final['day_of_week'] = df_final.date_time.dt.day
            return self.failedclean()

    def failedclean(self):
        print('\nCleaning failed\n')
        self.clean = 0
        df = self._rawdata
        df['date_time'] = pd.to_datetime(df.date + df.time, format="%m/%d/%Y%H:%M:%S")
        self.data = df.drop(['date', 'time'], axis=1)
        print(df.info())
        return 0

    def cleancheck(self):
        if self.data.size == 0:
            self.cleaner()
        if not self.clean:
            print('\nbad data!\n')
        return 0

    def before(self):
        self.cleancheck()
        return self.data[~self.data.posti]

    def after(self):
        self.cleancheck()
        return self.data[self.data.posti]

    def meanDiff(self):
        self.cleancheck()
        if self.daily:
            cols = ['daily_entries', 'daily_exits']
        else:
            cols = ['hourly_entries', 'hourly_exits']
        for col in cols:
            b = self.data[~self.data.posti][col].mean()
            a = self.data[self.data.posti][col].mean()
            print("mean {} changed from {:.2f} to {:.2f}, or by {:.2f} \
                  ({:.1f}%)".format(col, b, a, a - b, (a - b) * 100 / b))

    def scatter(self):
        self.cleancheck()
        if self.daily:
            cols = ['daily_entries', 'daily_exits']
        else:
            cols = ['hourly_entries', 'hourly_exits']

        g = sns.relplot(
            x=self.data.date_time,
            y=(self.data[cols[0]] + self.data[cols[1]]),
            hue=self.data.posti,
            facet_kws={'legend_out': True}
        )
        g._legend.set_title('{} Traffic'.format(cols[0][:-8].title()))
        g._legend.texts[0].set_text('Before Incident')
        g._legend.texts[1].set_text('After Incident')
        plt.xticks([self.data.date_time.min(), self.incident_date, self.data.date_time.max()])
        sns.move_legend(g, 'upper right', frameon=True)
        g.set_axis_labels('Time', 'Visits/Turnstile')
        plt.tight_layout()
        plt.show(g)

    def hist(self):
        self.cleancheck()
        if self.daily:
            cols = ['daily_entries', 'daily_exits']
        else:
            cols = ['hourly_entries', 'hourly_exits']

        histdf = self.data[['date_time', cols[0], cols[1]]].groupby('date_time', as_index=False).sum()
        histdf['freq'] = histdf[cols[0]] + histdf[cols[1]]
        histdf.drop(cols, axis=1)
        g = sns.histplot(
            x=histdf.date_time,
            weights=histdf.freq,
            data=histdf,
            discrete=True,
            hue=histdf.date_time >= self.incident_date,
        )
        g.legend(handles=g.legend_.legendHandles, labels=['Before Incident', 'After Incident'],
                 title='{} Traffic'.format(cols[0][:-8].title()), loc='upper left')
        plt.xticks([self.data.date_time.min(), self.incident_date, self.data.date_time.max()])
        g.set(xlabel='Time', ylabel='Total Visits')
        plt.tight_layout()
        plt.show(g)
