import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from typing import Union, Callable
from  rivapy.tools.datetime_grid import DateTimeGrid

def _logit(x):
    return np.log(x/(1-x))

def _inv_logit(x):
    return 1.0/(1+np.exp(-x))


class SolarProfile:
    def __init__(self, profile:Callable):
        self._profile = profile

    def get_profile(self, timegrid: DateTimeGrid):
        result = np.empty(timegrid.timegrid.shape[0])
        for i in range(result.shape[0]):
            result[i] = self._profile(timegrid.dates[i])
        return result

class SolarModel:
    def _eval_grid(f, timegrid):
        try:
            return f(timegrid)
        except:
            result = np.full(timegrid.shape, f)
            return result

    def __init__(self, daily_maximum_process,
                    profile,
                    mean_level,
                    name:str = 'Solar_Germany'):
        self.name = name
        self._daily_maximum_process = daily_maximum_process
        self._profile = profile
        self.mean_level = mean_level

  
    def simulate(self, timegrid: DateTimeGrid, start_value: float, rnd):
        # daily timegrid for daily maximum simulation
        tg_ = timegrid.get_daily_subgrid()
        ml = SolarModel._eval_grid(self.mean_level, tg_)
        start_value_ = _logit(start_value) - ml[0]
        daily_maximum = self._daily_maximum_process.simulate(tg_.timegrid, start_value_, rnd)
        profile = self._profile.get_profile(timegrid)
        result = np.empty((timegrid.shape[0], rnd.shape[0]))
        day = 0
        d = tg_.dates[0].date()
        for i in range(timegrid.timegrid.shape[0]):
            if d != timegrid.dates[i].date():
                day += 1
                d = timegrid.dates[i].date()
            result[i,:] = _inv_logit(daily_maximum[day,:] + ml[day])* profile[i] 
        return result

class WindPowerModel:
    def _eval_grid(f, timegrid):
        try:
            return f(timegrid)
        except:
            result = np.full(timegrid.shape, f)
            return result

    def __init__(self, 
                    speed_of_mean_reversion: Union[float, Callable], 
                    volatility: Union[float, Callable], 
                    mean_level: Union[float, Callable], 
                    name:str = 'Wind_Germany'):
        """Wind Power Model to model the efficiency of wind power production.

        Args:
            speed_of_mean_reversion (Union[float, Callable]): _description_
            volatility (Union[float, Callable]): _description_
            mean_level (Union[float, Callable]): _description_
        """
        self.speed_of_mean_reversion = speed_of_mean_reversion
        self.volatility = volatility
        self.mean_level = mean_level
        self.name = name
        self._timegrid = None

    def _set_timegrid(self, timegrid):
        self._timegrid = np.copy(timegrid)
        self._delta_t = self._timegrid[1:]-self._timegrid[:-1]
        self._sqrt_delta_t = np.sqrt(self._delta_t)

        self._speed_of_mean_reversion = WindPowerModel._eval_grid(self.speed_of_mean_reversion, timegrid)
        self._volatility = WindPowerModel._eval_grid(self.volatility, timegrid)
        self._mean_level = WindPowerModel._eval_grid(self.mean_level, timegrid)

    def simulate(self, timegrid, start_value, rnd):
        self._set_timegrid(timegrid.timegrid)
        start_value_ = _logit(start_value) - self._mean_level[0]
        return self._compute_efficiency(self._simulate_deseasonalized_logit(start_value_, rnd))

    #region private
    def _simulate_deseasonalized_logit(self, start_value, rnd):
        result = np.empty((self._timegrid.shape[0], rnd.shape[0]))
        result[0,:] = start_value
        for i in range(self._timegrid.shape[0]-1):
            result[i+1,:] = (1.0  - self._speed_of_mean_reversion[i]*self._delta_t[i])*result[i,:] + self._volatility[i]*self._sqrt_delta_t[i]*rnd[:,i]
        return result

    def _compute_efficiency(self, deseasonalized_logit_efficiency):
        return  _inv_logit(self._mean_level[:,np.newaxis] + deseasonalized_logit_efficiency)
  
