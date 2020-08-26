import sys
sys.path.insert(1, 'UK_pupil_data_functions')

import network_analysis_functions as naf
import pandas as pd
import importlib as il
import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Pool
import os



pupil_data = pd.read_csv('/Users/lsh1514285/jdrive/SCDATA/pupil_data.csv')
years_actives = [[1, 6, 'R', '1', '6'], [1, 6, 'R', '1', '6', 10, '10'], [1, 6, 'R', '1', '6', 12, '12'], 
                 [1, 6, 'R', '1', '6', 10, '10', '12', 12], [1, 2, 3, 4, 5, 6, 'R', '1', '2', '3', '4', '5', '6'], 
                 [7, 8, 9, 10, 11, 12, 13, '7', '8', '9', '10', '11', '12', '13'], 
                 [1, 2, 3, 4, 5, 6, 'R', '1', '2', '3', '4', '5', '6', 7, 8, 9, 10, 11, 12, 13, '7', '8', '9', '10', '11', '12', '13']]

 
print(os.getcwd())    


def generate_and_find_components(y,years_actives = years_actives, pupil_data=pupil_data, iters = 20): 
    
    years_active = years_actives[y]
    adjmat, nodelist, pupil_data_local = naf.specific_years_adjmat(years_active = years_active, pupil_data=pupil_data)
    
    for R0 in np.arange(1.1, 1.6, 0.1):
        print(R0, y)
        uk_trans_mat = naf.create_transmat_from_adjmat(adjmat, nodelist=nodelist, R0=R0, q=0.15)
        dfs = []
        for n in range(iters):
            uk_trans_mat_bin = (uk_trans_mat > np.random.rand(*adjmat.shape))*1.

            cc_out = calculate_connected_components_nx(uk_trans_mat_bin, nodelist)




            for i,cc in enumerate(list(cc_out)): 
                hh_ids = pupil_data_local[pupil_data_local.URN_AUT20.isin(cc)].hh_id.unique()
                dfs.append(pd.DataFrame(np.transpose([list(cc), [i+1]*len(cc), [len(cc)]*len(cc), [len(hh_ids)]*len(cc), [n+1]*len(cc) ]), 
                                        columns=['urn', 'component', 'size', 'size_hh', 'n']))

        df = pd.concat(dfs)
        df.to_csv(str(round(R0,2)) + '_' + str(y) + '.csv')
        

if __name__ == '__main__':
    with Pool(5) as p:
            p.map(generate_and_find_components, range(len(years_actives)))





        
        

