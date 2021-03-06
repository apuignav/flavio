import unittest
import numpy as np
from .bvgamma import *
from flavio.physics.bdecays.formfactors.b_v import bsz_parameters
from flavio.physics.eft import WilsonCoefficients
from flavio.physics.bdecays.wilsoncoefficients import wctot_dict
from flavio.parameters import default_parameters
import flavio


wc = WilsonCoefficients()
par = default_parameters#

class TestBVgamma(unittest.TestCase):
    def test_bksgamma(self):
        # just check if this works
        flavio.Observable.get_instance("ACP(B0->K*gamma)").prediction_central(par, wc)
        flavio.Observable.get_instance("S_K*gamma").prediction_central(par, wc)
        # numerical comparison to  David's old Mathematica code
        self.assertAlmostEqual(
            flavio.Observable.get_instance("BR(B0->K*gamma)").prediction_central(par, wc)*1e5/3.91526,
             1, places=1)
        self.assertAlmostEqual(
            flavio.Observable.get_instance("BR(B+->K*gamma)").prediction_central(par, wc)*1e5/4.11625,
             1, places=1)

    def test_bksgamma(self):
        # just check if this works
        flavio.Observable.get_instance("ACP(Bs->phigamma)").prediction_central(par, wc)
        flavio.Observable.get_instance("S_phigamma").prediction_central(par, wc)
        flavio.Observable.get_instance("BR(Bs->phigamma)").prediction_central(par, wc)
        flavio.Observable.get_instance("ADeltaGamma(Bs->phigamma)").prediction_central(par, wc)