class SupplyFunction:
    def __init__(self, floor:tuple, cap:tuple, peak:tuple, offpeak:tuple, peak_hours: set):
        self.floor = floor
        self.cap = cap
        self.peak = peak
        self.offpeak = offpeak
        self.peak_hours = peak_hours

    def compute(self, q, d:dt.datetime):
        def cutoff(x):
            return np.minimum(self.cap[1], np.maximum(self.floor[1], x))
        if q<=self.floor[0]:
            return self.floor[1]
        elif q>=self.cap[0]:
            return self.cap[1]
        if d.hour not in self.peak_hours:
            return cutoff(self.offpeak[0]+self.offpeak[1]/(q-self.floor[0])+self.offpeak[2]*q)
        return cutoff(self.peak[0]+self.peak[1]/(self.cap[0]-q))

    def plot(self, d:dt.datetime, res_demand_low = None, res_demand_high = None):
        if res_demand_low is None:
            res_demand_low = self.floor[0]
        if res_demand_high is None:
            res_demand_high = self.cap[0]
        q = np.linspace(res_demand_low, res_demand_high, 50)
        f = [self.compute(x, d) for x in q]
        plt.plot(q,f,'-', label=str(d))
        plt.xlabel('residual demand')
        plt.ylabel('price')

class LoadModel:
    def __init__(self,deviation_process, load_profile):
        self.load_profile = load_profile
        self.deviation_process = deviation_process

    def simulate(self, timegrid: DateTimeGrid, start_value: float, rnd:np.ndarray):
        result = np.empty((timegrid.shape[0], rnd.shape[0]))
        result[0,:] = start_value
        deviation = self.deviation_process.simulate(timegrid.timegrid, start_value, rnd)
        return self.load_profile.get_profile(timegrid)[:, np.newaxis] + deviation
        
class ResidualDemandModel:
    def __init__(self, wind_model, capacity_wind, 
                    solar_model, capacity_solar,  
                    load_model, supply_curve):
        self.wind_model = wind_model
        self.capacity_wind = capacity_wind
        self.solar_model = solar_model
        self.capacity_solar = capacity_solar
        self.load_model = load_model
        self.supply_curve = supply_curve

    def simulate(self, timegrid: DateTimeGrid, 
                    start_value_wind: float, 
                    start_value_solar: float, 
                    start_value_load: float,
                    n_sims: int,
                    rnd_wind: np.ndarray=None,
                    rnd_solar: np.ndarray=None,
                    rnd_load: float=None,
                    rnd_state = None):
        np.random.seed(rnd_state)
        if rnd_wind is None:
            rnd_wind = np.random.normal(size=(n_sims, timegrid.shape[0]-1))
        if rnd_solar is None:
            rnd_solar = np.random.normal(size=(n_sims, timegrid.get_daily_subgrid().shape[0]-1))
        if rnd_load is None:
            rnd_load = np.random.normal(size=(n_sims, timegrid.shape[0]-1))
        lm = self.load_model.simulate(timegrid, start_value_load, rnd_load)
        sm = self.capacity_solar*self.solar_model.simulate(timegrid, start_value_solar, rnd_solar)
        wm = self.capacity_wind*self.wind_model.simulate(timegrid, start_value_wind, rnd_wind)
        residual_demand = lm - sm - wm
        power_price = np.zeros(shape=( timegrid.shape[0], n_sims))
        for i in range(timegrid.shape[0]):
            for j in range(n_sims):
                power_price[i,j] =  self.supply_curve.compute(residual_demand[i,j],timegrid.dates[i] )
        result = {}
        result['load'] = lm
        result['solar'] = sm
        result['wind'] = wm
        result['price'] = power_price
        return result
