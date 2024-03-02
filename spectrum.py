# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 14:19:35 2024

@author: Jan
"""
import readingfids
import numpy as np

#CONSTANT
DEUTERIUM_EPSILON = 0.1535069

class Spectrum_1D:
    
    def __init__(self, procpar, headers, fid, spectrum=None):
        self._headers = headers
        self._fid = fid
        self._procpar = procpar
        self.info = dict()
        if not spectrum:
            self.spectrum = self.generate_power_mode_spectrum()
        else:
            self.spectrum = spectrum
        
    @classmethod
    def create_from_file(cls, file_content, fid_type):
        if fid_type == "agilent":
            headers, fid = readingfids.read_agilent_fid(file_content)
        else:
            raise NotImplementedError
        
        return cls(headers, fid)
    
    def generate_power_mode_spectrum(self):
        ft_rl = np.fft.fft(np.real(self._fid[0]))
        ft_im = np.fft.fft(np.imag(self._fid[0]))
        # simplified spectrum not suitable for anything, 
        # though good for display prototyping
        pow_spectr = [(i*i + j*j) for i, j in zip(
            np.real(ft_rl[:len(ft_rl)//2]), np.imag(ft_im[:len(ft_im)//2]))]
        return pow_spectr
    
    def generate_info(self):
        pass
    
    
    
if __name__ == "__main__":
    #example creation of Spectrum_1D instantion
    nmr_file_path = "./example_fids/agilent_example1H.fid/fid"
    with open(nmr_file_path, "rb") as file:
        file_content = file.read()
        
    widmo = Spectrum_1D.create_from_file(file_content, "agilent")