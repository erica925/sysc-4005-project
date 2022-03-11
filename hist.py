import numpy as np
import matplotlib.pyplot as plt
import math
import scipy.stats as stats

#define the folder where inspection time and assembly time files are located
DATA_FOLDER = "data/"

#load the inspection and assembly times from the files in the DATA_FOLDER
I1C1_times = np.loadtxt(DATA_FOLDER + 'servinsp1.dat', unpack = True)
I2C2_times = np.loadtxt(DATA_FOLDER + 'servinsp22.dat', unpack = True)
I2C3_times = np.loadtxt(DATA_FOLDER + 'servinsp23.dat', unpack = True)
W1_times = np.loadtxt(DATA_FOLDER + 'ws1.dat', unpack = True)
W2_times = np.loadtxt(DATA_FOLDER + 'ws2.dat', unpack = True)
W3_times = np.loadtxt(DATA_FOLDER + 'ws3.dat', unpack = True)

def build_qq_plot(title, data, test_dist):
    stats.probplot(data, dist = test_dist, plot = plt)
    plt.title(title + test_dist)
    plt.show()

def build_histogram(title, xlabel, ylabel, data):
    bins=math.floor(math.sqrt(len(data)))
    while True:
        arr=plt.hist(data,bins)
        zero_found = False
        for i in range(bins):
            if int(arr[0][i]) == 0:
                zero_found = True
        if not zero_found:
            break
        plt.cla()
        bins-=1
    chi_square_test(arr, len(data)/sum(data))
    for i in range(bins):
        plt.text(int(arr[1][i]),int(arr[0][i]),str(int(arr[0][i])))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()
    
def do_qq_plots(test_dist):
    build_qq_plot("Inspector 1 Inspection Times (Component 1)", I1C1_times, test_dist)
    build_qq_plot("Inspector 2 Inspection Times (Component 2)", I2C2_times, test_dist)
    build_qq_plot("Inspector 2 Inspection Times (Component 3)", I2C3_times, test_dist)
    build_qq_plot("Workstation 1 Assembly Times (Product 1)", W1_times, test_dist)
    build_qq_plot("Workstation 2 Assembly Times (Product 2)", W2_times, test_dist)
    build_qq_plot("Workstation 3 Assembly Times (Product 3)", W3_times, test_dist)
    
def do_histograms():
    build_histogram("Inspector 1 Inspection Times (Component 1)", "Minutes", "Frequency", I1C1_times)
    build_histogram("Inspector 2 Inspection Times (Component 2)", "Minutes", "Frequency", I2C2_times)
    build_histogram("Inspector 2 Inspection Times (Component 3)", "Minutes", "Frequency", I2C3_times)
    build_histogram("Workstation 1 Assembly Times (Product 1)", "Minutes", "Frequency", W1_times)
    build_histogram("Workstation 2 Assembly Times (Product 2)", "Minutes", "Frequency", W2_times)
    build_histogram("Workstation 3 Assembly Times (Product 3)", "Minutes", "Frequency", W3_times)

def chi_square_test(hist, lam):
    bin_counts = hist[0]
    bin_bottoms = hist[1]
    cum_probs_of_exp_dist = []
    n = sum(bin_counts)
    for x in bin_bottoms:
        cum_probs_of_exp_dist.append(1-math.e**(-1*lam*x))
    exp_freqs = []
    i = 0
    while i <= len(bin_bottoms):
        if i == 0:
            exp_freqs.append(n*(cum_probs_of_exp_dist[i]))
        elif i == len(bin_bottoms):
            exp_freqs.append(n*(1 - cum_probs_of_exp_dist[i - 1]))
        else:
            exp_freqs.append(n*(cum_probs_of_exp_dist[i] - cum_probs_of_exp_dist[i - 1]))
        i += 1
    
    ei = []
    oi = []
    running_exp_prob = 0
    running_obs_prob = 0
    for i in range(len(exp_freqs)):
        running_exp_prob += exp_freqs[i]
        if i == 0:
            running_obs_prob += 0
        elif i > len(bin_counts):
            running_obs_prob += 0
        else:
            running_obs_prob += bin_counts[i - 1]
        if running_exp_prob >= 5:
            if sum(exp_freqs[i + 1:]) < 5:
                ei.append(running_exp_prob + sum(exp_freqs[i + 1:]))
                oi.append(running_obs_prob + sum(bin_counts[i:]))
                break
            ei.append(running_exp_prob)
            oi.append(running_obs_prob)
            running_exp_prob = 0
            running_obs_prob = 0
    
    chi_square_sum = 0
    for i in range(len(oi)):
        chi_square_sum += (oi[i] - ei[i]) ** 2 / ei[i]
        
    print(chi_square_sum)
    
do_qq_plots("norm")
do_qq_plots("expon")
do_histograms()
