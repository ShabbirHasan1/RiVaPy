import numpy as np
from rivapy import enums
from typing import List, Union, Tuple
from rivapy.marketdata.curves import *

import pyvacon.finance.marketdata as _mkt_data
import pyvacon.finance.utils as _utils
import pyvacon.finance.pricing as _pricing

InflationIndexForwardCurve = _mkt_data.InflationIndexForwardCurve
SurvivalCurve = _mkt_data.SurvivalCurve
DatedCurve = _mkt_data.DatedCurve
# DividendTable = _mkt_data.DividendTable

class DividendTable:
    def __init__(self, id: str,
                refdate: datetime, 
                ex_dates: List[datetime],
                pay_dates: List[datetime],
                div_yield: List[float],
                div_cash: List[float],
                tax_factors: List[float]):
        """[summary]

        Args:
            id (str): [description]
            refdate (datetime): [description]
            ex_dates (List[datetime]): [description]
            pay_dates (List[datetime]): [description]
            div_yield (List[float]): [description]
            div_cash (List[float]): [description]
            tax_factors (List[float]): [description]

        Yields:
            [type]: [description]
        """
        self.id = id
        self.refdate = refdate
        self.ex_dates = ex_dates
        self.pay_dates = pay_dates
        self.div_yield = div_yield
        self.div_cash = div_cash
        self.tax_factors = tax_factors
        self._pyvacon_obj = None

    def _get_pyvacon_obj(self):
        if self._pyvacon_obj is None:
            self._pyvacon_obj = _mkt_data.DividendTable(self.id, self.refdate, self.ex_dates, self.div_yield, self.div_cash, self.tax_factors, self.pay_dates)
        return self._pyvacon_obj
    
class VolatilityParametrizationFlat:
    def __init__(self,vol: float):
        """Flat volatility parametrization

        Args:
            vol (float): Constant volatility.
        """
        self.vol = vol
        self._pyvacon_obj = None
        
    def _get_pyvacon_obj(self):
        if self._pyvacon_obj is None:
            self._pyvacon_obj = _mkt_data.VolatilityParametrizationFlat(self.vol)  
        return self._pyvacon_obj
    
class VolatilityParametrizationTerm:
    def __init__(self, expiries: List[float], fwd_atm_vols: List[float]):
        """Term volatility parametrization

        Args:
            expiries (List[float]): List of expiration dates.
            fwd_atm_vols (List[float]): List of at-the-money volatilities.
        """
        self.expiries = expiries
        self.fwd_atm_vols = fwd_atm_vols
        self._pyvacon_obj = None
        
    def _get_pyvacon_obj(self):
        if self._pyvacon_obj is None:
            self._pyvacon_obj = _mkt_data.VolatilityParametrizationTerm(self.expiries, self.fwd_atm_vols)  
        return self._pyvacon_obj

class   VolatilityParametrizationSVI:
    def __init__(self, expiries: List[float], svi_params: List[Tuple]):
        """Raw SVI parametrization (definition 3.1 in  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2033323)

            ..math:
                w(k) = a + b(\rho (k-m) + \sqrt{(k-m)^2+\sigma^2 })
        Args:
            expiries (List[float]): List of expiries (sorted from nearest to farest)
            svi_params (List): List of SVI parameters (one Tuple for each expiry). Tuple in the order (a, b, rho, m, sigma)

        """
        self.expiries = np.array(expiries)
        self._x = self._get_x(svi_params)

    def get_params_at_expiry(self, expiry: int)->np.array:
        return self._x[5*expiry:5*(expiry+1)]

    def calc_implied_vol(self, ttm, strike):
        i = np.searchsorted(self.expiries, ttm)
        if i == 0 or i == self.expiries.shape[0]:
            if i == self.expiries.shape[0]:
                i -= 1
            return np.sqrt(self._w(i,np.log(strike))/ttm)
        w0 = self._w(i-1,np.log(strike))
        w1 = self._w(i,np.log(strike))
        #linear n total variance
        delta_t = self.expiries[i]-self.expiries[i-1]
        w = ((self.expiries[i]-ttm)*w0 + (ttm-self.expiries[i-1])*w1)/delta_t
        return np.sqrt(w/ttm)

    def _w(self, expiry: int, k: float):
        p = self.get_params_at_expiry(expiry)
        return p[0] + p[1]*(p[2] * (k-p[3])+np.sqrt((k-p[3])**2+p[4]**2))

    def _get_x(self, svi_params)->np.array:
        x = np.empty(len(svi_params)*5)
        j=0
        for i in range(len(svi_params)):
            for k in range(5):
                x[j] = svi_params[i][k]
                j += 1
        return x
        
    def _set_param(self, x)->np.array:
        self._x = x

   

