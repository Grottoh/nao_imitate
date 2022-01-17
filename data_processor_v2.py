import pickle
import numpy as np
import matplotlib.pyplot as plt

PATH_DATA = "./logs/"
USE_TEST_DATA = False
data_index = 8

def save(filename, l):
    path = PATH_DATA+filename 
    with open(path, "wb") as f:
        pickle.dump(l, f)
def load(filename_prefix, data_index):
    path = "{}{}{:03d}.pkl".format(PATH_DATA, filename_prefix, data_index)
    with open(path, "r") as f: # Change <"r"> to <"rb"> when getting errors
        return pickle.load(f)

def get_extremes(array, n_extremes=1):
    n_extremes = min(len(array), n_extremes)
    n_lowest = array[np.argpartition(array, n_extremes)[:n_extremes]]
    n_highest = array[np.argpartition(array, -n_extremes)[-n_extremes:]]
    return n_lowest, n_highest
 

def print_spans_info(spans, name):
    print("-"*20 + " " + name + " " + "-"*20)
    if np.any(spans < 0):
        print("<{}> contains negative values!".format(name))
    print("np.average({})=={}".format(name, np.average(spans)))
    print("    np.std({})=={}".format(name, np.std(spans)))
    n_lowest, n_highest = get_extremes(spans)
    print("{}  lowest values in <{}>: {}".format(len(n_lowest), name, n_lowest))
    print("{} highest values in <{}>: {}".format(len(n_highest), name, n_highest))
    print()

def get_inner_spans(log, name, print_info=True):
    """ Get the time spans between beginning and end times of a log. """
    spans = []
    for entry in log:
        time_start, time_end = entry[1], entry[2]
        spans.append(time_end-time_start)
    spans = np.array(spans)
    print_spans_info(spans, name)
    return spans

def get_outer_spans(log_a, log_b, name):
    """ Get the time spans between the end of one log and the beginning of another. """
    indices_b = [entry[0] for entry in log_b]
    spans = []
    for entry_a in log_a:
        index_a = entry_a[0]
        if index_a in indices_b:
            pos_b = indices_b.index(index_a)
            time_end_a, time_start_b = entry_a[2], log_b[pos_b][1]
            spans.append(time_start_b - time_end_a)
    spans = np.array(spans)
    print_spans_info(spans, name)
    return spans

def plot_spans(spans_all, names, markersize=15, elinewidth=6):
    for i, (spans, name) in enumerate(zip(spans_all, names)):
        mean = np.mean(spans)
        std = np.std(spans)
        plt.errorbar([i], mean, std, linestyle='none', color='blue', marker='o', label=name, markersize=markersize, elinewidth=elinewidth)
        n_lowest, n_highest = get_extremes(spans)
        for low, high in zip(n_lowest, n_highest):
            plt.errorbar([i],  low, 0, marker='x', color='red', label='_nolegend_', markersize=markersize, elinewidth=elinewidth)
            plt.errorbar([i], high, 0, marker='x', color='red', label='_nolegend_', markersize=markersize, elinewidth=elinewidth)
    plt.title('Average time spans of pipeline processes', fontsize=30)
    plt.ylabel('seconds', fontsize=24)
    plt.xticks(range(len(names)), names, size='xx-large')
    plt.yticks(size='xx-large')
    plt.show()

if USE_TEST_DATA:
    log_test_0 = [(0, 1642361840.2331014, 1642361843.2331014),
                  (1, 1642361843.3331014, 1642361844.9331014),
                  (2, 1642361845.1331014, 1642361847.8331014),
                  (3, 1642361847.9331014, 1642361851.4331014),
                  (4, 1642361851.6331014, 1642361854.3331014)]

    log_test_1 =  [(0, 1642361844.2331014, 1642361844.2331014),
                  (1, 1642361845.3331014, 1642361845.9331014),
                  (2, 1642361848.1331014, 1642361848.8331014),
                  (3, 1642361852.9331014, 1642361851.4331014),
                  (4, 1642361855.6331014, 1642361855.3331014)]

    log_test_2 = [(0, 1642361840.2331014, 1642361843.2331014),
                  (1, 1642361843.3331014, 1642361844.9331014),
                  (2, 1642361847.1331014, 1642361848.8331014),
                  (3, 1642361849.9331014, 1642361851.4331014),
                  (4, 1642361853.6331014, 1642361855.3331014)]

    spans_test_0   = get_inner_spans(log_test_0, 'log_test_0')
    spans_test_1   = get_inner_spans(log_test_1, 'log_test_1')
    spans_test_2   = get_inner_spans(log_test_2, 'log_test_2')
    spans_tests_01 = get_outer_spans(log_test_0, log_test_1, 'log_tests_01')

    plot_spans([spans_test_0, spans_test_1, spans_test_2, spans_tests_01],
               ['test_0', 'test_1', 'test_2', 'tests_01'])
