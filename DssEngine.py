from dbconnector import DBConnector
from build_ontology import *
from datetime import datetime , timedelta
import numpy as np

class DSSEngine:
    def __init__(self , db_folder = '.' , ontology_folder = '.'):
        """
        Initializes a new DSS engine instance, capable of connecting to a db and knowledge base.

        """
        self.db_con = DBConnector(db_folder)
        self.ontology = get_ontology(os.path.join(ontology_folder,"cdss.owl")).load()

        # NOY : I've Decided that the Engine should only handle the names of patients and tests, no codes or IDS.
        self.patient_list = self.db_con.get_patients_names()
        self.test_list = self.db_con.get_test_names()


    def retrival_query(self ,target , patient , date , pov_date, hour = None , pov_hour = None ):
        """
        recieves parameters for a query to be retrived from the db
        :param target: str , FULL string of test or loinc number
        :param patient: str , name or id of the patient in the db
        :param date: str , date of item to retrieve
        :param perc_date: str , perceived date, filter the database from newer entries
        :param hour: str, hour of item to retrive - if None retrieves the most recent daily enry
        :param perc_hour: str, percieved hour to filter the database by. if nonexistant - 23:59
        :return:
        """

        ## date should be formatted  -  %d.%m.%Y
        ## Hours should be formatted  -  %H:%M

        ## If its not, convert it here

        return self.db_con.retrieve_patient_data(patient_name=patient,
                                                 target_key=target,
                                                 target_date=date,
                                                 target_hour = hour,
                                                 pov_date=pov_date,
                                                 pov_hour=pov_hour)

    def retrival_historic_query(self ,target , patient , date ,prev_date, hour = None, prev_hour= None ):
        """
         recieves parameters for a query to be retrived from the db
         :param target: str , FULL string of test or loinc number
         :param patient: str , name or id of the patient in the db
         :param date: str , date of item to retrieve
         :param perc_date: str , perceived date, filter the database from newer entries
         :param hour: str, hour of item to retrive - if None retrieves the most recent daily enry
         :param perc_hour: str, percieved hour to filter the database by. if nonexistant - 23:59
         :param prev_date: str, the earliest date to retrieve records from
         :param prev_hour: str, hour corresponding to the earliest date
         :return: retrieves all records documented for patient - INCLUDING DELETED RECORDS!
         """

        ## date should be formatted  -  %d.%m.%Y
        ## Hours should be formatted  -  %H:%M

        ## If its not, convert it here

        return self.db_con.retrieve_patient_data(patient_name=patient,
                                                 target_key=target,
                                                 target_date=date,
                                                 target_hour=hour,
                                                 pov_date=None,
                                                 pov_hour=None,
                                                 prev_date= prev_date,
                                                 prev_hour = prev_hour,
                                                 historic =True )
    def update_query(self, patient, target, measure_date, measure_time , update_date , update_time , updated_value):
        """
        Updates an existing value in the db, creates a *new* row with the new value updated in the specific transaction time.
         :param target: str , FULL string of test or loinc number of the measurement
         :param patient: str , name or id of the patient in the db
        :param measure_date: str formatted 'DD.MM.YYYY', date of the measurement
        :param measure_time: str formatted 'HH:MM' , time of the measurement
        :param update_date: str formatted 'DD.MM.YYYY', update date of the measurement
        :param update_time: str formatted 'HH:MM' , update time of the measurement
        :param updated_value: any , new value to be inserted
        :return: updated rows, or a string indicating no measurment exists for corresponding date
        """

        try:
            changed_row = self.db_con.update_patient_data(patient_name = patient,
                                    target_key =target,
                                     target_date = measure_date,
                                     target_time =measure_time,
                                     update_date = update_date,
                                     update_time = update_time,
                                     update_val = updated_value,
                                     mode = 'update' )
        except ValueError:  #
            return f'No entries found for {patient} and test {target} for the specified date'

        else:
            return changed_row

    def delete_query(self, patient, target, measure_date, measure_time ,):
        """
        Deletes  an existing entry in the db, while keeping it in the DB for historic retrival.
         :param target: str , FULL string of test or loinc number of the measurement
         :param patient: str , name or id of the patient in the db
        :param measure_date: str formatted 'DD.MM.YYYY', date of the measurement
        :param measure_time: str formatted 'HH:MM' , time of the measurement
        :return: deleted row, or a string indicating no measurment exists for corresponding date
        """

        try:
            changed_row = self.db_con.update_patient_data(patient_name = patient,
                                    target_key =target,
                                     target_date = measure_date,
                                     target_time =measure_time,
                                     update_date = None,
                                     update_time = None,
                                     update_val = None,
                                     mode = 'delete' )
        except ValueError:  #
            return f'No entries found for {patient} and test {target} for the specified date'

        else:
            return changed_row

    def retrieve_relevant_tests_for_patient(self, patient, req_date, req_hour, use_pov = True):
        """
        Retrieves all valid logs relevant to the patient from the db, for a set point in time
        :param patient: str, patient full name or Patient ID from the db
        :param req_date: str, date format (DD.MM.YYYY) to retrieve patient data
        :param req_hour: str, hour format HH:MM to retrieve patient data
        :param use_pov: boolean , if True than req_date and req_time are used as filters. if false, retrieves future tests as well
        :return: logs of relevant tests for the patient
        """
        patients_data_entries = self.db_con.get_patients_valid_tests_for_timeframe(patient_name=patient,
                                                                                   target_time= req_hour,
                                                                                   target_date = req_date ,
                                                                                   use_pov = use_pov)
        # Use them for inference here
        return patients_data_entries

    def infer_patients_states_for_timepoint(self , req_time_data, single_patient_id = None):
        """
        Function to return the states of all patients in the db for a current point in time.
        req_time_data should be converted to the retrieve_relevant_tests... function input!
        :param req_time_data: either a string received from the webapp or a datetime object
        :param single_patient_id : str, representing a single patient to check. otherwise None
        :return: dictionary in the form of {patient_name : State}
        """
        # Assuming req_time_date is formatted : '%Y-%m-%d %H:%M:%S'
        if isinstance(req_time_data , str):
            req_datetime = datetime.strptime(req_time_data, '%d.%m.%Y %H:%M')
        else:
            req_datetime = req_time_data
        req_date, req_hour =req_datetime.strftime('%d.%m.%Y') , req_datetime.strftime('%H:%M')
        res_dict = {}



        # Enables support for a single patient retrival
        patients_dict = {}

        if single_patient_id is None:
            patients_dict = self.db_con.get_patients_dict()
        else:
            pid = self.db_con.standartisize_patient(single_patient_id)
            patients_dict[pid] = self.db_con.get_patients_dict()[pid]

        # Retrieve patients states for all the required patients
        for pid , p_dict in patients_dict.items():
            cur_patient = self.ontology.Patient(f"Patient_{pid}")
            cur_patient.gender = [p_dict['Gender']]

            # Retrieve the tests for the patient
            if single_patient_id is None: # If not a single patient is specified, we filter the db using date and time
                most_recent_tests_logs = self.retrieve_relevant_tests_for_patient(pid ,req_date, req_hour, use_pov = False)
            else: # If we check for a single patient - retrieve future relevant test results as well
                most_recent_tests_logs = self.retrieve_relevant_tests_for_patient(pid, req_date, req_hour, use_pov=False)
            patients_test_scores = {}


            for i,row in most_recent_tests_logs.iterrows():
                patients_test_scores[row['Test Name']] = row['Value']

            # insert test data into patient instance
            if '718-7' in patients_test_scores:
                cur_patient.hemoglobin_level = [float(patients_test_scores['718-7'])]
            if '53286-1' in patients_test_scores:
                cur_patient.wbc_level = [float(patients_test_scores['53286-1'])]

            # Create new symptom
            symptom = self.ontology.Symptom(f"Symptom_{pid}")
            any_symptom = False
            if '386661006' in patients_test_scores:
                symptom.fever = [float(patients_test_scores['386661006'])]
                any_symptom = True
            if '43724002' in patients_test_scores:
                symptom.chills = [patients_test_scores['43724002']]
                any_symptom = True
            if '243865006' in patients_test_scores:
                symptom.allergic_state = [patients_test_scores['243865006']]
                any_symptom = True
            if '185823004' in  patients_test_scores:
                symptom.skin_look = [patients_test_scores['185823004']]
                any_symptom = True
            if any_symptom:
                cur_patient.has_symptom = [symptom]

            res_dict[pid] = p_dict.copy() # contains the patients name, age and gender
            try:
                hemoglobin_state = determine_hemoglobin_state(cur_patient)
                cur_patient.has_hemoglobin_state = [hemoglobin_state]
                res_dict[pid]["Hemoglobin State"] = hemoglobin_state.name
            except ValueError as e:
                res_dict[pid]["Hemoglobin State"] = f"Error: {str(e)}"

            try:
                hematological_state = determine_hematological_state(cur_patient)
                cur_patient.has_hematological_state = [hematological_state]
                res_dict[pid]["Hematological State"] = hematological_state.name
            except ValueError as e:
                res_dict[pid]["Hematological State"] = f"Error: {str(e)}"

            try:
                systemic_toxicity = determine_systemic_toxicity(cur_patient)
                cur_patient.has_systemic_toxicity = [systemic_toxicity]
                res_dict[pid]["Systemic Toxicity"] = systemic_toxicity.name
            except ValueError as e:
                res_dict[pid]["Systemic Toxicity"] = f"Error: {str(e)}"

            try:
                treatment = determine_treatment(cur_patient)
                cur_patient.has_treatment = [treatment]
                res_dict[pid]["Treatment"] = treatment.name
            except ValueError as e:
                res_dict[pid]["Treatment"] = f"Error: {str(e)}"

            # Delete the Patient instance
            destroy_entity(cur_patient)
            destroy_entity(symptom)

        return res_dict

    def retrieve_state_intervals(self , patient, state):
        try:
            patient_intervals = self.db_con.get_patient_intervals(patient , unmerged = True)
        except:
            print('Patient Name was not found in db! ')
            return

        if len(patient_intervals) == 0 :
            return []

        flatten_timepoints = list(itertools.chain(*patient_intervals))
        sorted_unique_timepoints = sorted(set(flatten_timepoints))

        intervals_dict = {}
        cur_state_value = 'No condition'  # set to represent a patient has no possible value for the state
        OPEN_INTERVAL_EXISTS = False

        for timepoint in sorted_unique_timepoints:
            prev_state_value = cur_state_value
            try :
                patient_dict = self.infer_patients_states_for_timepoint(single_patient_id=patient,
                                                                        req_time_data=timepoint)
            except:
                patient_dict = {patient : {}}
                print(f'Exception has occured on {timepoint}')

            patient_symptoms = list(patient_dict.values())[0]
            # Check for condition:
            cur_state_value = patient_symptoms.get(state, 'No condition')
            if cur_state_value == prev_state_value:
                    # If the current state equal the prev state, no need to do anything.
                    continue
            else:  # Current state is different from the previous state

                if OPEN_INTERVAL_EXISTS : # The previous state was a valid state, close the previous interval
                    intervals_dict[prev_state_value][-1].append(timepoint)

                # If the current state is valid, we will create a new interval.
                if 'Error' in cur_state_value :
                    OPEN_INTERVAL_EXISTS = False
                else:  # Create a new interval
                    # Initializes a new list if it is the first interval for the state value
                    intervals_dict[cur_state_value] = intervals_dict.get(cur_state_value, [])
                    intervals_dict[cur_state_value].append([timepoint])
                    OPEN_INTERVAL_EXISTS = True


        for state_value , intervals in intervals_dict.items():
            # Might happen that the last interval remains open
            if len(intervals[-1]) == 1 :
                intervals[-1].append(timepoint)

        return intervals_dict

    # def retrieve_interval_for_patient(self, patient, test_name, required_value):
    #     """
    #     Checks patient's test values across all medical logs, and retrives a list of time intervals where the patient
    #     had the required value for the test provided
    #     :param patient: str, id or name of patient
    #     :param test_name: str, name of condition to check status for
    #     :param required_value: str, value required for specific condition
    #     :return: list of datetime tuples [(start time, end time),.. ] representing time intervals when the patient was
    #     diagnosed with the condition
    #     """
    #
    #     # Check if patient is in system, and retrieve it's earliest entry date
    #     try:
    #         start_date = self.db_con.get_patient_earliest_entry(patient)
    #     except:
    #         print('Patient Name was not found in db!')
    #         return
    #     # Initialize an output list for intervals
    #     time_intervals_list = []
    #     end_date = datetime.now()
    #     time_step = timedelta(minutes = 60)  # Changes sampling step size
    #     cur_date = start_date
    #
    #     OPEN_INTERVAL = False
    #     # Iterate over all step points within the possible range of first entry date and current date
    #     while cur_date <= end_date:
    #
    #         # Check tha patient diagnosis dictionary for the timestamp
    #         try : ## Owl raises a weird exception
    #             patient_dict = self.infer_patients_states_for_timepoint(single_patient_id=patient,
    #                                                                     req_time_data=cur_date)
    #         except:
    #             patient_dict = {patient : {}}
    #             print(f'Exception has occured on {cur_date}')
    #
    #         patient_symptoms = list(patient_dict.values())[0]
    #         # Check for condition:
    #         if patient_symptoms.get(test_name, None) == required_value:
    #             # If condition exists a new interval will be opened, else we will continue to next time step
    #             if not OPEN_INTERVAL:
    #                 # Open a new interval
    #                 print(f'Opened interval : {cur_date}')
    #                 time_intervals_list.append([cur_date])
    #                 OPEN_INTERVAL = True
    #         else:  # Condition does not exist, close last interval if open, otherwise continue
    #             if OPEN_INTERVAL:
    #                 # Close last interval by appending the last timepoint to it
    #                 print(f'closed interval : {cur_date- time_step}')
    #                 time_intervals_list[-1].append(cur_date - time_step)
    #                 OPEN_INTERVAL = False
    #         # Increment timestamp by time step - 1 minute.
    #         cur_date += time_step
    #
    #     # Return the resulting lists, containing the time intervals
    #     return time_intervals_list
    #
    # def retrieve_interval_for_patient2(self, patient, condition_name, required_value):
    #     """
    #     Checks patient's condition across all medical logs, and retrieves a list of time intervals
    #     where the patient had the required value for the condition provided
    #     """
    #     # Get the patient's earliest entry date and current date
    #     start_date = self.db_con.get_patient_earliest_entry(patient)
    #     end_date = datetime.now()
    #
    #     # Retrieve all relevant data for the patient
    #     patient_data = self.db_con.patients_medical_data[
    #         (self.db_con.patients_medical_data['Patient ID'] == self.db_con.standartisize_patient(patient)) &
    #         (self.db_con.patients_medical_data['Valid Start Time'] >= start_date) &
    #         (self.db_con.patients_medical_data['Valid Start Time'] <= end_date)
    #         ]
    #
    #     # Sort the data by timestamp
    #     patient_data = patient_data.sort_values('Valid Start Time')
    #
    #     # Initialize variables to track intervals
    #     intervals = []
    #     interval_start = None
    #     prev_state = None
    #
    #     # Iterate through each day from start_date to end_date
    #     current_date = start_date.date()
    #     while current_date <= end_date.date():
    #         # Get the patient's state for the current date
    #         current_datetime = datetime.combine(current_date, datetime.min.time())
    #         try:
    #             patient_state = self.infer_patients_states_for_timepoint(current_datetime, single_patient_id=patient)
    #             current_value = patient_state[self.db_con.standartisize_patient(patient)].get(condition_name)
    #         except Exception as e:
    #             print(f"Error inferring state for {current_date}: {str(e)}")
    #             current_value = None
    #
    #         if current_value == required_value and prev_state != required_value:
    #             interval_start = current_datetime
    #         elif (current_value != required_value or current_date == end_date.date()) and prev_state == required_value:
    #             if interval_start:
    #                 intervals.append([interval_start, current_datetime - timedelta(minutes=1)])
    #                 interval_start = None
    #
    #         prev_state = current_value
    #         current_date += timedelta(days=1)
    #
    #     return intervals