class VolatilityParametrizationSSVI:
    def __init__(self, expiries: List[float], fwd_atm_vols: List[float], rho: float, eta: float, gamma: float):
        """SSVI volatility parametrization
        https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2033323

        Args:
            expiries (List[float]): List of expiration dates.
            fwd_atm_vols (List[float]): List of at-the-money volatilities.
            rho (float): Responsible for the skewness of the volatility surface.
            eta (float): Responsible for the curvature.
            gamma (float): Responsible for the "rate of decay".

        """
        self.expiries = expiries
        self.fwd_atm_vols = fwd_atm_vols
        self.rho = rho
        self.eta = eta
        self.gamma = gamma
        self._pyvacon_obj = None

    def calc_implied_vol(self, ttm, strike):
        return self._get_pyvacon_obj().calcImpliedVol(ttm, strike)

    def _get_pyvacon_obj(self):
        if self._pyvacon_obj is None:
            self._pyvacon_obj = _mkt_data.VolatilityParametrizationSSVI(self.expiries, self.fwd_atm_vols, self.rho, self.eta, self.gamma)  
        return self._pyvacon_obj
    
class VolatilityParametrizationSABR:
    def __init__(self, expiries: List[float], sabr_params: List[Tuple]):
        
        self.expiries = np.array(expiries)
        self._x = self._get_x(sabr_params)
        
    def get_params_at_expiry(self, expiry: int)->np.array:
        return self._x[4*expiry:4*(expiry+1)]
    
    def calc_implied_vol(self, ttm, strike):
        i = np.searchsorted(self.expiries, ttm)
        if i == 0 or i == self.expiries.shape[0]:
            if i == self.expiries.shape[0]:
                i -= 1
                
            return self._s(i,ttm, strike)
        s0 = self._s(i-1,ttm,strike)
        s1 = self._s(i,ttm, strike)
        #linear n total variance
        delta_t = self.expiries[i]-self.expiries[i-1]
        s = ((self.expiries[i]-ttm)*s0 + (ttm-self.expiries[i-1])*s1)/delta_t
        return s
    
    def _s(self, i: int, ttm: float, strike: float):
        K = strike
        alpha = self.get_params_at_expiry(i)[0] 
        ny = self.get_params_at_expiry(i)[1]
        beta = self.get_params_at_expiry(i)[2]
        rho = self.get_params_at_expiry(i)[3]
        f = 1
        
        zeta = ny/alpha*(f*K)**((1-beta)/2)*np.log(f/K)
        chi_zeta = np.log((np.sqrt(1-2*rho*zeta+zeta**2)+zeta-rho)/(1-rho))
        
        if f == K:
            sigma = alpha*(1+((1-beta)**2/24*alpha**2/f**(2-2*beta)+1/4*rho*beta*ny*alpha/f**(1-beta)+(2-3*rho**2)/24*ny**2)*ttm)/f**(1-beta)

        else:
            sigma = alpha*(1+((1-beta)**2/24*alpha**2/(f*K)**(1-beta)+1/4*rho*beta*ny*alpha/(f*K)**((1-beta)/2)+(2-3*rho**2)/24*ny**2)*ttm)/(f*K)**((1-beta)/2)*(1+(1-beta)**2/24*np.log(f/K)**2+(1-beta)**4/1920*np.log(f/K)**4)*zeta/chi_zeta

        return sigma
        

    def _get_x(self, sabr_params)->np.array:
        x = np.empty(len(sabr_params)*4)
        j = 0
        for i in range(len(sabr_params)):
            for k in range(4):
                x[j] = sabr_params[i][k]
                j += 1
        return x
    
    def _set_param(self, x)->np.array:
        self._x = x
    
class VolatilityGridParametrization:
    def __init__(self, expiries: np.array, strikes: np.ndarray, vols: np.ndarray):
        """Grid parametrization
        This parametrization stores a set of strike-vol grids for a given list of expiries and computes a volatility by
        - search for the neighboring expiries
        - apply a splien interpolation in each expiry to get the respective volatility
        - apply a linear interpolation (in total variance)

        Args:
            expiries (np.array): An array of the expiries.
            strikes (np.ndarray): 
            vols (np.ndarray): Two dimensional array of volatilities where each row i contains the values for expiry i
        """
        self.expiries = expiries
        if len(strikes.shape)==1:
            strikes = [strikes]*expiries.shape[0]
        self.strikes = strikes
        self.vols = vols
        self._pyvacon_obj = None

    def calc_implied_vol(self, ttm, strike):
        return self._get_pyvacon_obj().calcImpliedVol(ttm, strike)

    def _get_pyvacon_obj(self):
        if self._pyvacon_obj is None:
            vol_params = []
            self._pyvacon_obj = _mkt_data.VolatilityParametrizationTimeSlice(self.expiries, self.strikes, self.vols)  
        return self._pyvacon_obj
    