else:
    log_imcapt     = load("log_imcapt_", data_index)     # (index, log_time_start, log_time_end)
    log_imret      = load("log_imret_", data_index)      # (index, log_time_start, log_time_end)
    log_imload     = load("log_imload_", data_index)     # (index, log_time_start, log_time_end)
    log_opcomp     = load("log_opcomp_", data_index)     # (index, log_time_start, log_time_end, pose)
    log_convangle  = load("log_convangle_", data_index)  # (index, log_time_start, log_time_end, angles)
    log_angsend    = load("log_angsend_", data_index)    # (index, log_time_start, log_time_end, angles)
    log_angload    = load("log_angload_", data_index)    # (index, log_time_start, log_time_end, angles)
    log_movejoints = load("log_movejoints_", data_index) # (index, log_time_start, log_time_end, joint-angles)
    
    if not len(log_imcapt) == log_imcapt[-1][0]+1: # If true, something is wrong with the indices
        print("len(log_imcapt)=={} != log_imcapt[-1][0]+1=={}\n".format(len(log_imcapt), log_imcapt[-1][0]+1))
    
    # Print the lengths of each log such that they can be checked for inconsistencies
    print("len(log_imcapt)    =={:04d}".format(len(log_imcapt)))
    print("len(log_imret)     =={:04d}".format(len(log_imret)))
    print("len(log_imload)    =={:04d}".format(len(log_imload)))
    print("len(log_opcomp)    =={:04d}".format(len(log_opcomp)))
    print("len(log_convangle) =={:04d}".format(len(log_convangle)))
    print("len(log_angsend)   =={:04d}".format(len(log_angsend)))
    print("len(log_angload)   =={:04d}".format(len(log_angload)))
    print("len(log_movejoints)=={:04d}".format(len(log_movejoints)))
    print()
    
    spans_imcapt     = get_inner_spans(log_imcapt, 'log_imcapt')
    spans_imret      = get_inner_spans(log_imret, 'log_imret')
    spans_imload     = get_inner_spans(log_imload, 'log_imload')
    spans_opcomp     = get_inner_spans(log_opcomp, 'log_opcomp')
    spans_convangle  = get_inner_spans(log_convangle, 'log_convangle')
    spans_angsend    = get_inner_spans(log_angsend, 'log_angsend')
    spans_angload    = get_inner_spans(log_angload, 'log_angload')
    spans_movejoints = get_inner_spans(log_movejoints, 'log_movejoints')
    
    spans_imtrans = get_outer_spans(log_imcapt, log_opcomp, 'imcapt-opcomp')
    spans_angtrans = get_outer_spans(log_convangle, log_movejoints, 'convangle-movejoints')
    
    spans_startend = []
    indices_movejoints = [entry[0] for entry in log_movejoints]
    spans_startend = []
    for entry_imcapt in log_imcapt:
        index_imcapt = entry_imcapt[0]
        if index_imcapt in indices_movejoints:
            pos_movejoints = indices_movejoints.index(index_imcapt)
            time_start_imcapt, time_end_movejoints = entry_imcapt[1], log_movejoints[pos_movejoints][2]
            spans_startend.append(time_end_movejoints - time_start_imcapt)
    spans_startend = np.array(spans_startend)
    print_spans_info(spans_startend, 'start-end')
            
    plot_spans([spans_imcapt, spans_imret, spans_imload, spans_opcomp,
                spans_convangle, spans_angsend, spans_angload, spans_movejoints, spans_startend],
               ['imcapt', 'imret', 'imload', 'opcomp', 'convangle', 'angsend',
                'angload', 'movejoints', 'startend'])

# =============================================================================
#     plot_spans([spans_imcapt, spans_imret, spans_imload, spans_opcomp,
#                 spans_convangle, spans_angsend, spans_angload, spans_movejoints,
#                 spans_imtrans, spans_angtrans, spans_startend],
#                ['imcapt', 'imret', 'imload', 'opcomp', 'convangle', 'angsend',
#                 'angload', 'movejoints', 'imtrans', 'angtrans', 'startend'])
# =============================================================================
    
    
# =============================================================================
#     print(log_imcapt[:5])
#     print()
#     print(log_imret[:5])
#     print()
#     print(log_imload[:5])
#     print()
#     print(log_movejoints[:5])
#     print()
# =============================================================================
    
# =============================================================================
#     print(log_angsend[:5])
#     print()
#     print(log_angload[:5])
#     print()
#     print(log_movejoints[:5])
# =============================================================================






