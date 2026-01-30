# fft_calculations

This is a small package with some fft utility functions.

## functions

### fft(wave, max_f=None, output='dBVrms')

The function fft calculates the fast fourier transform of 'wave' using scipy.fft.rfft with default arguments.

The argument 'max-f' determines the maximum frequency for which to return results. With this argument higher frequencies which are not of interest can be chopped of the results.

The argument 'output' determines the unit of the returned magnitudes.
- 'dBVrms' returns the magnitudes in dBVrms
- 'dBV' returns the magnitudes in dBV
- 'V' returns the magnitudes in V (same unit as the unit of wave[1])
This assumes the unit of wave[1] is V, can be substituted for any other unit.

**In the future support for windowing functions should be added.**

The function returns a tuple (xf,yf,fft_max_f,fft_f_res) in which:

- xf is an array of frequency bins [0..max_f] is max_f is not None, else [0..fft_max_f]
- yf is an equally sized array of magnitudes with th eunit determined by the argument 'output'
- fft_max_f is the maximum frequency if the fft (equal to the Nyquist frequency)
- fft_f_res is the frequency resolution in the resulting fft. This is the distance between frequency bins.


### thd(fft,f0,correct_peaks=False,min_level=None)

This function calculates the total harmonic distortion of a signal. The fft for the signal to be analyzed is in the argument 'fft', where fft is a tuple (t,v) in which t is an array of time, and v is an equally sized array of values.

The argument 'f0' is the fundamental frequency for which the harmonics are searched in the suuplied signal.

The argument 'correct_peaks' will decide if frequency bin correction is applied. Frequency bin correction means that after finding the bin for a harmonic, the bin with highest value will take over. This is only for bins directly neighbouring with the original bin, and without any inbetween bins with lower values.

The argument 'min_level' defines the lowest signal level for which harmonics will be included in the THD calculation. Any values lower than 'min_level' will be skipped.

The function returns a tuple (thd,bins) where

- thd is a float giving the total harmonic distortion (in %)
- bins is an array of indices into the frequency bins for the harmonics (regardless if they have been taken into account for the thd calculation or not)


### frequency_window(fft,centre,span)

Returns a slice from 'fft'. The argument 'fft' is a tuple (f,y) where f and y are equally sized arrays. The array f contains the centre frequency of the frequency bins of the fft. The array y contains the magnitude (any unit) of the respective frequency bins.

The returned slice is determined by the arguments 'centre' and 'span'. The argument 'centre' determines the centre of the frequency range to return, and 'span' is the entire span of the returned frequency range. The returned frequency range thus will be [centre-span/2:centre+span/2].

The returned slice will be in the same format as the input argument 'fft', namely a tuple (f',y'), where f' is the reduced frequency range, and y' the according magnitudes.


## installation

```python3 -m pip install fft_calculations```


## requirements

- numpy
- scipy