class VolatilitySurface:
    @staticmethod
    def _create_param_pyvacon_obj(vol_param):
        if hasattr(vol_param, '_get_pyvacon_obj'):
            return vol_param._get_pyvacon_obj()
        if hasattr(vol_param, 'expiries'):
            expiries = vol_param.expiries
        else:
            expiries = np.linspace(0.0, 4.0, 13, endpoint=True)
        strikes = np.linspace(0.4, 1.6, num=100)
        vols = np.empty((expiries.size, strikes.size))
        for i in range(expiries.size):
            for j in range(strikes.size):
                vols[i,j] = vol_param.calc_implied_vol(expiries[i], strikes[j])
        return VolatilityGridParametrization(expiries, strikes, vols)._get_pyvacon_obj()

    def __init__(self, id: str, refdate: datetime, forward_curve, daycounter, vol_param):
        """Volatility surface

        Args:
            id (str): Identifier (name) of the volatility surface.
            refdate (datetime): Valuation date.
            forward_curve (rivapy.market_data.EquityForwardCurve): Forward curve.
            daycounter (enums.DayCounterType): [description]
            vol_param ([VolatilityParametrizationFlat,VolatilityParametrizationTerm,VolatilityParametrizationSSVI]): Volatility parametrization.
        """
        self.id = id
        self.refdate = refdate
        self.forward_curve = forward_curve
        self.daycounter = daycounter
        self.vol_param = vol_param
        self._pyvacon_obj = None  
           
    def _get_pyvacon_obj(self, fwd_curve=None):
        if self._pyvacon_obj is None:
            if fwd_curve is None:
                fwd_curve = self.forward_curve
            self._pyvacon_obj = _mkt_data.VolatilitySurface(self.id, self.refdate,
                fwd_curve._get_pyvacon_obj(),self.daycounter.name, 
                VolatilitySurface._create_param_pyvacon_obj(self.vol_param))
        return self._pyvacon_obj
    
    def calc_implied_vol(self,  expiry: datetime, strike: float, refdate: datetime = None, forward_curve=None)->float:
        """Calculate implied volatility

        Args:
            refdate (datetime): Valuation date.
            expiry (datetime): Expiration date.
            strike (float): Strike price.

        Raises:
            Exception: [description]

        Returns:
            float: Implied volatility.
        """
        # convert strike into x_strike 
        if refdate is None:
            refdate = self.forward_curve.refdate
        if forward_curve is None and self.forward_curve is None:
            raise Exception('Please specify a forward curve')
        vol = self._get_pyvacon_obj()
        if forward_curve is None:
            forward_curve = self.forward_curve
        elif self.forward_curve is not None:
            vol = _mkt_data.VolatilitySurface.createVolatilitySurfaceShiftedFwd(vol, forward_curve._get_pyvacon_obj())
        forward_curve_obj = forward_curve._get_pyvacon_obj() 
        x_strike = _utils.computeXStrike(strike, forward_curve_obj.value(refdate, expiry), forward_curve_obj.discountedFutureCashDivs(refdate, expiry))
        if x_strike < 0:
            raise Exception(f'The given strike value seems implausible compared to the discounted future cash dividends\
                ({forward_curve_obj.discountedFutureCashDivs(refdate, expiry)}).')
        return vol.calcImpliedVol(refdate, expiry, x_strike)
      
    @staticmethod        
    def set_stickyness(vol_stickyness: enums.VolatilityStickyness):
        if vol_stickyness is enums.VolatilityStickyness.StickyXStrike:
            _pricing.GlobalSettings.setVolatilitySurfaceFwdStickyness(_pricing.VolatilitySurfaceFwdStickyness.Type.StickyXStrike)
        elif vol_stickyness is enums.VolatilityStickyness.StickyStrike:
            _pricing.GlobalSettings.setVolatilitySurfaceFwdStickyness(vol_stickyness)
        elif vol_stickyness is enums.VolatilityStickyness.StickyFwdMoneyness:
            _pricing.GlobalSettings.setVolatilitySurfaceFwdStickyness(_pricing.VolatilitySurfaceFwdStickyness.Type.StickyFwdMoneyness)
        elif vol_stickyness is enums.VolatilityStickyness.NONE:
            _pricing.GlobalSettings.setVolatilitySurfaceFwdStickyness(_pricing.VolatilitySurfaceFwdStickyness.Type.NONE)
        else:
            raise Exception ('Error')

if __name__=='__main__':
    svi = VolatilityParametrizationSVI(expiries=np.array([1.0/365.0, 1.0]), svi_params=[
        (0.0001, 0.1, -0.5, 0.0, 0.0001),
        (0.2, 0.1, -0.5, 0.0, 0.4),
    ])
    expiry = 1.0/365.0
    x_strike = 1.0
    svi.calc_implied_vol(expiry, x_strike)