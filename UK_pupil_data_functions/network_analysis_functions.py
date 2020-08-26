import pandas as pd
import numpy as np
import networkx as nx
from scipy.sparse import coo_matrix
from scipy import optimize
import matplotlib.pyplot as plt


def op_fs(s, r0):
    rcalc = lambda s, r0, r_inf : r_inf - 1. +  np.exp(- s * r0 * r_inf)
    fun_op = lambda r : rcalc(s, r0, r) 
    fs = optimize.root(fun_op, 0.5).x[0]
    return fs * s
    

# Create network from UK school data using particular school years
def specific_years_adjmat(years_active, pupil_data):
    
    # filter the data to only include particular school years
    pupil_data = pupil_data[[year in years_active for year in pupil_data.NCYearActual_AUT20]]
    
    

    # create DFs with numeric ids 0 to N and hh and school ids
    hhiddict = pd.DataFrame(pupil_data.hh_id.unique()).reset_index().rename(columns = {'index':'local_hh_id', 0:'hh_id'})
    urn_dict = pd.DataFrame(pupil_data.URN_AUT20.unique()).reset_index().rename(columns = {'index':'local_urn', 0:'URN_AUT20'})

    
    # merge DFs into pupil data array to assign local ids to each child
    pupil_data_local = pupil_data.merge(hhiddict, how='left', on='hh_id')
    pupil_data_local = pupil_data_local.merge(urn_dict, how='left', on='URN_AUT20')

    # create nested DF with number of children per hh per school - sparse
    pupils_per_hh_per_school= pupil_data_local[['PupilMatchingRefAnonymous_AUT20', 'local_urn', 'local_hh_id']].groupby(['local_urn', 'local_hh_id']).nunique().PupilMatchingRefAnonymous_AUT20

    # convert to sparse matrix (uing scipy coo) [too large for full matrix]
    coo = coo_matrix((pupils_per_hh_per_school.values, zip(*pupils_per_hh_per_school.index.values)))
    
    # square matrix to find adjacency matrix of contact pairs (Cij)
    adjmat = coo.dot(coo.transpose()).toarray() 
    # set diagonal to 0
    adjmat = adjmat - np.diag(np.diag(adjmat))
    
    # record the school list for reference (order of rows/columns)
    nodelist = np.array(urn_dict.URN_AUT20)
    
    return adjmat, nodelist, pupil_data_local

# find connected components in a binary outbreak network (trans_mat_bin)
def calculate_connected_components_nx(trans_mat_bin, nodelist):
    trans_net_bin = create_network_from_transmat_undi(trans_mat_bin, nodelist = nodelist)
    return nx.components.connected_components(trans_net_bin)


# calculate transmission probabilitlies from contact pair matrix (adjmat) with differnt vaccination (vacc_dict), R0 and q (within household transmission probability)
def create_transmat_from_adjmat(adj_mat, vacc_dict=False, nodelist=[], R0=15., q=0.5):
    if vacc_dict == False:
        vacc_dict = dict(np.transpose([nodelist, np.zeros_like(nodelist)]))
    FSLIST = [op_fs(p, R0) for p in np.arange(0, 1., 0.001)]
  
                         
    fs_vec = np.array([FSLIST[int((1.-vacc_dict[n])*1000) - 1] for n in nodelist])
    vac_vec = np.array([vacc_dict[n] for n in nodelist])

 
    Pst_vec = 1. - np.minimum(1.,1./(R0*(1.-vac_vec)))
    pairprob = np.outer( q*fs_vec, (1.-vac_vec)*Pst_vec)
    trans_mat = 1. - (1. - pairprob) ** adj_mat
    
    return trans_mat

# create undirected network from a matrix
def create_network_from_transmat_undi(trans_mat, nodelist):
    trans_net = nx.from_numpy_matrix(trans_mat)
    rename_dict = dict([[i, nodelist[i]] for i in range(len(nodelist))])
    trans_net = nx.relabel_nodes(trans_net, rename_dict)
    return trans_net


# plot a network (use scalar to scale nodes/edges depending on whether network is contact pair / transmission prob / binary)
def plot_transnet(trans_net, pos, highlight=[] , title='transmission network of the Nethelands', sizes='deg', ax=False, scaler=1.):
    
    if ax == False:
    
        fig = plt.figure(figsize=[14,20])
        ax = fig.add_subplot(111)
    
    
    
    highlight_net = trans_net.subgraph(nodes=highlight)
    if sizes == 'deg':
        degree_dict = trans_net.degree(weight='weight')
        sizes = degree_dict
    else:
        sizes
    edge_dict = nx.get_edge_attributes(trans_net, 'weight')

    nx.draw_networkx_nodes(trans_net, weight='weight', pos=pos, node_size=np.array([sizes[n]*scaler for n in trans_net.nodes()])*1., node_color='DodgerBlue', alpha=0.7, linewidths=0.2, ax=ax)
    nx.draw_networkx_nodes(highlight_net, weight='weight', pos=pos, node_size=np.array([sizes[n]*scaler for n in highlight_net.nodes()])*1., node_color='Red', alpha=0.7, linewidths=0.2, ax=ax)
    nx.draw_networkx_edges(trans_net, weight='weight', pos=pos, edgelist=trans_net.edges(), width=np.array([edge_dict[e ]*scaler for e in trans_net.edges()]), edge_color='Grey', ax=ax, arrows=False)
    ax.set_aspect('equal')
    
    ax.set_xticks([])
    ax.set_yticks([])
    
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    ax.set_title(title)
    
    return ax