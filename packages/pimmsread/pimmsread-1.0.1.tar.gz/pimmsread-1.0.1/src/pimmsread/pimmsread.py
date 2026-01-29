import numpy as np
import pimmsread.Subfunctions.jit_functions as jit_functions
import h5py

class pimms():
    """Class which can process binary PImMS files (to some extent at least!).

    Requires:
        filename - the path to a PImMS file (.bin)

    Optional:
        frames_to_skip - Defaults to zero. Must be an integer
        frames_to_proc - Defaults to all (-1). Must be an integer

        **Please note that there is no check to see if this combination actually
        processes any frames, so be careful when selecting values**

    Provides the following functions:
        read_full_data()
                - Adds full_image, no_frames, tof variables to class
                - Reads the entire PImMS file, stores an image for each timecode

        read_full_image_data()
                - Adds full_image and no_frames to the class
                - Reads the entire PImMS file, stores an image for each timecode

        read_image_data_subset(minimum_timecode,maximum_timecode)
                - Adds subset_image, time_codes and no_frames to the class
                - Same as read_full_image_data, but only reads between the provided
                    limits (inclusively)
                - time_codes variable is used to keep track of the timecodes for
                    each image in the subset_image array

        read_image_data_subset_single_image(minimum_timecode,maximum_timecode)
                - Adds subset_image and no_frames to the class
                - Same as read_full_image_data, but only reads between the provided
                    limits (inclusively)

        read_image_data_subset_delay_image(min_tof,max_tof, *, min_delay, max_delay, bin_spacing, no_bins)
                - Adds subset_image and no_frames to the class
                - Same as read_full_image_data, but only reads between the provided
                    limits (inclusively)

        read_ranges_image_data(timecode_ranges)
                - Adds image_data and no_frames variables to class
                - Requires pairs of timecodes
                - Image produced between the two timecodes (inclusive)

        read_ranges_image_data_subset_tof(timecode_ranges)
                - Adds image_data and no_frames variables to class
                - Requires pairs of timecodes
                - Image produced between the two timecodes (inclusive)
                - Similar to read_ranges_image_data(), but is more efficient when
                    reading multiple ranges and a subset of the TOF

        read_ranges_image_data_with_frame_intensities(bin_ranges)
                - Adds image_data, no_frames and intensity variables to class
                - Requires pairs of timecodes
                - Image produced between the two timecodes
                - For each pair of timecodes, the intensity is recorded for each
                    frame
                - Other than recording the intensity, this is identical to
                    read_ranges_image_data

        read_tof_only()
                - Adds tof variable to the class
                - Just reads the time-of-flight from the PImMS file

        read_pimms_file()
                - The function which reads the PImMS file
                - Called by the other functions. Can also be called externally
                - Acts as a generator for each PImMS frame

        read_pimms_file_multiproc(proc_no, total_proc)
                - The function which reads the PImMS file
                - Called by the other functions. Can also be called externally
                - Acts as a generator for each PImMS frame

        read_delay_file()
                - The function which reads the delay stage h5 file
                - Called by the other functions as required. Can also be called externally
                - Acts as a generator providing the delay for each acquisition cycle

        read_delay_file_multiproc(proc_no, total_proc)
                - The function which reads the delay stage h5 file
                - Called by the other functions as required. Can also be called externally
                - Acts as a generator providing the delay for each acquisition cycle

        get_min_max_delay(no_bins):
                - Reads the data in the delay stage file
                - Returns the min and max delay
                - Also returns the bin edges for histogram purposes, assuming the same number
                    of acquisition cycles fall in each bin

        read_tof_and_delay(min_tof, max_tof, *, min_delay, max_delay, bin_spacing, no_bins):
                - Reads the time of flight between min_tof and max_tof as a function of delay
                - bin_spacing can either be even, in which case there is an equal delay between
                    each bin, or equal_count, in which case the number of acquisition cycles per bin
                    is equal
    """
    def __init__(self, filename, frames_to_skip = 0, frames_to_proc = -1):
        self.filename = filename
        self.frames_to_skip = frames_to_skip
        self.frames_to_proc = frames_to_proc

    def read_full_data(self):
        """Read an entire PImMS image into an array, along with TOF

        Reads the entire PImMS image into a numpy array, which is stored in full_image, a 324 x 324 x 4096 array. Also produces the time-of-flight spectrum.

        Does not return anything, but adds the variables tof, full_data and no_frames
        to the class.
        """
        # Reinitialise generator
        data_gen = self.read_pimms_file()

        # Define a variable for the full data set
        self.full_image = np.zeros([324,324,4096]) #Zeros is one indexed
        # Define a variable for the TOF
        self.tof = np.zeros(4096)
        # Set the number of acquisition cycles to zero
        self.no_frames = 0

        #Read in the data, populate the image array
        try:
            i = 0
            while True:
                frame_data = next(data_gen)
                i += 1
                
                # Process the acquisition cycle (updates self.full_image and self.tof)
                jit_functions.read_full_data(frame_data, self.full_image, self.tof)

        except ValueError:
            self.no_frames = i
        except StopIteration:
            self.no_frames = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass


    def read_full_image_data(self):
        """Read an entire PImMS image into an array

        Reads the entire PImMS image into a numpy array, which is stored in full_image, a 324 x 324 x 4096 array. A TOF can be trivially extracted by summing the array for each time bin, although you can just use the read_full_data function for that.

        Does not return anything, but adds the variables full_data and no_frames
        to the class.
        """
        #Reinitialise generator
        data_gen = self.read_pimms_file()
        #Define a variable for the full data set
        self.full_image = np.zeros([324,324,4096]) #Zeros is one indexed
        self.no_frames = 0
        #Read in the data, populate the image array
        try:
            i = 0
            while True:
                frame_data = next(data_gen)
                i += 1

                # Process the acquisition cycle (updates self.full_image)
                jit_functions.read_full_image_data(frame_data, self.full_image)

        except ValueError:
            self.no_frames = i
        except StopIteration:
            self.no_frames = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass

    def read_image_data_subset(self,minimum_timecode=0,maximum_timecode=4095):
        """Read a subset of a PImMS image into an array

        Reads a subset of the PImMS image into a numpy array, which is stored in subset_image, a 324 x 324 x n array, where n is the maximum timecode - minimum timecode + 1 (provided as variables, which default to the same behaviour as read_full_image_data, +1 to include the maximum timecode as well). The TOF should be read using the read_full_data function, as there is little memory impact there.

        Does not return anything, but adds the variables subset_data, time_codes and no_frames
        to the class.

        Parameters required:
            minimum_timecode - an integer in the range 0 - 4095 corresponding to the minimum timecode
                               to include in the dataset
            maximum_timecode - an integer in the range 0 - 4095 corresponding to the maximum timecode
                               to include in the dataset

        Added to class:
            subset_image - a 324 x 324 x (maximum_timecode-minimum_timecode+1) array
                           containing PImMS data for each timecode from minimum_timecode
                           to maximum_timecode, inclusive. Use time_codes variable to
                           check which timecode each 324 x 324 array corresponds to
            time_codes   - a 1D array of the timecodes to which subset_data corresponds
            no_frames    - the number of frames in the PImMS file
        """
        # Validation of the provided timecodes
        for timecode in [minimum_timecode,maximum_timecode]:
            if not isinstance(timecode, int):
                print('Please provide integer bin edges.')
                return -1
            elif timecode < 0:
                print('Cannot have a negative bin edge (time codes start at 0).')
                return -1
            elif timecode > 4095:
                print('Bin edges must not exceed 4095 (4096 time codes, zero indexed).')
                return -1

        #Reinitialise generator
        data_gen = self.read_pimms_file()
        #Define a variable for the full data set. Note zeros is one indexed
        self.subset_image = np.zeros([324,324,maximum_timecode-minimum_timecode+1])
        self.no_frames = 0

        #Read in the data, populate the image array
        try:
            i = 0
            while True:
                frame_data = next(data_gen)
                i += 1

                # Process the acquisition cycle (updates self.subset_image)
                jit_functions.read_image_data_subset(frame_data, self.subset_image, minimum_timecode, maximum_timecode)

        except ValueError:
            self.no_frames = i
        except StopIteration:
            self.no_frames = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass

    def read_image_data_subset_single_image(self,minimum_timecode=0,maximum_timecode=4095, test=True):
        """Read a subset of a PImMS image into an array (2D rather thnn 3D)

        Reads a subset of the PImMS image into a numpy array, which is stored in subset_image, a 324 x 324 array.

        Does not return anything, but adds the variables subset_data, time_codes and no_frames
        to the class.

        Parameters required:
            minimum_timecode - an integer in the range 0 - 4095 corresponding to the minimum timecode
                               to include in the dataset
            maximum_timecode - an integer in the range 0 - 4095 corresponding to the maximum timecode
                               to include in the dataset

        Added to class:
            subset_image - a 324 x 324 array containing PImMS data summed for all timecodes
                           from minimum_timecode to maximum_timecode, inclusive.
            no_frames    - the number of frames in the PImMS file
        """
        # Validation of the provided timecodes
        for timecode in [minimum_timecode,maximum_timecode]:
            if not isinstance(timecode, int):
                print('Please provide integer bin edges.')
                return -1
            elif timecode < 0:
                print('Cannot have a negative bin edge (time codes start at 0).')
                return -1
            elif timecode > 4095:
                print('Bin edges must not exceed 4095 (4096 time codes, zero indexed).')
                return -1

        #Reinitialise generator
        data_gen = self.read_pimms_file()
        #Define a variable for the full data set. Note zeros is one indexed
        self.subset_image = np.zeros([324,324])
        self.no_frames = 0

        # Set the time_codes array
        time_codes = np.linspace(minimum_timecode, maximum_timecode, abs(maximum_timecode-minimum_timecode) + 1).astype('uint16')

        #Read in the data, populate the image array
        try:
            i = 0
            while True:
                frame_data = next(data_gen)
                i += 1

                # Process the acquisition cycle (updates self.subset_image)
                jit_functions.read_image_data_subset_single_image(frame_data, self.subset_image, minimum_timecode, maximum_timecode)

        except ValueError:
            self.no_frames = i
        except StopIteration:
            self.no_frames = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass

    def read_image_data_subset_delay_image(self, min_tof=0, max_tof=4095, *, min_delay=None, max_delay=None, bin_spacing='even', no_bins=10):
        """Read a subset of a PImMS image into an array (2D rather thnn 3D)

        Reads a subset of the PImMS image into a numpy array, which is stored in subset_image, a 324 x 324 array.

        Does not return anything, but adds the variables subset_data, time_codes and no_frames
        to the class.

        Parameters required:
            minimum_timecode - an integer in the range 0 - 4095 corresponding to the minimum timecode
                               to include in the dataset
            maximum_timecode - an integer in the range 0 - 4095 corresponding to the maximum timecode
                               to include in the dataset

        Added to class:
            subset_image - a 324 x 324 array containing PImMS data summed for all timecodes
                           from minimum_timecode to maximum_timecode, inclusive.
            no_frames    - the number of frames in the PImMS file
        """
        # Validation of the provided timecodes
        for timecode in [min_tof,max_tof]:
            if not isinstance(timecode, int):
                print('Please provide integer bin edges.')
                return -1
            elif timecode < 0:
                print('Cannot have a negative bin edge (time codes start at 0).')
                return -1
            elif timecode > 4095:
                print('Bin edges must not exceed 4095 (4096 time codes, zero indexed).')
                return -1

        if bin_spacing=='equal_count' or min_delay==None or max_delay==None:
            # Read the delay data from the h5 file and assign as appropriate
            data_min, data_max, bin_edges = self.get_min_max_delay(no_bins, min_delay, max_delay)
            if min_delay == None:
                self.min_delay = data_min
            else:
                self.min_delay = min_delay
            if max_delay == None:
                self.max_delay = data_max
            else:
                self.max_delay = max_delay

            self.bin_edges = bin_edges

        else:
            # Assign the provided delay data to the class
            self.min_delay = min_delay
            self.max_delay = max_delay

        if bin_spacing=='even':
            # Get the location of the bin edges
            self.bin_edges = np.linspace(self.min_delay, self.max_delay, num=no_bins+1, endpoint=True)

        #Reinitialise generators
        data_gen = self.read_pimms_file()
        delay_gen = self.read_delay_file()
        #Define a variable for the full data set. Note zeros is one indexed
        self.subset_image = np.zeros([no_bins,324,324])
        self.no_cycles = 0
        self.bin_count = np.zeros(no_bins, dtype='uint32')

        #Read in the data, populate the image array
        i = 0
        for delay in delay_gen:
            cycle_data = next(data_gen)
            i += 1

            # Process the acquisition cycle (updates self.subset_image)
            jit_functions.read_image_data_subset_delay_image(cycle_data, self.subset_image, delay, self.bin_edges, self.bin_count, no_bins, min_tof, max_tof)

        self.no_frames = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass

        # Normalise the ion images
        self.subset_image[self.bin_count>0] /= self.bin_count[self.bin_count>0, None, None]

    def read_ranges_image_data(self,bin_ranges):
        """Read PImMS image for specified time range(s) into array(s)

        Reads images recorded with a PImMS camera within the specified bin ranges
        into a numpy array, which is stored in image_data, an n x 324 x 324 array,
        where n is the number of bin ranges specified. Note that this function
        does not read the time-of-flight.

        Note that it will read from the lower bin limit to the upper bin limit,
        inclusively. So for a single bin, provide [1,1], for example.

        Requires a numpy array of bin ranges to be provided, with one dimension
        of two. For example, the below would be accepted:

        np.array([[1,2],    np.array([1,2])     np.array([[1],
                  [3,4]])                                 [2]])

        Where the array provided is 2 x 2, the first dimension would specify each
        pair, so the bin ranges from the first example above would be [1,2] and
        the second [3,4].

        Does not return anything, but adds the variables image_data and no_frames
        to the class.
        """
        #Make sure the bin range is formatted correctly. Otherwise returns.
        bin_ranges = self.sort_dimensions_of_bin_ranges(bin_ranges)

        #Get a ValueError trying to do a comparison with an array, so catch it.
        try:
            bin_ranges == -1
            #Just in case an error is not raised
            if bin_ranges == -1:
                return
        except ValueError:
            pass

        #Reinitialise generator
        data_gen = self.read_pimms_file()

        #Define an image for each bin range.
        self.image_data = np.zeros([bin_ranges.shape[0],324,324]) #Zeros is one indexed
        self.no_frames = 0

        try:
            i = 0
            while True:
                frame_data = next(data_gen)
                i += 1

                # Process the data from the acquisition cycle
                jit_functions.read_ranges_image_data(frame_data, self.image_data, bin_ranges)

        except ValueError:
            self.no_frames = i
        except StopIteration:
            self.no_frames = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass

    def read_ranges_image_data_subset_tof(self,bin_ranges):
        """Depreciated due to no difference in performance compared to read_ranges_image_data.
        
        Calls read_ranges_image_data, since the same parameters are required.
        """
        print('read_ranges_image_data_subset_tof is deprecieated.')
        print('Running read_ranges_image_data with the provided bin ranges.')
        self.read_ranges_image_data(bin_ranges)

    def read_ranges_image_data_with_frame_intensities(self,bin_ranges):
        """Read PImMS image for specified time range(s) into array(s), with intensity per frame

        Reads images recorded with a PImMS camera within the specified bin ranges
        into a numpy array, which is stored in image_data, an n x 324 x 324 array,
        where n is the number of bin ranges specified. Note that this function
        does not read the time-of-flight.

        Note that it will read from the lower bin limit to the upper bin limit,
        inclusively. So for a single bin, provide [1,1], for example.

        Requires a numpy array of bin ranges to be provided, with one dimension
        of two. For example, the below would be accepted:

        np.array([[1,2],    np.array([1,2])     np.array([[1],
                  [3,4]])                                 [2]])

        Where the array provided is 2 x 2, the first dimension would specify each
        pair, so the bin ranges from the first example above would be [1,2] and
        the second [3,4].

        For each timebin range, the total intensity is read each frame and is
        stored in the intensity variable, an n x no_frames array, where n is the
        number of bin ranges specified.

        Does not return anything, but adds the variables image_data and no_frames
        to the class.
        """
        #Make sure the bin range is formatted correctly. Otherwise returns.
        bin_ranges = self.sort_dimensions_of_bin_ranges(bin_ranges)

        #Get a ValueError trying to do a comparison with an array, so catch it.
        try:
            bin_ranges == -1
            #Just in case an error is not raised
            if bin_ranges == -1:
                return
        except ValueError:
            pass

        #Reinitialise generator
        data_gen = self.read_pimms_file()

        #Define an image for each bin range.
        self.image_data = np.zeros([bin_ranges.shape[0],324,324]) #Zeros is one indexed
        self.no_frames = 0

        #Define the intensity variable
        self.intensity = []

        try:
            i = 0
            while True:
                frame_data = next(data_gen)
                i += 1
                
                # Add another column to the intensity array
                self.intensity.append(np.zeros(bin_ranges.shape[0], dtype='int'))

                # Process the data from the acquisition cycle
                jit_functions.read_ranges_image_data_with_frame_intensities(frame_data, self.image_data, bin_ranges, self.intensity[i - 1])

        except ValueError:
            self.no_frames = i
        except StopIteration:
            self.no_frames = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass

        #Convert the intensity to a numpy array, and add it to the class
        #Note that as the list consists of np arrays for each frame, you need to
        #transpose to get the required dimensions for the variable
        self.intensity = np.array(self.intensity).transpose()

    def read_tof_only(self):
        """Read the time of flight from a PImMS image. Nothing else.

        Does not return anything, but adds the variables tof and no_frames
        to the class.
        """
        #Reinitialise generator
        data_gen = self.read_pimms_file()
        #Define a variable for the full data set
        self.tof = np.zeros([4096]) #Zeros is one indexed
        self.no_frames = 0
        #Read in the data, populate the image array
        try:
            i = 0
            while True:
                frame_data = next(data_gen)
                i += 1
                
                # Pass the data from the acquisition cycle to the function using jit 
                jit_functions.generateAcqCycleToF(frame_data, self.tof)

        except ValueError:
            self.no_frames = i
        except StopIteration:
            self.no_frames = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass

    def read_pimms_file(self):
        """Generator to read PImMS file

        The generator used to read in PImMS data. If you want to use this, set up a generator by
        using generator_name = pimms.read_pimms_file() and iterate through the file with a loop,
        calling next(generator_name) to get the data from the next acquisition cycle.
        """
        #Defines generator to read in PImMS data
        with open(self.filename, 'rb') as f:
            for i in range(self.frames_to_skip):
                # Read two int32 from the file and decode
                buffer = f.read(8)
                m, n = np.frombuffer(buffer, dtype='<i4')
                
                # Read the appropriate number of uint16 from the file and decode
                buffer = f.read(m * n * 2)
                np.frombuffer(buffer, dtype='<u2')

            if self.frames_to_proc == -1:
                while True:
                    # Read two int32 from the file and decode
                    buffer = f.read(8)
                    m, n = np.frombuffer(buffer, dtype='<i4')

                    # Read the appropriate number of uint16 from the file and decode
                    buffer = f.read(m * n * 2)
                    yield np.frombuffer(buffer, dtype='<u2').reshape((-1,3))

            else:
                for i in range(self.frames_to_proc):
                    # Read two int32 from the file and decode
                    buffer = f.read(8)
                    m, n = np.frombuffer(buffer, dtype='<i4')

                    # Read the appropriate number of uint16 from the file and decode
                    buffer = f.read(m * n * 2)
                    yield np.frombuffer(buffer, dtype='<u2').reshape((-1,3))

    def read_pimms_file_multiproc(self, proc_no, total_proc):
        """Generator to read PImMS file using multiple processors

        The generator used to read in PImMS data. If you want to use this, set up a generator by
        using generator_name = read_pimms_file() and iterate through the file with a loop,
        calling next(generator_name) to get the data from acquisition cycles separated by the total
        number of processors used.
        """
        # Subtract one from the total number of processors to get the number of cycles to skip
        cycles_to_skip = total_proc - 1

        #Defines generator to read in PImMS data
        with open(self.filename, 'rb') as f:
            for i in range(self.frames_to_skip):
                # Read two int32 from the file and decode
                buffer = f.read(8)
                m, n = np.frombuffer(buffer, dtype='<i4')
                
                # Read the appropriate number of uint16 from the file
                buffer = f.read(m * n * 2)

            for i in range(proc_no):
                # Skip files according to processor number
                # Read two int32 from the file and decode
                buffer = f.read(8)
                m, n = np.frombuffer(buffer, dtype='<i4')
                
                # Read the appropriate number of uint16 from the file
                buffer = f.read(m * n * 2)

            if self.frames_to_proc == -1:
                while True:
                    # Read two int32 from the file and decode
                    buffer = f.read(8)
                    m, n = np.frombuffer(buffer, dtype='<i4')

                    # Read the appropriate number of uint16 from the file and decode
                    buffer = f.read(m * n * 2)
                    yield np.frombuffer(buffer, dtype='<u2').reshape((-1,3))

                    for i in range(cycles_to_skip):
                        # Skip files according to total number of processors
                        # Read two int32 from the file and decode
                        buffer = f.read(8)
                        m, n = np.frombuffer(buffer, dtype='<i4')
                        
                        # Read the appropriate number of uint16 from the file
                        buffer = f.read(m * n * 2)

            else:
                for i in range(self.frames_to_proc):
                    # Read two int32 from the file and decode
                    buffer = f.read(8)
                    m, n = np.frombuffer(buffer, dtype='<i4')

                    # Read the appropriate number of uint16 from the file and decode
                    buffer = f.read(m * n * 2)
                    yield np.frombuffer(buffer, dtype='<u2').reshape((-1,3))

                    for i in range(cycles_to_skip):
                        # Skip files according to total number of processors
                        # Read two int32 from the file and decode
                        buffer = f.read(8)
                        m, n = np.frombuffer(buffer, dtype='<i4')
                        
                        # Read the appropriate number of uint16 from the file
                        buffer = f.read(m * n * 2)


    def sort_dimensions_of_bin_ranges(self, bin_ranges):
        """Checks validity of timecode ranges

        Makes sure that a provided bin range is actually valid. For the purposes intended,
        this should be a range of PImMS time bins for which ion images will be plotted.
        Could be used in conjunction with plotting a TOF, but would impact speed for
        little memory difference, so it is not advised.

        Parameters required:
            bin_ranges  - an array with one dimension of two, which contains a maximum
                          and minimum value. Should only contain integers that fall
                          between 0 and 4096 (inclusive).

        Returns either:
            -1          - if the input is invalid
            bin_ranges  - a numpy array with dimensions (n, 2) where n is the number
                          of bin ranges included in the array.
        """
        #Check the input is valid in various ways
        try:
            bin_ranges = np.array(bin_ranges)
        except:
            print('Cannot convert bin ranges to numpy array')
            return -1

        dimensions = bin_ranges.ndim

        if 2 not in bin_ranges.shape:
            print(str(bin_ranges.shape) + ' does not have a dimension of two.')
            return -1
        elif dimensions != 1 and dimensions != 2:
            print(str(dimensions) + ' is an invalid number of dimensions. Should be one or two.')
            return -1
        elif bin_ranges.dtype != 'int':
            print('Please provide integer bin edges.')
            return -1
        elif np.any(bin_ranges < 0):
            print('Cannot have a negative bin edge (time codes start at 0).')
            return -1
        elif np.any(bin_ranges > 4095):
            print('Bin edges must not exceed 4095 (4096 time codes, zero indexed).')
            return -1
        ###

        #Make the output bin ranges uniform
        if dimensions == 1:
            bin_ranges = np.array([bin_ranges])
        else:
            if bin_ranges.shape[1] != 2:
                bin_ranges = bin_ranges.transpose()

        #Make sure the limits are the correct way round (raises an error if not)
        if np.any(bin_ranges[:,0] > bin_ranges[:,1]) == True:
            print('Minimum bin must not exceed maximum bin.')
            return -1

        return bin_ranges

    def read_delay_file(self):
        """Generator to read delay stage position file

        The generator used to read in delay stage data. If you want to use this, set up a generator by
        using generator_name = pimms_h5.read_delay_file() and iterate through the file with a loop,
        calling next(generator_name) to get the data from the next acquisition cycle.
        """
        if self.filename[-3] == '.':
            filename = self.filename[:-3]
        else:
            filename = self.filename[:-4]

        if filename[-5:-1] == 'mini':
            # Make sure the position file can still be found if the file has been centroided
            filename = '_'.join(filename.split('_')[:-2])

        skipped_frames = 0
        processed_frames = 0
        # The data is stored as arrays of five second increments
        # This was done to reduce read/write operations on the hard drive
        # shot_total tracks how many shots have been seen in each loop
        with h5py.File(filename + '_position.h5', 'r') as hf:

            # Order the keys so the data is in the correct order
            dataset_index = np.sort(np.array([key for key in hf.keys()]).astype('int'))

            # Loop through each dataset index
            for idx in range(len(dataset_index)):
                # Read delay data
                delay_data = hf[str(dataset_index[idx])][()]

                # Deal with skipping frames
                if skipped_frames < self.frames_to_skip:
                    total_cycles = len(delay_data)

                    # Check whether the number of acquisition cycles processed in this dataset
                    # takes us over the number of frames to skip or not
                    if skipped_frames + total_cycles < self.frames_to_skip:
                        skipped_frames += total_cycles
                        continue

                    # If it does not, remove the appropriate number of delays
                    else:
                        delay_data = delay_data[self.frames_to_skip - skipped_frames:]

                # Deal with the remainder of the delay data
                for delay in delay_data:
                    if processed_frames == self.frames_to_proc:
                        break

                    # Yield the data
                    yield delay

                    processed_frames += 1

    def read_delay_file_multiproc(self, proc_no, total_proc):
        """Generator to read the delay stage position file using multiple processors

        The generator used to read in delay stage data. If you want to use this, set up a generator by
        using generator_name = read_delay_file_multiproc() and iterate through the file with a loop,
        calling next(generator_name) to get the data from acquisition cycles separated by the total
        number of processors used.
        """
        if self.filename[-3] == '.':
            filename = self.filename[:-3]
        else:
            filename = self.filename[:-4]

        if filename[-5:-1] == 'mini':
            # Make sure the position file can still be found if the file has been centroided
            filename = '_'.join(filename.split('_')[:-2])

        skipped_frames = 0
        processed_frames = 0
        # The data is stored as arrays of five second increments
        # This was done to reduce read/write operations on the hard drive
        # shot_total tracks how many shots have been seen in each loop
        with h5py.File(filename + '_position.h5', 'r') as hf:

            # Order the keys so the data is in the correct order
            dataset_index = np.sort(np.array([key for key in hf.keys()]).astype('int'))

            # Loop through each dataset index
            for idx in range(len(dataset_index)):
                # Read delay data
                delay_data = hf[str(dataset_index[idx])][()]

                # Deal with skipping frames
                if skipped_frames < self.frames_to_skip:
                    total_cycles = len(delay_data)

                    # Check whether the number of acquisition cycles processed in this dataset
                    # takes us over the number of frames to skip or not
                    if skipped_frames + total_cycles < self.frames_to_skip:
                        skipped_frames += total_cycles
                        continue

                    # If it does not, remove the appropriate number of delays
                    else:
                        delay_data = delay_data[self.frames_to_skip - skipped_frames:]

                # Deal with the remainder of the delay data
                for delay in delay_data:
                    if processed_frames == self.frames_to_proc:
                        break

                    if processed_frames % total_proc == proc_no:
                        # Yield the delay
                        yield delay

                    processed_frames += 1

    def get_min_max_delay(self, no_bins=10, min_delay=None, max_delay=None):
        # Get the sorted delay data
        delay_array = np.sort(np.array([delay for delay in self.read_delay_file()]))

        # Get the min and max if not already specified
        if min_delay == None:
            min_delay = delay_array[0]
        else:
            delay_array = delay_array[delay_array >= min_delay]

        if max_delay == None:
            max_delay = delay_array[-1]
        else:
            delay_array = delay_array[delay_array <= max_delay]

        # Work out where the bin edges would be if there are equal counts in each bin
        bin_edge_indexes = np.rint(np.linspace(0, len(delay_array) - 1, num=no_bins+1, endpoint=True))
        bin_edges = np.array([delay_array[int(idx)] for idx in bin_edge_indexes])

        bin_edges[0] = min_delay; bin_edges[-1] = max_delay
        
        return min_delay, max_delay, bin_edges

    def read_tof_and_delay(self, min_tof=1000, max_tof=3000, *, min_delay=None, max_delay=None, bin_spacing='even', no_bins=10):
        """Read the time of flight between min_tof and max_tof as a function of delay.

        Options:
            min_tof - Minimum ToF to plot
            max_tof - Maximum ToF to plot
            min_delay - Minimum delay to plot
            max_delay - Maximum delay to plot
            bin_spacing - 'even' or 'equal_count', discussed below
            no_bins - Number of bins to split data into

        Bin spacing is either:
            'even' : The bin edges are picked linearly between min_delay and max_delay
            'equal_count': The bin edges are picked to make the count per bin as even as possible

        Does not return anything, but adds the variables min_tof, max_tof, tof, no_frames, min_delay, max_delay and bin_edges
        to the class.
        """
        self.min_tof = min_tof
        self.max_tof = max_tof

        if bin_spacing=='equal_count' or min_delay==None or max_delay==None:
            # Read the delay data from the h5 file and assign as appropriate
            data_min, data_max, bin_edges = self.get_min_max_delay(no_bins, min_delay, max_delay)
            if min_delay == None:
                self.min_delay = data_min
            else:
                self.min_delay = min_delay
            if max_delay == None:
                self.max_delay = data_max
            else:
                self.max_delay = max_delay

            self.bin_edges = bin_edges

        else:
            # Assign the provided delay data to the class
            self.min_delay = min_delay
            self.max_delay = max_delay

        if bin_spacing=='even':
            # Get the location of the bin edges
            self.bin_edges = np.linspace(self.min_delay, self.max_delay, num=no_bins+1, endpoint=True)

        #Reinitialise generators
        data_gen = self.read_pimms_file()
        delay_gen = self.read_delay_file()
        #Define a variable for the full data set
        self.tof = np.zeros((no_bins,self.max_tof-self.min_tof + 1)) #Zeros is one indexed, hence the +1
        self.no_cycles = 0
        self.bin_count = np.zeros(no_bins, dtype='uint32')
        #Read in the data, populate the image array
        i = 0
        for delay in delay_gen:
            frame_data = next(data_gen)
            i += 1
            
            # Pass the data from the acquisition cycle to the function using jit
            jit_functions.generateAcqCycleDelayToF(frame_data, self.tof, delay, self.bin_edges, self.bin_count, no_bins, min_tof, max_tof)

        self.no_cycles = i

        try:
            del event; del frame_data
        #If there was no event, this catches the error
        except UnboundLocalError:
            pass

        # Normalise the ToF
        self.tof[self.bin_count>0] /= self.bin_count[self.bin_count>0, None]

