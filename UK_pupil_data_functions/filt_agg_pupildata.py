
import numpy as np
import pandas as pd

import os

from scipy.sparse import coo_matrix


from pathlib import Path

p = Path(os.getcwd()).parents[0]

# set file paths 
schooldatapath = '/Users/lsh1514285/jdrive/SCDATA/'
filename = 'Autumn_Census_Addresses_2020.txt'
filename_hh_id = 'aut_hh_v2.csv'
postcode_path = str(p) + '/Postcode_to_Output_Area_to_Lower_Layer_Super_Output_Area_to_Middle_Layer_Super_Output_Area_to_Local_Authority_District_(August_2018)_Lookup_in_the_UK.csv'


postcode_locations = pd.read_csv('../school_networks/Dutch data/NSPL_NOV_2019_UK.csv', encoding='cp1252', usecols=['pcds', 'lat', 'long'])
postcode_dict = pd.read_csv('../Postcode_to_Output_Area_to_Lower_Layer_Super_Output_Area_to_Middle_Layer_Super_Output_Area_to_Local_Authority_District_(August_2018)_Lookup_in_the_UK.csv')
postcode_to_lad = postcode_dict[['pcds', 'ladcd', 'ladnm']].rename(columns={'pcds':'Postcode_AUT20'})

# load pupil data 
pupil_data = pd.read_table(schooldatapath + filename, delimiter='\t', encoding='cp1252')

# load hh_ids matched by household_matching.R and merge into pupil_data
pupil_hh_ids = pd.read_csv(schooldatapath + filename_hh_id, encoding='cp1252')
pupil_data = pupil_data.merge(pupil_hh_ids, how='left', on='PupilMatchingRefAnonymous_AUT20')
pupil_data = pupil_data[pupil_data.index.isin(pupil_hh_ids.unfiltered_rowkey)]

# Calculate pupils hh sizes 
hh_sizes = pupil_hh_ids.groupby('hh_id').count().PupilMatchingRefAnonymous_AUT20
hh_sizes = pd.DataFrame(hh_sizes).reset_index().rename(columns={'PupilMatchingRefAnonymous_AUT20':'hh_size'})
pupil_data = pupil_data.merge(hh_sizes, how='left', on='hh_id')

# filter pupils on Enrol status, Border status and hhsize (not over 20 children - deemed impossibly large)
pupil_data = pupil_data[pupil_data.EnrolStatus_AUT20.isin(['C', 'M', 'F'])]
pupil_data = pupil_data[pupil_data.Boarder_AUT20 == 'N']
pupil_data = pupil_data[pupil_data.hh_size < 20]

# remove households duplicated due to multiple postcodes
hh_between_schools = pupil_data.groupby('hh_id').nunique()[['Postcode_AUT20']].reset_index()
idswithmultiplepostcodes = hh_between_schools[hh_between_schools.Postcode_AUT20 > 1].hh_id
pupil_data = pupil_data[pupil_data.hh_id.isin(np.array(idswithmultiplepostcodes)) != True]


# assign local authority to pupils and schools based on postcode
pupil_data = pupil_data.merge(postcode_to_lad, how='left', on='Postcode_AUT20')
pupil_data.rename(columns={'ladcd':'ladcd_pupil', 'ladnm':'ladnm_pupil'}, inplace=True)
pupil_data = pupil_data.merge(postcode_to_lad.rename(columns={"Postcode_AUT20":"SchoolPostcode_AUT20"}), how='left', on='SchoolPostcode_AUT20')
pupil_data.rename(columns={'ladcd':'ladcd_school', 'ladnm':'ladnm_school'}, inplace=True)


# Generate schools dataframe with codes, postcode, local authority, number of pupils, mean age (based on year of birth), primary/secondary status (sec mean age > 11 yrs), and coordinates
all_schools_frame = pupil_data[['URN_AUT20', 'LAEstab_AUT20', 'SchoolPostcode_AUT20' ]].drop_duplicates()
all_schools_frame = all_schools_frame.merge(postcode_to_lad.rename(columns = {'Postcode_AUT20':'SchoolPostcode_AUT20'}), how='left', on='SchoolPostcode_AUT20')
school_sizes = pupil_data.groupby('URN_AUT20').count().PupilMatchingRefAnonymous_AUT20.reset_index()
all_schools_frame = school_sizes.merge(all_schools_frame, on='URN_AUT20', how='left').rename(columns={"PupilMatchingRefAnonymous_AUT20":"pupil_count"})
all_schools_frame = all_schools_frame.merge(postcode_locations.rename(columns = {'pcds':'SchoolPostcode_AUT20'}), how='left', on='SchoolPostcode_AUT20')


mean_ages = pupil_data[['URN_AUT20','YearOfBirth_AUT20']].groupby('URN_AUT20').mean()[['YearOfBirth_AUT20']].reset_index().rename(columns={'YearOfBirth_AUT20':'mean_yob'})
all_schools_frame = all_schools_frame.merge(mean_ages, how = "left", on='URN_AUT20')
all_schools_frame['kind'] = ['pri' if y > 2008 else 'sec' for y in all_schools_frame.mean_yob ]
sec_codes = all_schools_frame[all_schools_frame.kind == 'sec'].URN_AUT20
pri_codes = all_schools_frame[all_schools_frame.kind == 'pri'].URN_AUT20

all_schools_frame['xy'] = list(zip(all_schools_frame['long'], all_schools_frame['lat']))
pos_geo = all_schools_frame[['URN_AUT20','xy']].set_index('URN_AUT20').to_dict()
pos_geo = pos_geo['xy']





all_schools_frame.to_csv(schooldatapath + '/all_schools_frame.csv')
pupil_data.to_csv(schooldatapath + '/pupil_data.csv')


# Generate schools dataframe with codes, postcode, local authority, number of pupils, mean age (based on year of birth), primary/secondary status (sec mean age > 11 yrs)
sec_codes = all_schools_frame[all_schools_frame.kind == 'sec'].URN_AUT20
pri_codes = all_schools_frame[all_schools_frame.kind == 'pri'].URN_AUT20



london = all_schools_frame[all_schools_frame.LAEstab_AUT20 < 3200000].URN_AUT20
birmingham = all_schools_frame[(all_schools_frame.ladnm == 'Birmingham') & (all_schools_frame.LAEstab_AUT20 > 3300000)].URN_AUT20


pos_geo = all_schools_frame[['URN_AUT20','xy']].set_index('URN_AUT20').to_dict()
pos_geo = pos_geo['xy']



