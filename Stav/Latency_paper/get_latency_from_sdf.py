import numpy as np
from get_prestimulus_time import get_prestimulus_time
from get_time_window_buffer import get_time_window_buffer

def get_latency_from_sdf(sdf, number_of_std=2):
    pre_stimulus_time = get_prestimulus_time() - get_time_window_buffer()
    pre_stimulus_sdf = sdf[:pre_stimulus_time]
    post_stimulus_sdf = sdf[pre_stimulus_time:]

    pre_std_val = np.std(pre_stimulus_sdf)
    pre_mean_val = np.mean(pre_stimulus_sdf)
    positive_threshold = pre_mean_val + number_of_std*pre_std_val
    negative_threshold = pre_mean_val + -1*number_of_std*pre_std_val

    first_occur = -1
    pos_first_occur = -1
    neg_first_occur = -1
    response_type = np.nan

    if post_stimulus_sdf.max() > positive_threshold:
        pos_first_occur = np.argmax(post_stimulus_sdf > positive_threshold)

    if post_stimulus_sdf.min() < negative_threshold:
        neg_first_occur = np.argmax(post_stimulus_sdf < negative_threshold)

    if pos_first_occur > -1 and neg_first_occur > -1:
        if pos_first_occur < neg_first_occur:
            first_occur = pos_first_occur
            response_type = 1
        else:
            first_occur = neg_first_occur
            response_type = -1
    else:
        if pos_first_occur > -1:
            first_occur = pos_first_occur
            response_type = 1
        elif neg_first_occur > -1:
            first_occur = neg_first_occur
            response_type = -1

    response_time = np.nan
    if first_occur > -1:
        response_time = int(first_occur)

    return response_time, response_type