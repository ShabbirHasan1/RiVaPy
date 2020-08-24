
from pyvacon import PricingResults
from crumble.instruments import CDSSpecification
from datetime import datetime 
from dateutil import relative_delta


class CDSPricingData:
    def __init__(self, spec: CDSSpecification, val_date, discount_curve, survival_curve, recovery_curve=None):
        self.spec = spec
        self.val_date = val_date
        self.discount_curve = discount_curve
        self.survival_curve = survival_curve
        self.recovery_curve = recovery_curve
        self._pricer_type = 'ISDA'
        
    def _pv_protection_leg(self, valuation_date: datetime, integration_stepsize: relative_delta):

        prev_date = max(self.val_date, self.spec.protection_start)
        current_date = min(prev_date + relative_delta, self.spec.expiry)
        pv_protection = 0.0
        
        while current_date <= self.spec.expiry:
            default_prob = self.survival_curve.value(valuation_date, prev_date)-self.survival_curve.value(valuation_date, current_date)
            recovery = self.spec.recovery
            if recovery is None and self.recovery_curve is not None:
                recovery = self.recovery_curve.value(valuation_date, current_date) 
            pv_protection += self.discount_curve.value(valuation_date, current_date) * recovery * default_prob
            prev_date = current_date
            current_date += relative_delta
            
        if prev_date < self.spec.expiry and current_date > self.spec.expiry:
            default_prob = self.survival_curve.value(valuation_date, prev_date)-self.survival_curve.value(valuation_date, self.spec.expiry)
            recovery = self.spec.recovery
            if recovery is None and self.recovery_curve is not None:
                recovery = self.recovery_curve.value(valuation_date, self.spec.expiry) 
            pv_protection += self.discount_curve.value(valuation_date, self.spec.expiry) * recovery * default_prob
            
        return pv_protection
        
    def price(self):
        pv_protection = CDSPricingData._pv_protection_leg(self.val_date,)
        pr_results = PricingResults()
        pr_results.pv_protection = pv_protection
        return pr_results