class pimms_h5(pimms):
    """Class which can process h5 PImMS files (to some extent at least!).

    Requires:
        filename - the path to a PImMS file (.h5)

    Optional:
        frames_to_skip - Defaults to zero. Must be an integer
        frames_to_proc - Defaults to all (-1). Must be an integer

        **Please note that there is no check to see if this combination actually
        processes any frames, so be careful when selecting values**

    Provides the following functions:
        read_full_data()
                - Adds full_image, no_frames, tof variables to class
                - Reads the entire PImMS file, stores an image for each timecode

        read_full_image_data()
                - Adds full_image and no_frames to the class
                - Reads the entire PImMS file, stores an image for each timecode

        read_image_data_subset(minimum_timecode,maximum_timecode)
                - Adds subset_image, time_codes and no_frames to the class
                - Same as read_full_image_data, but only reads between the provided
                    limits (inclusively)
                - time_codes variable is used to keep track of the timecodes for
                    each image in the subset_image array

        read_image_data_subset_single_image(minimum_timecode,maximum_timecode)
                - Adds subset_image and no_frames to the class
                - Same as read_full_image_data, but only reads between the provided
                    limits (inclusively)

        read_image_data_subset_delay_image(min_tof,max_tof, *, min_delay, max_delay, bin_spacing, no_bins)
                - Adds subset_image and no_frames to the class
                - Same as read_full_image_data, but only reads between the provided
                    limits (inclusively)

        read_ranges_image_data(timecode_ranges)
                - Adds image_data and no_frames variables to class
                - Requires pairs of timecodes
                - Image produced between the two timecodes (inclusive)

        read_ranges_image_data_subset_tof(timecode_ranges)
                - Adds image_data and no_frames variables to class
                - Requires pairs of timecodes
                - Image produced between the two timecodes (inclusive)
                - Similar to read_ranges_image_data(), but is more efficient when
                    reading multiple ranges and a subset of the TOF

        read_ranges_image_data_with_frame_intensities(bin_ranges)
                - Adds image_data, no_frames and intensity variables to class
                - Requires pairs of timecodes
                - Image produced between the two timecodes
                - For each pair of timecodes, the intensity is recorded for each
                    frame
                - Other than recording the intensity, this is identical to
                    read_ranges_image_data

        read_tof_only()
                - Adds tof variable to the class
                - Just reads the time-of-flight from the PImMS file

        read_pimms_file()
                - The function which reads the PImMS file
                - Called by the other functions. Can also be called externally
                - Acts as a generator for each PImMS frame

        read_pimms_file_multiproc(proc_no, total_proc)
                - The function which reads the PImMS file
                - Called by the other functions. Can also be called externally
                - Acts as a generator for each PImMS frame

        read_delay_file()
                - The function which reads the delay stage h5 file
                - Called by the other functions as required. Can also be called externally
                - Acts as a generator providing the delay for each acquisition cycle

        read_delay_file_multiproc(proc_no, total_proc)
                - The function which reads the delay stage h5 file
                - Called by the other functions as required. Can also be called externally
                - Acts as a generator providing the delay for each acquisition cycle

        get_min_max_delay(no_bins):
                - Reads the data in the delay stage file
                - Returns the min and max delay
                - Also returns the bin edges for histogram purposes, assuming the same number
                    of acquisition cycles fall in each bin

        read_tof_and_delay(min_tof, max_tof, *, min_delay, max_delay, bin_spacing, no_bins):
                - Reads the time of flight between min_tof and max_tof as a function of delay
                - bin_spacing can either be even, in which case there is an equal delay between
                    each bin, or equal_count, in which case the number of acquisition cycles per bin
                    is equal
    """
    def __init__(self, filename, frames_to_skip = 0, frames_to_proc = -1):
        super().__init__(filename, frames_to_skip, frames_to_proc)

    def read_pimms_file(self):
        """Generator to read PImMS file

        The generator used to read in PImMS data. If you want to use this, set up a generator by
        using generator_name = pimms_h5.read_pimms_file() and iterate through the file with a loop,
        calling next(generator_name) to get the data from the next acquisition cycle.
        """
        skipped_frames = 0
        processed_frames = 0
        # The data is stored as arrays of five second increments
        # This was done to reduce read/write operations on the hard drive
        # shot_total tracks how many shots have been seen in each loop
        with h5py.File(self.filename, 'r') as hf:

            # Order the keys so the data is in the correct order
            dataset_index = np.sort(np.array([key for key in hf.keys()]).astype('int'))

            # Loop through each dataset index
            for idx in range(len(dataset_index)):

                # Data format is x, y, t, mem_reg. Cycles are separated by 0, 0, 0, 0
                shot_data = hf[str(dataset_index[idx])][()]

                # Check for lines containing just 0 (the ~ inverts the False returned to True).
                # Then finds the indices for these lines
                shot_indices = np.where(~shot_data.any(axis=1))[0]

                # Deal with skipping frames
                if skipped_frames < self.frames_to_skip:
                    total_cycles = len(shot_indices)

                    # Check whether the number of acquisition cycles processed in this dataset
                    # takes us over the number of frames to skip or not
                    if skipped_frames + total_cycles < self.frames_to_skip:
                        skipped_frames += total_cycles
                        continue

                    # If it does, remove the appropriate number of shot indices. Note that the
                    # original shot_indices array will act as if one cycle has been skipped
                    else:
                        for i in range(self.frames_to_skip - skipped_frames - 1):
                            shot_indices.pop(0)

                else:
                    # Add a -1 at the start so all acquisition cylces can be processed in a single loop
                    shot_indices = np.hstack((np.array(-1), shot_indices))

                # Remove information on the memory register
                shot_data = shot_data[:,:3]

                # Deal with the remainder of the dataset
                for i in range(len(shot_indices) - 1):
                    if processed_frames == self.frames_to_proc:
                        break

                    # Convert to PImMS format and yield the data
                    yield shot_data[shot_indices[i] + 1:shot_indices[i+1]]

                    processed_frames += 1

    def read_pimms_file_multiproc(self, proc_no, total_proc):
        """Generator to read PImMS file using multiple processors

        The generator used to read in PImMS data. If you want to use this, set up a generator by
        using generator_name = read_pimms_file_multiproc() and iterate through the file with a loop,
        calling next(generator_name) to get the data from acquisition cycles separated by the total
        number of processors used.
        """
        skipped_frames = 0
        processed_frames = 0
        # The data is stored as arrays of five second increments
        # This was done to reduce read/write operations on the hard drive
        # shot_total tracks how many shots have been seen in each loop
        with h5py.File(self.filename, 'r') as hf:

            # Order the keys so the data is in the correct order
            dataset_index = np.sort(np.array([key for key in hf.keys()]).astype('int'))

            # Loop through each dataset index
            for idx in range(len(dataset_index)):

                # Data format is x, y, t, mem_reg. Cycles are separated by 0, 0, 0, 0
                shot_data = hf[str(dataset_index[idx])][()]

                # Check for lines containing just 0 (the ~ inverts the False returned to True).
                # Then finds the indices for these lines
                shot_indices = np.where(~shot_data.any(axis=1))[0]

                # Deal with skipping frames
                if skipped_frames < self.frames_to_skip:
                    total_cycles = len(shot_indices)

                    # Check whether the number of acquisition cycles processed in this dataset
                    # takes us over the number of frames to skip or not
                    if skipped_frames + total_cycles < self.frames_to_skip:
                        skipped_frames += total_cycles
                        continue

                    # If it does, remove the appropriate number of shot indices. Note that the
                    # original shot_indices array will act as if one cycle has been skipped
                    else:
                        for i in range(self.frames_to_skip - skipped_frames - 1):
                            shot_indices.pop(0)

                else:
                    # Add a -1 at the start so all acquisition cylces can be processed in a single loop
                    shot_indices = np.hstack((np.array(-1), shot_indices))

                # Remove information on the memory register
                shot_data = shot_data[:,:3]

                # Deal with the remainder of the dataset
                for i in range(len(shot_indices) - 1):
                    if processed_frames == self.frames_to_proc:
                        break

                    if processed_frames % total_proc == proc_no:
                        # Convert to PImMS format and yield the data
                        yield shot_data[shot_indices[i] + 1:shot_indices[i+1]]

                    processed_frames += 1
