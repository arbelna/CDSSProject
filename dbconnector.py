import pandas as pd
import os
from datetime import datetime, timedelta


class DBConnector:
    def __init__(self, db_folder=''):
        # self.type = type
        self.db_folder_path = db_folder
        self.patients_medical_data = self.load_patients_medical_data()
        self.patients_personal_data, self.id2name_map, self.name2id_map = self.load_patients_personal_data()
        self.loinc_data, self.test2loincmap = self.load_loinc_data()

        # Create patients dictionary for easier retrival
        self.patients_dict = {}
        for i, row in self.patients_personal_data.iterrows():
            self.patients_dict[row['ID']] = {'Name': row['First Name'] + ' ' + row['Last Name'],
                                             'Gender': row['Gender'],
                                             'Age': row['Age']}

    def load_patients_personal_data(self, patients_csv_path='patients.csv'):
        """
        Loads patients personal data, and returns it with 2-d mapping between names and patients ids
        :param patients_csv_path:
        :return:
        """
        file_path = os.path.join(self.db_folder_path, patients_csv_path)
        patients_csv = pd.read_csv(file_path)

        id2name_map, name2id_map = {}, {}
        for i, row in patients_csv.iterrows():
            name = row['First Name'] + ' ' + row['Last Name']
            id = row['ID']
            id2name_map[id] = name
            name2id_map[name] = id
        return patients_csv, id2name_map, name2id_map

    def load_patients_medical_data(self, patients_data_path='patient_data.csv'):
        """
        Loads data from csv file
        :param patients_data_path:
        :return:
        """
        file_path = os.path.join(self.db_folder_path, patients_data_path)
        patients_data_csv = pd.read_csv(file_path)
        for col in patients_data_csv.columns:
            if 'Time' in col:
                try:
                    patients_data_csv[col] = pd.to_datetime(patients_data_csv[col])
                except:
                    patients_data_csv[col] = pd.to_datetime(patients_data_csv[col], format='%d/%m/%Y %H:%M')
        # Make sure deleted row is a boolean column
        patients_data_csv['Deleted'] = patients_data_csv['Deleted'].astype(bool)

        return patients_data_csv

    def load_loinc_data(self, loinc_csv_path='loinc_data.csv'):

        def convert_to_time_delta(in_str):
            days, hours, minutes = map(int, in_str.split(','))
            return timedelta(days=days, hours=hours, minutes=minutes)

        file_path = os.path.join(self.db_folder_path, loinc_csv_path)
        loinc_df = pd.read_csv(file_path)
        test2loincmap = {}
        for i, row in loinc_df.iterrows():
            test_name = row['name']
            loinc_id = row['id']
            test2loincmap[test_name] = loinc_id
        loinc_df['good_before'] = loinc_df['good_before'].apply(convert_to_time_delta)
        loinc_df['good_after'] = loinc_df['good_after'].apply(convert_to_time_delta)

        return loinc_df, test2loincmap

    def save_patients_medical_data(self, patients_data_path='patient_data.csv'):
        """
        Saves patients medical data back to csv
        :param patients_data_path:
        :return:
        """
        file_path = os.path.join(self.db_folder_path, patients_data_path)
        temp = self.patients_medical_data.copy()
        temp['Deleted'] = temp['Deleted'].astype(int)
        self.patients_medical_data.to_csv(file_path, index=False)

    def standartisize_datetime(self, date_str, hour_str='23:59'):
        """
        parses str hour and date to a date time format to enable usage of comperators
        """
        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
        if hour_str is not None:
            time_obj = datetime.strptime(hour_str, '%H:%M')
            datetime_obj = datetime.combine(date_obj.date(), time_obj.time())
        else:
            datetime_obj = date_obj
        return datetime_obj

    def standartisize_target_key(self, target_key):
        """
        A function to map the target to a loinc num if its a component or a test name
        :param target_key:
        :return:  loinc num
        """
        if target_key in self.test2loincmap:
            return self.test2loincmap[target_key]
        elif target_key in self.test2loincmap.values():
            return target_key
        else:
            raise KeyError('Loinc num or Test name provided is not in the DB.')

    def standartisize_patient(self, patient_name):
        """
        A function to standartize patient name to an indexed id
        :param patient_name:
        :return: A known patient ID
        """
        if patient_name in self.name2id_map:
            return self.name2id_map[patient_name]
        elif patient_name in self.id2name_map:
            return patient_name
        else:
            raise ValueError('Patient Name Unknown to System')

    def retrieve_patient_data(self, patient_name, target_key, target_date, pov_date, target_hour=None, pov_hour=None,
                              historic=False, prev_date='1.1.1990', prev_hour=None):
        """
        implements the function of "שאילתת אחזור"
        :param patient_name:
        :param target_key:
        :param target_date:
        :param pov_date:
        :param target_hour:
        :param pov_hour:
        :return:
        """
        if pov_hour is None:  # To retrieve the full day in case its was not supplied
            pov_hour = '23:59'
        if prev_hour is None:
            prev_hour = '00:00'  # To get the full day

        loinc_num = self.standartisize_target_key(target_key)
        patient_id = self.standartisize_patient(patient_name)
        target_datetime = self.standartisize_datetime(target_date, target_hour)


        # Creates a temporal view of the patients medical data
        if historic:
            prev_datetime = self.standartisize_datetime(prev_date, prev_hour)
            temporal_view = self.patients_medical_data[
                (self.patients_medical_data['Valid Start Time'] <= target_datetime) &
                (self.patients_medical_data['Valid Start Time'] >= prev_datetime)]
        else:
            pov_datetime = self.standartisize_datetime(pov_date, pov_hour)
            temporal_view = self.patients_medical_data[self.patients_medical_data['Transaction Time'] <= pov_datetime]
            # Removes deleted entries from non - historical retrieval
            temporal_view = temporal_view[~temporal_view['Deleted'].astype('bool')]
        patient_target_filtered_view = temporal_view[
            (temporal_view['Patient ID'] == patient_id) & (temporal_view['Test Name'] == loinc_num)]

        ## Returns only relevant scores
        if target_hour is not None:
            req_rows = patient_target_filtered_view[patient_target_filtered_view['Valid Start Time'] == target_datetime]
        else:
            if not historic:
                req_rows = patient_target_filtered_view[
                    (patient_target_filtered_view['Valid Start Time'] >= target_datetime) &
                    (patient_target_filtered_view['Valid Start Time'] <= self.standartisize_datetime(target_date))]
            else:
                req_rows = patient_target_filtered_view

        req_rows_sorted = req_rows.sort_values(by='Transaction Time', ascending=False)
        if historic:
            return req_rows_sorted
        else:
            return req_rows_sorted.head(1)

    def update_patient_data(self, patient_name, update_date, update_time, update_val,
                            target_key, target_date, target_time, mode='update'):
        # retrieve required measurment:
        current_date = datetime.now().strftime("%d.%m.%Y")
        current_time = datetime.now().strftime("%H:%M")
        logs = self.retrieve_patient_data(patient_name=patient_name,
                                          target_key=target_key,
                                          target_date=target_date,
                                          target_hour=target_time,
                                          pov_date=current_date,
                                          pov_hour=current_time)

        # Raise exception if no data exists for the parameters
        if len(logs) == 0:
            raise ValueError('No data exists for required test, patient and date')

        # Data exists
        index_to_update = logs.index[0]
        if mode == 'update':
            update_datetime = self.standartisize_datetime(update_date, update_time)
            # create a new row and Update values and transaction time
            new_row = self.patients_medical_data.iloc[index_to_update].copy()
            new_row['Value'] = update_val
            new_row['Transaction Time'] = update_datetime

            # insert new row
            self.patients_medical_data = pd.concat([self.patients_medical_data, pd.DataFrame([new_row])],
                                                   ignore_index=True)
            changed_row = self.patients_medical_data.iloc[-1].copy()
        elif mode == 'delete':
            # Changed the required row to be Deleted
            self.patients_medical_data.loc[index_to_update, 'Deleted'] = True
            changed_row = self.patients_medical_data.iloc[index_to_update].copy()

        # Save results
        self.save_patients_medical_data()

        # Retrieve the changed row with the corresponding index

        return changed_row

    def get_patients_valid_tests_for_timeframe(self, patient_name, target_date, target_time , use_pov = True):
        """
        retrieves all relevant logs for the patients for a specific time points, returns
        :param patient_name:
        :param target_date:
        :param target_time:
        :return:
        """

        def filter_by_timedelta(row):
            """
            Returns True if an entry is valid for current time , else False
            :param row: pandas series representing a test entry from the db
            :return:
            """
            if row['Test Name'].strip() not in self.test2loincmap.values():  # Filter out tests not known to system
                return False
            loinc_row = self.loinc_data[self.loinc_data['id'].str.strip() == row['Test Name'].strip()]

            good_after_delta = loinc_row['good_after'].values[0]
            good_before_delta = loinc_row['good_before'].values[0]

            return ((row['Valid Start Time'] + good_after_delta) >=
                    target_datetime >=
                    (row['Valid Start Time'] - good_before_delta) < target_datetime)

        patient_id = self.standartisize_patient(patient_name)
        target_datetime = self.standartisize_datetime(target_date, target_time)

        relevant_medical_data = self.patients_medical_data[~self.patients_medical_data['Deleted']
                                                           & (self.patients_medical_data['Patient ID'] == patient_id)]

        relevant_medical_data = relevant_medical_data[
            relevant_medical_data.apply(filter_by_timedelta, axis=1)]

        if use_pov:  # Use target time to only select past records
            relevant_medical_data = relevant_medical_data[relevant_medical_data['Transaction Time'] <= target_datetime]


        # Pick only the rows with the most updated test values
        recent_entries_per_exam_idx = relevant_medical_data.groupby('Test Name')['Valid Start Time'].idxmax()
        # Filter the DataFrame to keep only those rows
        recent_entries_per_exam_df = relevant_medical_data.loc[recent_entries_per_exam_idx]


        return recent_entries_per_exam_df

    def get_patients_names(self):
        return list(self.name2id_map.keys())

    def get_patients_ids(self):
        return list(self.id2name_map.keys())

    def get_test_names(self):
        return list(self.test2loincmap.keys())

    def get_loinc_ids(self):
        return list(self.test2loincmap.values())

    def get_patients_dict(self):
        return self.patients_dict.copy()

    def get_patient_earliest_entry(self , patient):
        """
        returns a timedate format with the patients first entry in the db
        :param patient: str, patient name or id
        :return: timedate , representing the date of the first entry of the patient in the medical db
        """
        patient_id = self.standartisize_patient(patient)
        patient_logs = self.patients_medical_data[self.patients_medical_data['Patient ID'] == patient_id]
        earliest_entry = patient_logs.sort_values(by='Valid Start Time', ascending=True).head(1)
        timestamp = pd.Timestamp(earliest_entry['Valid Start Time'].values[0])
        return timestamp.to_pydatetime()

    def get_patient_intervals(self, patient , unmerged = False):

        patient_id = self.standartisize_patient(patient)
        patient_logs = self.patients_medical_data[self.patients_medical_data['Patient ID'] == patient_id]
        tests_intervals = []
        for _, row in patient_logs.iterrows():
            if row['Test Name'].strip() not in self.test2loincmap.values():  # Filter out tests not known to system
                print('skipped ' , row['Test Name'].strip())
                continue
            loinc_row = self.loinc_data[self.loinc_data['id'].str.strip() == row['Test Name'].strip()]

            good_after_delta = loinc_row['good_after'].values[0]
            good_before_delta = loinc_row['good_before'].values[0]
            tests_intervals.append([(row['Valid Start Time'] -good_before_delta).to_pydatetime() , (row['Valid Start Time']+ good_after_delta).to_pydatetime()])

        if len(tests_intervals) == 0 :
            return tests_intervals

        sorted_intervals = sorted(tests_intervals, key=lambda x: x[0])

        if unmerged :
            return sorted_intervals
        merged_intervals = []

        current_start, current_end = sorted_intervals[0]

        for start, end in sorted_intervals[1:]:
            # If the current interval overlaps with the next one, merge them
            if start <= current_end:
                current_end = max(current_end, end)
            else:
                # No overlap, add the current interval and start a new one
                merged_intervals.append([current_start, current_end])
                current_start, current_end = start, end

        # Add the last interval
        merged_intervals.append([current_start, current_end])
        return merged_intervals

    def get_goodbefore_goodafter_df(self):

        new_df = self.loinc_data[['id' , 'good_before' , 'good_after']].copy()
        return new_df


