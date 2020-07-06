
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import pandas as pd
import pickle
import datetime

class CountryData():

    def __init__(self):
        self.infected_dataset_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
        self.recovered_dataset_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv"
        self.deaths_dataset_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"
        self.countries_dataset_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv"

        self.the_gamma = 1/30.

    def fetch(self):
        self.countries = pd.read_csv(self.countries_dataset_url)
        self.infected_original = pd.read_csv(self.infected_dataset_url)
        self.recovered_original = pd.read_csv(self.recovered_dataset_url)
        self.deaths_original = pd.read_csv(self.deaths_dataset_url)

        self.population = self.countries[self.countries['Province_State'].isnull()][['Country_Region','Population']].rename(columns={'Country_Region' : 'Country/Region'}).set_index('Country/Region')
        self.infected = self.infected_original.groupby('Country/Region').sum().reset_index().set_index('Country/Region').join(self.population,on='Country/Region')
        self.deaths = self.deaths_original.groupby('Country/Region').sum().reset_index().set_index('Country/Region').join(self.population,on='Country/Region')
        self.recovered = self.recovered_original.groupby('Country/Region').sum().reset_index().set_index('Country/Region').join(self.population,on='Country/Region')

    # The SIR model differential equations.
    def deriv(self, y, t, N, beta, gamma):
        S, I, R = y
        dSdt = -beta * S * I / N
        dIdt = beta * S * I / N - gamma * I
        dRdt = gamma * I
        return dSdt, dIdt, dRdt

    # Compute SIR model starting from given numbers of infected/removed ppl
    def sir_model(self, infected,removed,N,beta,gamma,ndays):
        t = np.linspace(0,ndays,ndays)
        y0 = N-infected-removed,infected,removed
        ret = odeint(self.deriv, y0, t, args=(N, beta, gamma))
        return ret.T # S,I,R

    def model(self,V,R,N,beta,gamma):
        S,I,R = self.sir_model(V[0],R[0],N,beta,gamma,len(V))
        dV = np.diff(V)
        dI = np.diff(I+R)
        return np.linalg.norm(dV-dI)

    # Подобрать параметры модели по векторам V и R
    def fit(self,V,R,N):
        # res = minimize(lambda x:model(V,R,N,x[0],x[1]),x0=[0.5,1/20],method='powell')
        # return res.x[0],res.x[1]
        res = minimize(lambda x:self.model(V,R,N,x,self.the_gamma),x0=0.5,method='powell')
        return res.x,self.the_gamma

    def make_frame(self,country_name,smooth_window=3):
        f = pd.DataFrame([self.infected.loc[country_name],self.recovered.loc[country_name],self.deaths.loc[country_name]]).T
        population = f.iloc[-1,0]
        f = f.iloc[2:-1].reset_index()
        f.columns = ['Date','Infected','Recovered','Deaths']
        f['Removed'] = f['Recovered']+f['Deaths']
        f["Date"] = pd.to_datetime(f["Date"],format="%m/%d/%y")
        for x in ['Infected','Recovered','Deaths','Removed']:
            f[x+"_Av"] = f[x].rolling(window=smooth_window).mean()
        return population, f

    def get_start_index(self,df):
        return df[df['Infected_Av']>1000].index[0]

    def compute_params(self, df,population, start_index, ndays=8):
        for i in range(start_index,len(df)-ndays):
            V = df['Infected_Av'][i:i+ndays].to_numpy()
            R = df['Removed_Av'][i:i+ndays].to_numpy()
            beta,gamma = self.fit(V,R,population)
            df.loc[i,'Beta'] = beta
            df.loc[i,'Gamma'] = gamma

    def analyze(self,country_name,truncate_frame=True):
        population, df = self.make_frame(country_name)
        n = self.get_start_index(df)
        self.compute_params(df,population,n)
        df['Rt'] = df['Beta'] / df['Gamma']
        return population, df.iloc[n:] if truncate_frame else df
        
    def get_country_data(self,countries=None,callback=None):
        countries = countries or \
                    [ 'Spain','Italy', 'France', 'Germany', 'Brazil', 'United Kingdom', 'US', 'Russia',
                      'Sweden', 'Norway', 'Finland', 'Denmark', 'China', 'Japan', 'Korea, South', 'India']

        country_data = {}
        for x in countries:
            if callback:
                callback(x)
            country_data[x] = self.analyze(x)

        return country_data