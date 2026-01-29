# PImMSread
Python package used to read data recorded using the Pixel Imaging Mass Spectrometry (PImMS) sensor.

This package supports reading of both the binary (.bin), and the Hierarchical Data Format version 5 (.h5) PImMS formats.

## Creating a PImMS file object
The following is used to initialise a PImMS file object
```
import pimmsread

# For .bin PImMS files
pimmsObject = pimmsread.pimms(filename)

# For .h5 PImMS files
pimmsObject = pimmsread.pimms_h5(filename)
```
Various functions are then available within the object to read the data from the file, which can be explored using the help function.