# if __name__ == '__main__':
#     print('Db connector Testing Started')
#     conn = DBConnector(db_folder='.')
#     patients_personal_data, id2name, name2id = conn.load_patients_personal_data()
#     patients_data = conn.load_patients_medical_data()
    # print('Patients:')
    # print(patients_personal_data)
    # print('Maps:')
    # print(id2name)
    # print(name2id)
    #
    # print('Patients data ')
    # print(patients_data.head(10))
    # print(patients_data.tail(10))
    #
    # print('Testing functionality:')
    # patient_num = 'P015'
    # target_id = 'Fever'
    # target_date = '05.08.2024'
    # target_time = '9:00'
    # print('retrieving known patient single value:')
    # print(' should fetch one row:')
    # output = conn.retrieve_patient_data(patient_name=patient_num,
    #                                     target_key=target_id,
    #                                     target_date=target_date,
    #                                     target_hour=target_time,
    #                                     pov_date='05.08.2024',
    #                                     pov_hour='10:00')
    # print(output)
    # print(' should fetch no rows:')
    # output = conn.retrieve_patient_data(patient_name=patient_num,
    #                                     target_key=target_id,
    #                                     target_date=target_date,
    #                                     target_hour=target_time,
    #                                     pov_date='05.08.2024',
    #                                     pov_hour='09:00')
    # print(output)
    #
    # print('retrieving known patient historic value:')
    # print('should print 4 rows : ')
    # output = conn.retrieve_patient_data(patient_name=patient_num,
    #                                     target_key=target_id,
    #                                     target_date=target_date,
    #                                     pov_date='05.08.2024',
    #                                     pov_hour='10:00',
    #                                     historic=True)
    # print(output)
    # # print('trying to acess unknown patient ')
    # try:
    #     output = conn.retrieve_patient_data(patient_name='P016',
    #                                         target_key=target_id,
    #                                         target_date=target_date,
    #                                         pov_date='05.08.2024',
    #                                         pov_hour='10:00',
    #                                         historic=True)
    # except Exception as e:
    #     print('Exception occured! : ', e)
    #
    # conn.update_patient_data(patient_name=patient_num,
    #                          target_key=target_id,
    #                          target_date=target_date,
    #                          target_time=target_time,
    #                          update_date='20.12.2024',
    #                          update_time='11:40',
    #                          update_val=15)
    #
    # print('Retrieving all exams for patient in a specific time:')
    # res = conn.get_patients_valid_tests_for_timeframe(patient_name=patient_num,
    #                                                   target_date='01.08.2024',
    #                                                   target_time='07:00',
    #                                                   use_pov = False)
    # print(res)

    # datetime_out = conn.get_patient_earliest_entry('P015')
    # print(datetime_out)
    # print(type(datetime_out))
