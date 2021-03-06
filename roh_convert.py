#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Converts ROH files of the Avantes spectrometer using the 'kaitai' parser.

The amplitude curve is divided by the experimental spectrum of a calibration
lamp, and multiplied by the manufacturer-supplied spectrum thereof. This 
suppresses the spectrometer nonuniformity. You may wish to edit this file
if the calibration changes. Pass the '--raw' parameter to disable the 
calibration curve and the removal of outliers.

Finally, the original ROH and RCM files are moved into a new 'orig' directory 
and a human-readable data file is left. Pass the '--keeporig' parameter to 
prevent this. 

You can convert multiple files at once by specifying multiple names.

Related files:
    roh.py            -- auto-generated parser module
    avantes_roh60.ksy -- definiton of the parser module in kaitai format
    calibration_curve.dat -- calibration curve for the spectrometer used

If needed, you can download the kaitai project and re-generate the conversion 
module using (e.g. on Ubuntu): 

    kaitai-struct-compiler roh.ksy -t python

You can inspect the output file(s) e.g. with 

    https://github.com/FilipDominec/plotcommander

Written by Filip Dominec, 2017, dominecf@fzu.cz
Released under the MIT license
"""

        ## FIXME with some UV-data
secondorderampli = 178./12900 + 322./4348 - 300./3176  #- 217./6307     # subtraction of 2nd order artifacts; set to 0 to disable


## note: calibration with additional peak in UV did not help much
#np.loadtxt(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'calib-UV.dat'), unpack=True)[1]
#-(- 960*np.exp(-((x-328)/22)**2)  - 105*np.exp(-((x-360)/35)**2) + 120*np.exp(-((x-305)/15)**2))

def divide_spectrum():
    """ Measured for the calibration lamp """
    return np.loadtxt(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'calibration_curve.dat'), unpack=True)[1] 
def multiply_spectrum(xx):
    ## Provided by the calibration lamp manufacturer
    ## and added a fitted UV-component of a smooth UV emission peak
    return 1e3 * xx**(-5)*np.exp(41.7997795219285 - 4911.81898363455/xx)* \
            (0.654775110978796 + 856.950266207982/xx - 677547.170628456/(xx**2) + \
            205060324.151146/(xx**3)  - 22492160721.6625/(xx**4)) \

## Import common moduli
import numpy as np
import sys, os
from scipy.constants import c, hbar, pi

import roh

keeporig  = ('--keeporig' in   [ff for ff in sys.argv[1:] if ff[0:1] == '-'])
israw = ('--raw' in   [ff for ff in sys.argv[1:] if ff[0:1] == '-'])
keepoutliers = ('--keepoutliers' in   [ff for ff in sys.argv[1:] if ff[0:1] == '-'])
keepsec = ('--keepsec' in   [ff for ff in sys.argv[1:] if ff[0:1] == '-'])

for filepath in [ff for ff in sys.argv[1:] if ff[0:1] != '-']:
    my_roh = roh.Roh.from_file(filepath);
    print('processing: ',  filepath)

    ## Avaspec generates the x-axis exactly this weird way
    x0 = np.arange(int(my_roh.ipixfirst)+2, int(my_roh.ipixlast)+1)  
    x  = my_roh.wlintercept + x0*my_roh.wlx1 + x0**2 *my_roh.wlx2 + x0**3 *my_roh.wlx3 + x0**4 *my_roh.wlx4
    print('    integration_ms  = ', my_roh.integration_ms )
    print('    averaging       = ', my_roh.averaging      )
    print('    pixel_smoothing = ', my_roh.pixel_smoothing)

    spec = np.array(my_roh.spectrum)                          ## load the y-axis of the spectrum

    if not israw:
        kernel = [1]*(1+int(my_roh.pixel_smoothing)*2)     # averaging of neighboring pixels is needed also for the calibration curve
        kernel /= np.sum(kernel)                        # normalize the kernel
        print('    applying calibration curve, smoothed by kernel', kernel)
        smooth_divide = np.convolve(divide_spectrum(), kernel, mode='same')    # find the average value of neighbors
        spec /= smooth_divide                             ## divide by the grating+CCD response
        spec /= my_roh.integration_ms                             ## divide by the integration time
        spec *= multiply_spectrum(x)                   ## normalize to the spectral lamp XX included in calibration curve, 


    if not keepoutliers and not israw:
        kernel = [1,0,1] # averaging of neighbors #kernel = np.exp(-np.linspace(-2,2,5)**2) ## Gaussian
        kernel /= np.sum(kernel)                        # normalize
        smooth = np.convolve(spec, kernel, mode='same')    # find the average value of neighbors
        kernel2 = [1,0,0,0,1] # averaging of neighbors #kernel = np.exp(-np.linspace(-2,2,5)**2) ## Gaussian
        kernel2 /= np.sum(kernel2)                        # normalize
        smooth2 = np.convolve(spec, kernel2, mode='same')    # find the average value of neighbors
        rms_noise = np.average((spec[1:]-spec[:-1])**2)**.5   # estimate what the average noise is (rms derivative)
        where_excess =  (np.abs(spec-smooth) > rms_noise*1)    # find all points with difference from average more than 3sigma
        where_excess = where_excess[1:-1]                   # exclude the starting and ending point from outliers - they do not have 2 neighbors anyway
        print("    removing {} outliers".format(len(where_excess)))
        spec[where_excess] = smooth2[where_excess]
        #where_not_excess =  (np.abs(spec-smooth) < rms_noise*3)    # find all points with difference from average less than 3sigma
        #x, spec = x[where_not_excess], spec[where_not_excess]   # filter the data - WRONG, leads to uneven length of spectra

    if not keepsec:
        print('    subtracting second order with ratio ', secondorderampli) 
        spec -= np.interp(x, x*2, spec*secondorderampli)      ## subtract the second-order grating artifact
                                                        ##   see also https://gist.github.com/FilipDominec/2aa3af9f558483a25b04628e60bdf7e7


    try: 
        with open(filepath[:-4]+".RCM") as commentfile:
            comment = commentfile.read().strip()[3:]
            header = "\nuser_comment=%s" % comment      ## save the user-supplied comment, if possible
            print('    naming the file with comment = ', comment)
    except:
        header = "original_filename=%s" % filepath      ## if no RCM file found, include the file name in the header instead
        comment = ''
    header += "\nwavelength(nm) %s_intensity" % ("calibrated" if not israw else "uncalibrated")

    np.savetxt(filepath + '_converted_' + ('raw_' if israw else '') + comment + '.dat', 
            np.vstack([x, spec ]).T, header=header, fmt='%6f')

    ## Clean up the original files
    if not keeporig:
        try:
            dirname, filename = os.path.split(filepath)
            dest_dirname = os.path.join(dirname, 'orig')
            if not os.path.isdir(dest_dirname): os.makedirs(dest_dirname)
            os.rename(filepath, os.path.join(dest_dirname, filename))
            rcmfilename = filepath[:-3]+'RCM'
            if os.path.exists(rcmfilename): os.rename(rcmfilename, os.path.join(dest_dirname, rcmfilename))
            trtfilename = filepath[:-3]+'trt'
            if os.path.exists(trtfilename): os.rename(trtfilename, os.path.join(dest_dirname, trtfilename))
            if os.path.exists('dark0.dat'): os.rename('dark0.dat', os.path.join(dest_dirname, 'dark0.dat'))
        except:
            print('Warning: could not move the original file %s to the `orig` directory in %s' % (dirname, filename))

