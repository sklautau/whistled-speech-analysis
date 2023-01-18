'''
This versions writes the output files in a folder provided by the user
in the command line.
'''
### an example for batch processing audios in a given folder with
# linear-scale frequency scan implementation
# Original author: Jiayi (Maggie) Zhang <jiayizha@andrew.cmu.edu>

import argparse
import time
import math
import os
import numpy as np

import librosa
import torch
import reassignment.reassignment_linear as reassign_lin
import matplotlib.pyplot as plt
#from mpl_toolkits.axes_grid1 import make_axes_locatable # colorbar

# turn the histogram matrix into an image
def make_image(spectrogram, minf, maxf, sr, length, save_dir):
    h, w = spectrogram.shape
    num = math.ceil(math.log2(maxf/minf))

    # calculate the tick marks
    y_axis = np.logspace(0, num, base=2) * minf * sr
    y_axis = np.round(y_axis).astype(int)
    y_range = np.linspace(0, h-1, num=len(y_axis))
    x_range = np.linspace(0, w-1, num=2)
    x_axis = np.linspace(0, round(length, 4), num=2)

    fig = plt.figure(figsize=(w/20, h/20))
    spec = np.log(spectrogram+1e-8)
    spec /= np.max(np.abs(spec))
    spec += 1
    plt.axis('off')
    #plt.yticks(y_range, y_axis[::-1])
    #plt.xticks(x_range, x_axis)
    plt.imshow(spec, cmap='inferno')
    #plt.colorbar(fraction=0.07,pad=0.04)
     
    # save image
    plt.savefig(save_dir, bbox_inches='tight')

if __name__ == '__main__':
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir',help='input folder with wav files',required=True)
    parser.add_argument('--output_dir',help='output folder for spec and PNG files',required=True)
    args = parser.parse_args()

    data_dir = args.data_dir
    output_dir = args.output_dir

    # defining constants and parameters
    q = 2
    tdeci = 96
    over = 2
    noct = 108
    minf = 1.5e-2
    maxf = 0.16

    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if (file.endswith(".wav")): # only run analysis on audio files
                filename = os.path.join(root, file)
                x, sr = librosa.load(filename, sr=None, mono=False)
                if (len(x.shape) > 1): # take only the first channel
                    x = x[0]
                length = len(x)/sr
                print("Processing: %s. Audio length: %.2f seconds"%(file, length))
                #torch.cuda.empty_cache()

                # time and run the anlysis
                tic = time.perf_counter(   )
                spectrogram = reassign_lin.high_resolution_spectrogram(x, q, tdeci, over, noct, minf, maxf, device=torch.device('cpu'))
                toc = time.perf_counter()
                print("Task done in %.5f seconds."%(toc-tic))

                # port the spectrogram to cpu
                # No need to do it if device = cpu
                spectrogram = spectrogram.cpu().numpy().T

                #save files
                basename = os.path.basename(filename)                
                output_file = os.path.join(output_dir,"%s"%basename.replace(".wav", "_spec"))
                np.save(output_file, spectrogram)
                print("Wrote",output_file)
                output_png_file = os.path.join(output_dir,"%s"%basename.replace(".wav", "_spec.png"))
                make_image(spectrogram, minf, maxf, sr, length, output_png_file)
                print("Wrote",output_png_file)


