# -*- coding: utf-8 -*-
from datetime import datetime as _datetime
from rivapy.enums import SecuritizationLevel
from rivapy.enums import Currency
from rivapy import _pyvacon_available
if _pyvacon_available:
    import pyvacon.finance.specification as _spec
    
    ComboSpecification = _spec.ComboSpecification
    #Equity/FX
    PayoffStructure = _spec.PayoffStructure
    ExerciseSchedule = _spec.ExerciseSchedule
    BarrierDefinition = _spec.BarrierDefinition
    BarrierSchedule = _spec.BarrierSchedule
    BarrierPayoff = _spec.BarrierPayoff
    BarrierSpecification = _spec.BarrierSpecification
    # EuropeanVanillaSpecification = _spec.EuropeanVanillaSpecification
    AmericanVanillaSpecification = _spec.AmericanVanillaSpecification
    #RainbowUnderlyingSpec = _spec.RainbowUnderlyingSpec
    #RainbowBarrierSpec = _spec.RainbowBarrierSpec
    LocalVolMonteCarloSpecification = _spec.LocalVolMonteCarloSpecification
    RainbowSpecification = _spec.RainbowSpecification
    MultiMemoryExpressSpecification = _spec.MultiMemoryExpressSpecification
    MemoryExpressSpecification = _spec.MemoryExpressSpecification
    ExpressPlusSpecification = _spec.ExpressPlusSpecification
    AsianVanillaSpecification = _spec.AsianVanillaSpecification
    RiskControlStrategy = _spec.RiskControlStrategy
    AsianRiskControlSpecification = _spec.AsianRiskControlSpecification


    #Interest Rates
    IrSwapLegSpecification = _spec.IrSwapLegSpecification
    IrFixedLegSpecification = _spec.IrFixedLegSpecification
    IrFloatLegSpecification = _spec.IrFloatLegSpecification
    InterestRateSwapSpecification = _spec.InterestRateSwapSpecification
    InterestRateBasisSwapSpecification = _spec.InterestRateBasisSwapSpecification
    DepositSpecification = _spec.DepositSpecification
    InterestRateFutureSpecification = _spec.InterestRateFutureSpecification
        
    InflationLinkedBondSpecification = _spec.InflationLinkedBondSpecification
    CallableBondSpecification = _spec.CallableBondSpecification

    #GasStorageSpecification = _spec.GasStorageSpecification

    #ScheduleSpecification = _spec.ScheduleSpecification

    #SpecificationManager = _spec.SpecificationManager

    #Bonds/Credit
    CouponDescription = _spec.CouponDescription
    BondSpecification = _spec.BondSpecification
else:
    #empty placeholder...
    class BondSpecification:
        pass

class EuropeanVanillaSpecification:
    def __init__(self, 
                 id: str,
                 type: str,
                 expiry: _datetime,
                 strike: float,
                 issuer: str = '',
                 sec_lvl: str = SecuritizationLevel.COLLATERALIZED,
                 curr: str = Currency.EUR,
                 udl_id: str = '',
                 share_ratio: float = 1.0,
                #  holidays: str = '',
                 ex_settle: int = 0,
                 trade_settle: int = 0):
        
        """Constructor for european vanilla option

        Args:
            id (str): Identifier (name) of the european vanilla specification.
            type (str): Type of the european vanilla option ('PUT','CALL').
            expiry (_datetime): Expiration date.
            strike (float): Strike price.
            issuer (str, optional): Issuer Id. Only used if pricing data is manually defined. Defaults to ''.
            sec_lvl (str, optional): Securitization level. Can be selected from rivapy.enums.SecuritizationLevel. Defaults to SecuritizationLevel.COLLATERALIZED.
            curr (str, optional): Currency (ISO-4217 Code). Must not be set if pricing data is manually defined. Can be selected from rivapy.enums.Currency. Defaults to Currency.EUR.
            udl_id (str, optional): Underlying Id. Only used if pricing data is manually defined. Defaults to ''.
            share_ratio (float, optional): [description]. Defaults to 1.0.
            ex_settle (int, optional): . Defaults to 0.
            trade_settle (int, optional): [description]. Defaults to 0.
        """
        
        self.id = id
        self.issuer = issuer
        self.sec_lvl = sec_lvl
        self.curr =  curr
        self.udl_id = udl_id
        self.type = type
        self.expiry = expiry
        self.strike = strike
        self.share_ratio = share_ratio
        # self.holidays = holidays
        self.ex_settle = ex_settle
        self.trade_settle = trade_settle
        
        self._pyvacon_obj = None
        
    def _get_pyvacon_obj(self):
        if self._pyvacon_obj is None:
            self._pyvacon_obj = _spec.EuropeanVanillaSpecification(self.id, 
                                            self.issuer, 
                                            self.sec_lvl, 
                                            self.curr, 
                                            self.udl_id, 
                                            self.type,
                                            self.expiry,
                                            self.strike,
                                            self.share_ratio,
                                            '',
                                            self.ex_settle,
                                            self.trade_settle)
                                            
        return self._pyvacon_obj


def ZeroBondSpecification(obj_id: str, curr: str,  issue_date: _datetime, expiry: _datetime, notional: float = 100.0, 
                        issuer: str = 'dummy_issuer', sec_level: str='NONE')->BondSpecification:
    """[summary]

    Args:
        obj_id (str: [description]
        curr (str: [description]
        issue_date (_datetime: [description]
        expiry (_datetime: [description]
        notional (float, optional: [description]. Defaults to 100.0.
        issuer (str, optional: [description]. Defaults to 'dummy_issuer'.
        sec_level (str, optional: [description]. Defaults to 'NONE'.

    Returns:
        BondSpecification: [description]
    """
    return BondSpecification(obj_id, issuer, sec_level, curr, expiry, issue_date, notional, 'ACT365FIXED', [], [], '', [], [])



#ProjectToCorrelation = _analytics.ProjectToCorrelation
  