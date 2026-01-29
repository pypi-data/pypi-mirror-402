
import data_import_tools as dit
import network_evaluation_functions as nef
import network_propagation as prop
from shuffle_networks import shuffle_network
import pandas as pd
import numpy as np
import networkx as nx
import os

if True:
    datadir="/cellar/users/snwright/Data/Network_Analysis/Processed_Data/v2_2022/"
    network = dit.load_network_file(datadir+"bind.v8_net.txt", verbose=True)
    genesets = dit.load_node_sets('/cellar/users/snwright/Git/Network_Evaluation_Tools/Data/DisGeNET_genesets_entrez.txt', id_type='Entrez')
    genesets_p = nef.calculate_p(network, genesets, id_type='Entrez')
    alpha = prop.calculate_alpha(network)
    print("kernel")
    kernel = pd.read_csv("/cellar/users/snwright/Data/Network_Analysis/Evaluation/bind.v3_kernel.csv", index_col=0)
    if kernel.index.dtype == int:
        kernel.columns = [int(c) for c in kernel.columns]
    #kernel = nef.construct_prop_kernel(network, alpha=alpha, verbose=True)
    print("AUPRC")
    AUPRC_values = nef.small_network_AUPRC_wrapper(kernel, genesets, genesets_p, n=30, cores=1, verbose=True)
    null_AUPRCs = []
    print("loop")
    for i in range(10):
        shuffNet = shuffle_network(network, n_swaps=1)
        shuffNet_kernel = nef.construct_prop_kernel(shuffNet, alpha=alpha, verbose=False)
        shuffNet_AUPRCs = nef.small_network_AUPRC_wrapper(shuffNet_kernel, genesets, genesets_p, n=30, cores=1, verbose=False)
        null_AUPRCs.append(shuffNet_AUPRCs)
        print('shuffNet', repr(i+1), 'AUPRCs calculated')
    # Construct table of null AUPRCs
    null_AUPRCs_table = pd.concat(null_AUPRCs, axis=1)
    null_AUPRCs_table.columns = ['shuffNet'+repr(i+1) for i in range(len(null_AUPRCs))]
    network_performance = nef.calculate_network_performance_score(AUPRC_values, null_AUPRCs_table, verbose=True)
    # Calculate network performance gain over median null AUPRC
    network_perf_gain = nef.calculate_network_performance_gain(AUPRC_values, null_AUPRCs_table, verbose=True)
    network_perf_gain.name = 'Test Network'
    network_performance.name = 'Test Network'
    # Rank network on average performance across gene sets vs performance on same gene sets in previous network set
    all_network_performance = pd.read_csv('~/Data/Network_Performance.csv', index_col=0)
    all_network_performance_filt = pd.concat([network_performance, all_network_performance.ix[network_performance.index]], axis=1)
    network_performance_rank_table = all_network_performance_filt.rank(axis=1, ascending=False)
    network_performance_rankings = network_performance_rank_table['Test Network']
    # Rank network on average performance gain across gene sets vs performance gain on same gene sets in previous network set
    all_network_perf_gain = pd.read_csv('~/Data/Network_Performance_Gain.csv', index_col=0)
    all_network_perf_gain_filt = pd.concat([network_perf_gain, all_network_perf_gain.ix[network_perf_gain.index]], axis=1)
    network_perf_gain_rank_table = all_network_performance_filt.rank(axis=1, ascending=False)
    network_perf_gain_rankings = network_perf_gain_rank_table['Test Network']
    # Network Performance
    network_performance_metric_ranks = pd.concat([network_performance, network_performance_rankings, network_perf_gain, network_perf_gain_rankings], axis=1)
    network_performance_metric_ranks.columns = ['Network Performance', 'Network Performance Rank', 'Network Performance Gain', 'Network Performance Gain Rank']
    network_performance_metric_ranks.sort_values(by=['Network Performance Rank', 'Network Performance', 'Network Performance Gain Rank', 'Network Performance Gain'],
                                                ascending=[True, False, True, False])
    # Construct network summary table
    network_summary = {}
    network_summary['Nodes'] = int(len(network.nodes()))
    network_summary['Edges'] = int(len(network.edges()))
    network_summary['Avg Node Degree'] = np.mean(network.degree().values())
    network_summary['Edge Density'] = 2*network_summary['Edges'] / float((network_summary['Nodes']*(network_summary['Nodes']-1)))
    network_summary['Avg Network Performance Rank'] = network_performance_rankings.mean()
    network_summary['Avg Network Performance Rank, Rank'] = int(network_performance_rank_table.mean().rank().ix['Test Network'])
    network_summary['Avg Network Performance Gain Rank'] = network_perf_gain_rankings.mean()
    network_summary['Avg Network Performance Gain Rank, Rank'] = int(network_perf_gain_rank_table.mean().rank().ix['Test Network'])
    for item in ['Nodes', 'Edges' ,'Avg Node Degree', 'Edge Density', 'Avg Network Performance Rank', 'Avg Network Performance Rank, Rank',
                'Avg Network Performance Gain Rank', 'Avg Network Performance Gain Rank, Rank']:
        print(item+':\t'+repr(network_summary[item]))