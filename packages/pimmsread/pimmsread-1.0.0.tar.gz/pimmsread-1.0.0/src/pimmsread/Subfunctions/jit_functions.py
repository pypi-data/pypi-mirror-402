from numba import jit

@jit(nopython=True, cache=True)
def generateAcqCycleToF(data, tof):
    for arrival_time in data[:,2]:
        tof[arrival_time] += 1

    # tof is automatically updated in the calling function

@jit(nopython=True, cache=True)
def read_full_data(acqCycleData, full_image, ToF):
    for line in acqCycleData:
        # Increment the appropriate part of the image
        full_image[line[1], line[0], line[2]] += 1
        ToF[line[2]] += 1

    # full_image and ToF are automatically updated in the calling function

@jit(nopython=True, cache=True)
def read_full_image_data(acqCycleData, full_image):
    for line in acqCycleData:
        # Increment the appropriate part of the image
        full_image[line[1], line[0], line[2]] += 1

    # full_image is automatically updated in the calling function

@jit(nopython=True, cache=True)
def read_image_data_subset(acqCycleData, subset_image, min_time, max_time):
    for line in acqCycleData:
        # Check whether the data is in the appropriate time range
        if line[2] >= min_time and line[2] <= max_time:
            # Increment the appropriate part of the image
            subset_image[line[1], line[0], line[2] - min_time] += 1

    # subset_image is automatically updated in the calling function

@jit(nopython=True, cache=True)
def read_image_data_subset_single_image(acqCycleData, subset_image, min_time, max_time):
    for line in acqCycleData:
        # Check whether the data is in the appropriate time range
        if line[2] >= min_time and line[2] <= max_time:
            # Increment the appropriate part of the image
            subset_image[line[1], line[0]] += 1

    # subset_image is automatically updated in the calling function

@jit(nopython=True, cache=True)
def read_ranges_image_data(acqCycleData, image_data, bin_ranges):
    for line in acqCycleData:
        for i, bin_range in enumerate(bin_ranges):
            if line[2] >= bin_range[0] and line[2] <= bin_range[1]:
                image_data[i, line[1], line[0]] += 1

    # image_data is automatically updated in the calling function

@jit(nopython=True, cache=True)
def read_ranges_image_data_with_frame_intensities(acqCycleData, image_data, bin_ranges, intensity):
    for line in acqCycleData:
        for i, bin_range in enumerate(bin_ranges):
            if line[2] >= bin_range[0] and line[2] <= bin_range[1]:
                image_data[i, line[1], line[0]] += 1
                intensity[i] += 1

    # image_data and intensity are automatically updated in the calling function

@jit(nopython=True, cache=True)
def generateAcqCycleDelayToF(data, tof, delay, bin_edges, bin_count, no_bins, min_tof, max_tof):
    # Determine which delay bin to append to
    # The count of delay >= bin edges gives the bin number
    delay_bin = sum(delay >= bin_edges) - 1

    # Deal with the edge cases
    if delay_bin == -1:
        return
    elif delay_bin == no_bins:
        # Include the top edge
        if delay == bin_edges[-1]:
            delay_bin -= 1
        else:
            return

    # Update the bin count
    bin_count[delay_bin] += 1
    
    # Read the data into the ToF array
    for arrival_time in data[:,2]:
        if arrival_time < min_tof:
            continue
        if arrival_time > max_tof:
            continue
        tof[delay_bin, arrival_time - min_tof] += 1    

@jit(nopython=True, cache=True)
def read_image_data_subset_delay_image(acqCycleData, subset_image, delay, bin_edges, bin_count, no_bins, min_time, max_time):
    # Determine which delay bin to append to
    # The count of delay >= bin edges gives the bin number
    delay_bin = sum(delay >= bin_edges) - 1

    # Deal with the edge cases
    if delay_bin == -1:
        return
    elif delay_bin == no_bins:
        # Include the top edge
        if delay == bin_edges[-1]:
            delay_bin -= 1
        else:
            return

    # Update the bin count
    bin_count[delay_bin] += 1

    for line in acqCycleData:
        # Check whether the data is in the appropriate time range
        if line[2] >= min_time and line[2] <= max_time:
            # Increment the appropriate part of the image
            subset_image[delay_bin, line[1], line[0]] += 1

    # subset_image is automatically updated in the calling function