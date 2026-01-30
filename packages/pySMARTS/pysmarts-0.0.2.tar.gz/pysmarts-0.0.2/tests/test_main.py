#!/usr/bin/env python
# coding: utf-8

"""
Created on Jan 21, 2026

@author: cdeline

Using pytest to create unit tests for pySMARTS.

to run unit tests, run pytest from the command line in the pySMARTS directory
to run coverage tests, run py.test --cov-report term-missing --cov=pySMARTS


"""

#from bifacial_radiance import RadianceObj, SceneObj, AnalysisObj
import pySMARTS

#import pytest
import os
import pandas as pd
import numpy as np

# try navigating to tests directory so tests run from here.
try:
    os.chdir('tests')
except:
    pass

TESTDIR = os.path.dirname(__file__)  # this folder

def test_import_pySMARTS():
    """ Test that pySMARTS can be imported """
    assert pySMARTS.__version__ is not None

def test_SpectraZenAzm():
    """ Test that SMARTSSpectraZenAzm runs without error """
    zen = 30
    azm = 180
    material = 'LiteSoil'
    min_wavelength = 300
    max_wavelength = 4000
    smarts_res = pySMARTS.SMARTSSpectraZenAzm(IOUT='2 3 4', ZENITH=str(zen), AZIM=str(azm),
                                     material=material,
                                     min_wvl=str(min_wavelength),
                                     max_wvl=str(max_wavelength))
    assert len(smarts_res) == 1962