if __name__ == "__main__":
    dss = DSSEngine()
    patient_name = 'James Smith'
    target_date = '05.08.2024'
    target_time = '9:00'
    target = '718-7'

    #  ## Retrival tests
    #
    # logs = dss.retrival_query(patient = patient_name,
    #                           target = target,
    #                           date = target_date,
    #                           hour = target_time,
    #                           pov_date = '05.08.2024')
    # assert(len(logs) == 1 )
    #
    # logs = dss.retrival_query(patient = patient_name,
    #                           target = target,
    #                           date = target_date,
    #                           hour = target_time,
    #                           pov_date = '05.08.2024',
    #                           pov_hour = '09:12')
    # assert(len(logs) == 0 )
    #
    #
    # ## Historic Retrival tests
    #
    # logs = dss.retrival_historic_query(patient = patient_name,
    #                           target = target,
    #                           date = '01.10.2024',
    #                           pov_date = '05.10.2024',
    #                           prev_date = '01.07.2024',
    #                                    )
    # print(logs)
    # # assert(len(logs) == 7 )
    #
    # Update and deletion test:
    # Update the latest entry to 300
    # logs = dss.update_query(patient = patient_name,
    #                         target = target,
    #                         measure_date= '22.08.2024',
    #                         measure_time= '07:30',
    #                         update_date= '09.09.2024',
    #                         update_time= '13:00',
    #                         updated_value= 666)
    #
    # print(logs)
     # Delete latest entry
    # logs = dss.delete_query(patient = patient_name,
    #                         target = target,
    #                         measure_date= '20.08.2024',
    #                         measure_time= '09:30')
    # print(logs)

    # print('retrieve history after updates:')
    # print(dss.retrival_historic_query(patient = patient_name,
    #                           target = target,
    #                           date = '01.10.2024',
    #                           prev_date = '01.07.2024',
    #                                    ))
    #
    # # Test interval for given condition and state
    # condition_name = 'Systemic Toxicity'
    # condition_value = 'Grade_I'
    # time_start = datetime.now()
    # interval_list = dss.retrieve_interval_for_patient( patient_name, condition_name, condition_value)
    # time_taken = datetime.now() - time_start
    # print(f'Operation took : {time_taken}  sec , sampling once every 60 minutes')
    # print(interval_list)
    #
    # Test interval for given condition and state
    # condition_name = 'Systemic Toxicity'
    # condition_value = 'Grade_I'
    # time_start = datetime.now()
    # interval_list = dss.retrieve_interval_for_patient2(patient_name, condition_name, condition_value)
    # time_taken = datetime.now() - time_start
    # print(f'Operation took : {time_taken}  sec , sampling once every 60 minutes')
    # print(interval_list)

    # Test for infer_patients_states_for_timepoint
    # logs = dss.infer_patients_states_for_timepoint('30.08.2024 09:30')
    # print(logs)

    condition_name = 'Hematological State'
    time_start = datetime.now()
    state_intervals = dss.retrieve_state_intervals(patient_name, condition_name)
    time_taken = datetime.now() - time_start
    print(f'Operation took : {time_taken}  sec , sampling once every 60 minutes')
    print(state_intervals)

