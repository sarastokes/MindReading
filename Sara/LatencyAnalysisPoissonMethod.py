# -*- coding: utf-8 -*-
"""
Latency analysis implementing Rahul's method

Created on Wed Aug 29 13:12:14 2018

@author: sarap
"""


#%% STANDARD IMPORTS
import os
import sys
import time
import pickle
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.axes as plt_axes
import time

import seaborn as sns
sns.set_context('talk', font_scale=1.6, rc={'lines.markeredgewidth': 2})
sns.set_style('white')
sns.set_palette('deep');

#%% IMPORTS FROM MINDREADING REPOSITORY
sys.path.append('D:/resources/mindreading_repo/mindreading/Sara/')
from neuropixel_data import open_experiment, check_folder, get_depth

sys.path.append('D:/resources/mindreading_repo/mindreading/Sebastien/')
from SDF import SDF

sys.path.append('D:/resources/mindreading/Rahul/')
from get_highfire_starts import get_highfire_starts
from find_min_highfire import find_min_highfire

#%% IMPORT DATA IF NEEDED
drive_path = os.path.normpath('d:/visual_coding_neuropixels/')
dataset = open_experiment(drive_path, 2)
#%% INFORMATION FOR SAVING
expt_index = dataset.nwb_path[-6:-4]
save_path = os.path.normpath('D:/Latencies/{}/'.format(expt_index))
print('Saving to: ', save_path)
check_folder(save_path)

#%% DATA SETTINGS

# Experiment to analyze:
stim_name = 'natural_scenes'
stim_table = dataset.get_stimulus_table(stim_name)
# stim_name = 'flash_decrement'
# stim_table = stim_table[stim_table['color'] == -1]
# Regions to analyze:
region_list = dataset.unit_df['structure'].unique()
print('Analyzing regions: ', region_list)

#%% ANALYSIS SETTINGS
min_start_time=15 # (minimum time in ms after which baseline ends)
pre_time=100 # (time in sec in sdf function before stimulus)
pre_stim_time = 0.1
post_time = 0
# %% CALCULATED SETTINGS
window_length = int(pre_time + 250)
num_trials = stim_table.shape[0]
#%% MAIN CALCULATION

for region in region_list:
    # Time single region
    start_timer = time.time()
    # Identify all units in this structure
    units_in_structure = dataset.unit_df[dataset.unit_df['structure']==region]
    print('Analyzing {} units in {}'.format(len(units_in_structure), str(region)))
    # Identify all probes that probed this structure
    probes_in_structure = units_in_structure['probe'].unique()
    # Initialize list that will contain all the latency info for all units.
    latency = []
    # Initialize the data frame
    col = ['structure', 'probe', 'unit_id', 'depth', 'latency']
    Big_dataframe = pd.DataFrame(columns=col)

    for probe in probes_in_structure: 
        # Get a dictionary of the depths
        depths = {}
        for i, row in units_in_structure[units_in_structure['probe'] == probe].iterrows():
            depths[row['unit_id']] = row['depth']
        # Find the spike times of all the units recorded from this probe
        probe_spikes = dataset.spike_times[probe]
        units_on_probe_in_structure = units_in_structure['unit_id'][units_in_structure['probe']==probe]
        print('    {} contains {} units'.format(probe, len(units_on_probe_in_structure)))
        
        for unit in units_on_probe_in_structure: # Loop through units on probe
            
            raster_matrix = np.zeros((num_trials, window_length))            
            unit_spikes = probe_spikes[unit]
            
            #Loop through every presentation of any image to create raster matrix
            for i,start in enumerate(stim_table.start):
                #Find spikes times between start and end of this trial.
                spike_timestamps = unit_spikes[(unit_spikes > start - pre_time*1e-3) & (unit_spikes <= start + post_time*1e-3)]
                #Subtract start time of stimulus presentation
                spike_timestamps = (spike_timestamps - (start-pre_time*1e-3))*1000
                spike_timestamps = spike_timestamps.astype(int)
                #Add list of spikes to main list
                raster_matrix[i,spike_timestamps] = 1
            
            # Compute SDF on raster matrix    
            sdf = SDF(raster_matrix,5)    
            mean_SDF = sdf.mean(axis=0)
            latency = get_highfire_starts(mean_SDF[:350], 0.1, 15)
                  
            Big_dataframe = Big_dataframe.append(pd.DataFrame([[region, probe, unit, depths[unit], latency]], columns=col), ignore_index=True)
    
    print('Region analysis completed in ' + str(round(time.time()-start_timer)) + 'seconds')
    
    #% SAVE EACH REGION
    # Save as .pkl
    fname = os.path.join(save_path, os.path.normpath(region.decode('UTF-8') + '_' + stim_name + '_latency_rahul'))
    print('Saving as : {}'.format(fname + '.pkl'))
    f = open(fname + '.pkl', 'wb')
    pickle.dump(Big_dataframe, f)
    f.close()
    
    # Save as .json (for comparison)
    Big_dataframe.to_json(fname + '_rahul.json', orient='split')
    
    # % PLOT EACH REGION
    #Plot histogram of latencies for this region
    vals = Big_dataframe['latency'].values.astype(float) #transforms datatype  to allow removing the nan entries
    vals_nonan = vals[~np.isnan(vals)] #remove the nans
    counts, edges = np.histogram(vals_nonan, bins=20)
    centers = edges[:1] - (edges[1]-edges[0])/2
    mean_latency = np.mean(vals_nonan) #calculate the mean latency
    median_latency = np.median(vals_nonan) #calculate the median latency

    fig,ax1 = plt.subplots(1,1,figsize=(8,5)) #initialize subplot
    plt.hist(vals_nonan, 20) #plot the histogram
    ax1.set_xlabel('Latency of visual response (msec)')
    ax1.set_ylabel('Number of units')
    ax1.set_title('Natural scenes in ' + region)
    y_axis_max = plt_axes.Axes.get_ylim(ax1)[1] 
    ax1.vlines(mean_latency, 0, y_axis_max)
    ax1.vlines(median_latency, 0, y_axis_max)
    plt.text(mean_latency+10, y_axis_max, 'mean = ' + str(round(mean_latency)), fontsize=18)
    plt.text(ax1.get_xlim()[0]+15, y_axis_max, 'median = ' + str(round(median_latency)), fontsize=18)
    plt.grid(True)    
    fig.savefig(fname + '_rahul.png')
            
print('Latency analysis completed in ' + str(round(time.time()-start_timer)) + 'seconds')