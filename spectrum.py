# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 14:19:35 2024

@author: Jan
"""

import numpy as np
import os
import scipy.signal as spsig
import scipy.stats as spstat

import readingfids
import processing







class Spectrum_1D:
    # class will contain only universal methods, if needed they may call format-specific
    # functions from readingfids
    # class instantion should be created via classmethod create_from_file(path, file_type)

    
    def __init__(self, fid, info, path):
        
        #--------------------------------------
        # private variables
        
        # _fid : np.array usually complex type - contains raw fid read from .fid file
        # _integral_rel_one : float - real value of integral that is set to be equal one as relative value
        # _signal_treshold : minimal y-value for signal to be considered non zero in integration etc
        # _complex_spectrum : np.array of complex values, full spectrum of both domains
        #--------------------------------------
        # public variables
        
        # info : dictionary - contains information about spectrum, its guaranteed keys are listed at the end of file
        # path : string - absolute path to folder from which spectrum was created by create_from_file
        # spectrum : np.array of real values - ready to draw absorption spectrum, essentialy np.real(self._complex_spectrum)
        # integral_list : list of lists : [begin, end, real_value, rel_value] all members are floats
        #     list of integrals generated by integrate(), their range as fraction of spectrum and real and relative values
        # phase_correction : list of 3 floats - values of phase correction: zero, first, pivot of first
        # peak_list : TO BE EXPLAINED! including format of members
        # auto_peak_list : list of peaks found by algorithmic means, format to be specified
        #--------------------------------------
        # methods
        
        #--------------------------------------
        # initialization
        
        self._fid = fid
        self.path = path
        self.info = info 
        
        self.zero_fill_to_next_power_of_two()

        self.generate_spectrum()
        
        
        self._integral_rel_one = None
        self.integral_list = []

        self.peak_list = []
        
        self.phase_correction = [0.0, 0.0, 0.0]
        self.correct_phase(self.opt_zero_order_phase_corr(0, 1, 0.001))
        
        # value to be decided - placeholder currently
        self._signal_treshold = np.average(self.spectrum)/2
        
        self.auto_peak_list = []
        
        self.calc_treshold()
        
        self.find_peaks()
        
        # print(max(self.spectrum))
        # print(self._signal_treshold)
        # print(len(self._fid))

    @classmethod
    def create_from_file(cls, path):
        #to be considered: open() exceptions 
        path = os.path.abspath(path)
        ftype = readingfids.fid_file_type(path)
        if ftype == "agilent":
            info, fid = readingfids.agilent_wrapper(path)
        elif ftype == "bruker":
            info, fid = readingfids.bruker_wrapper(path)
        else:
            raise NotImplementedError(f"not implemented file format: {ftype}")
        
        return cls(fid[0], info, path)
    
    def zero_fill_to_next_power_of_two(self):
        """
        Fills fid with 0 + 0j up to the length equal to power of two, 
        if length is already equal to one of powers of two does nothing

        Returns
        -------
        None.

        """
        self._fid = processing.zero_fill_to_power_of_two(self._fid)
    
    def zero_to_number(self, number):
        self._fid = processing.zero_fill_to_number(self._fid, number)
    
    def generate_power_mode_spectrum(self):

        ft_rl = np.fft.fft(np.real(self._fid))
        ft_im = np.fft.fft(np.imag(self._fid))
        pow_spectr = [(i*i + j*j) for i, j in zip(
            np.real(ft_rl[:len(ft_rl)//2]), np.imag(ft_im[:len(ft_im)//2]))]
        
        self.pow_spectrum = pow_spectr
    
    def generate_spectrum(self):
        # # # 
        ft = np.fft.fft(self._fid)
        left_half = ft[:len(ft)//2][::-1]
        rigth_half = ft[len(ft)//2:][::-1]
        spectrum = np.concatenate((left_half, rigth_half))
        
        self._complex_spectrum = spectrum
        self.spectrum = np.real(self._complex_spectrum)
    
    def reset_integrals(self):
        """
        function to reset all integrals - delete them all from self.integral_list,
        and set self._integral_rel_one = None. After its use state before integrating is restored

        Returns
        -------
        None.

        """
        self.integral_list = []
        self._integral_rel_one = None
        
    def set_relative_one(self, real_value, rel_value):
        """
        function to recalculate all rel_values in self.integral_list based on provided real_value and rel_value pair

        Parameters
        ----------
        real_value : numeric
            real value which should corespond to relative value specified as second param.
        rel_value : numeric
            

        Returns
        -------
        None.

        """
        self._integral_rel_one = real_value/rel_value
        for integral in self.integral_list:
            integral[3] = integral[2] / self._integral_rel_one
    
    def integrate(self, begin, end, vtype="fraction"):
        """
        Function to integrate, it appends self.integral_list, and may modify self._integral_rel_one
        as its side effects
        
        Parameters
        ----------
        begin : numeric value [ppm or fraction]
            Start of integral in ppm scale or as fraction of spectrum
        end : numeric value [ppm or fraction]
            End of integral in ppm scale or as fraction of spectrum
        Their order is irrelevant
        If vtype == "fraction" 0 is assumed to mean left edge of spectrum,
        and 1 right edge

        Returns
        -------
        list: [begin, end, real_value, relative value]
        
            begin, end: numeric
            same values as arguments though, if arguments are in ppm they are converted 
            to fraction 
            
            real_value: numeric
            value of integration of part of self.spectrum starting
            with begin and ending with end.
            
            relative_value: numeric
            if it is a first integration relative value is equal to one,
            and self.integral_one is set to its real_value
            If it is a next integral it is equal to real_value/self.integral_rel_one
            
        *******
         the same list is appended to self.integral_list
        """
        # to be added: checking input validity
        
        # translation of values in ppm or fraction to data points number
        
        if vtype == "ppm":
            if begin < end: 
                begin, end = end , begin
                
            begin = begin - self.info["plot_begin_ppm"]
            begin = begin/(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
            begin = 1 - begin
            
            end = end - self.info["plot_begin_ppm"]
            end = end/(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
            end = 1 - end
            
        elif vtype == "fraction":
            if begin > end:
                begin, end = end, begin
        else:
            raise ValueError
            
        begin_point = round(begin*len(self.spectrum))
        end_point = round(end*len(self.spectrum))
        
        # setting low values to zero, it allows broad integrals where there are no peaks
        # to be equal to zero
        peak_values = self.spectrum[begin_point:end_point]
        # peak_values[peak_values < self._signal_treshold] = 0
        
        # numerical integration - trapezoid rule, 
        # to be considered simpsons rule or simple summation
        real_value = np.trapz(peak_values, dx=0.001)
        
        if not self._integral_rel_one:
            relative_value = 1.0
            self._integral_rel_one = real_value
        else:
            if self._integral_rel_one is None:
                raise ValueError
            relative_value = real_value/self._integral_rel_one
        
        self.integral_list.append([begin, end, real_value, relative_value])
        return [begin, end, real_value, relative_value]
    
    def quick_peak(self, rang):
        # docstring would be a nice addition
        #just for working with gui, this picks the max in a selected range
        rang = [round(i*len(self.spectrum)) for i in rang]
        spect_sliced = self.spectrum[rang[0]:rang[1]]
        index = max(range(len(spect_sliced)), key=spect_sliced.__getitem__)
        index+=rang[0]
        x_value = index/len(self.spectrum)
        peak_ppm = self.info['plot_end_ppm'] - x_value*(self.info["plot_end_ppm"] - self.info['plot_begin_ppm'])
        self.peak_list.append([x_value, peak_ppm])
        print(self.peak_list)
    
    def x_coordinate(self, x_value, vtype, out_type):
        """
        Conversion of x coordinate between different units:
            "ppm" delta scale
            "fraction" fraction of spectrum: 0 - left edge, 1 - right edge
            "Hz" relative frequency of point
            "data_point" : number of data point from self.spectrum
            
        It should only be used for conversion of x coordinate of real point on spectrum
        not as a mean for general unit conversion
            
        Parameters
        ----------
        x_value : numeric
            DESCRIPTION.
        vtype : string
            scale of input.
        out_type : string
            desired output scale.

        Returns
        -------
        x_value : numeric
            x_coordinates in scale specified in out_type.

        """
        
        
        if vtype=="ppm":
            x_value = x_value - self.info["plot_begin_ppm"]
            x_value = x_value/(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
            x_value = 1 - x_value
        elif vtype=="fraction":
            pass
        elif vtype=="Hz":
            x_value = x_value - self.info["plot_begin"]
            x_value = x_value/(self.info["plot_end"] - self.info["plot_begin"])
        elif vtype=="data_point":
            x_value = x_value / len(self.spectrum)
        else:
            raise NotImplementedError
            
        if out_type=="ppm":
            x_value = x_value*(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
            x_value = x_value+self.info["plot_begin_ppm"]
        elif out_type=="fraction":
            pass
        elif out_type=="Hz":
            x_value = 1 - x_value
            x_value = x_value*(self.info["plot_end"] - self.info["plot_begin"])
            x_value = x_value + self.info["plot_begin"]
        elif out_type=="data_point":
            x_value = round(x_value*len(self.spectrum))
        
        return x_value
            
    def correct_phase(self, zero, first_a=None, first_b=None):
        self.phase_correction[0] += zero
        self._complex_spectrum = self._complex_spectrum*np.exp(zero*1j*np.pi)
        
        if first_a or first_b:
            raise NotImplementedError
        
        self.spectrum = np.real(self._complex_spectrum)
        
    def opt_zero_order_phase_corr(self, start, first_step, precision):
        # temporary solution, later proper algorithm will be implemented
        complex_spectrum = self._complex_spectrum.copy()
        
        def spectrum_sum():
            nonlocal complex_spectrum
            
            spectrum = np.real(complex_spectrum)
            score = 0
            
            for i in spectrum:
                if i > 0:
                    score += i
                else:
                    score += -i*i
            return score
            
        angle = start
        maximum = spectrum_sum()
        step = first_step
        improved = False
        #print(angle, maximum)
        while True:
            complex_spectrum = complex_spectrum*np.exp(step*1j*np.pi)
            current = spectrum_sum()
            angle += step
            #print(angle, current)
            if current > maximum:
                maximum = current
                improved = True
                # print("better")
                value, counts = np.unique(np.round(np.real(complex_spectrum)/1000, 0), return_counts=True)
                # print(len(counts))
                # print(spstat.entropy(counts, base=2))
            else:
                #print("not really")
                angle -= step
                complex_spectrum = complex_spectrum*np.exp(-step*1j*np.pi)
                step /= 10
            if abs(step) < precision:
                if not improved:
                    #print("reversing!")
                    step = -first_step
                    improved = True
                    continue
                #print("end")
                break
            
        return angle
     
    def calc_treshold(self, begin=0.0, end=0.05):
        if begin > end:
            begin, end = end, begin
            
        begin_point = round(begin*len(self.spectrum))
        end_point = round(end*len(self.spectrum))
        section = self.spectrum.copy()[begin_point:end_point]
        section[section < 0] = 0
        
        treshold = np.average(section)
        
        self._signal_treshold = treshold
        
    def find_peaks(self):
        # to be considered: minimum peak height and distance, low concentration spectra, solvent peaks
        elem, _ = spsig.find_peaks(self.spectrum, height=50*self._signal_treshold, 
                                   distance=round((1/self.info["spectral_width"])*len(self.spectrum)))
        
        self.auto_peak_list.extend(elem)
        
        elem = 1 - (elem / len(self.spectrum))
        elem = elem*(self.info["plot_end_ppm"] - self.info["plot_begin_ppm"])
        elem = elem+self.info["plot_begin_ppm"]
        # print(elem)

        
        
        
# self.info - guaranteed keys:
    # "solvent"        : string
    # "samplename"     : string
    # "nucleus"        : string - observed nucleus e.g.: H1, C13 etc.
    # "spectral_width" : float - [Hz] width of spectrum
    # "obs_nucl_freq"  : float - [MHz] Larmor frequency of observed nucleus
    # "plot_begin"     : float - [Hz] beginning of plot
    # "plot_end"       : float - [Hz] end of plot
    # "plot_ppm"       : float - [ppm] beginning of plot
    # "plot_ppm"       : float - [ppm] end of plot
    # "quadrature"     : bool: true - fid as complex numbers
    # "vendor"         : string - producer of spectrometer
    # "acquisition_time" : float - [s] time of acquisition (fid recording time for single scan)
        
if __name__ == "__main__":
    
    # widmo = Spectrum_1D.create_from_file("./example_fids/bruker/1")
    
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFontDatabase
    from interface import openNMR
    
    import warnings
    warnings.filterwarnings("error")
    
    spektra = ("./example_fids/agilent/agilent_example1H.fid",
    "./example_fids/agilent/agilent_example13C.fid",
    "./example_fids/agilent/agilent_example19F.fid",
    "./example_fids/agilent/agilent_example31P.fid",
    "./example_fids/bruker/1",
    "./example_fids/bruker/2",
    "./example_fids/bruker/3")
    
    app = QApplication(sys.argv)
    # app.setStyle('Fusion')
    QFontDatabase.addApplicationFont("styling/titillium.ttf")
    with open("styling/styles.css", "r") as f:
        style = f.read()
        app.setStyleSheet(style)
    # main app
    window = openNMR()
    window.show()
    for i in spektra:
        print(i)
        window.add_new_page(i)
    sys.exit(app.exec())
    