import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time
from DssEngine import DSSEngine
import plotly.graph_objects as go
import random
import pytz


# Load data
dss = DSSEngine()
patients_df = dss.db_con.patients_personal_data    #pd.read_csv('patients.csv')
observations_df = dss.db_con.patients_medical_data #pd.read_csv('patient_data.csv', na_values=["NA", "N/A", ""], keep_default_na=False)
loinc_data = dss.db_con.loinc_data     #pd.read_csv('loinc_data.csv')

local_tz = pytz.timezone('Asia/Jerusalem')


st.markdown("""
<style>
p {
    line-height: 1;
    margin-bottom: 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .stRadio [role=radiogroup] {
        align-items: flex-start;
        justify-content: flex-start;
    }
    .stRadio [role=radio] {
        width: auto;
        padding-right: 10px;
    }
    [data-testid=stSidebar] [role=radiogroup] {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    [data-testid=stSidebar] [role=radio] {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def replace_errors_with_not_found(dict_data):
    for id_patient, data_patient in dict_data.items():
        for key, value in data_patient.items():
            if isinstance(value, str) and value.startswith("Error:"):
                data_patient[key] = "Not Found"
    return dict_data

def get_patient_id_from_name(full_name):
    first_name, last_name = full_name.split(' ', 1)
    patient = patients_df[(patients_df['First Name'] == first_name) & (patients_df['Last Name'] == last_name)]
    return patient['ID'].values[0] if not patient.empty else None


def get_test_info(test_id):
    # Ensure loinc_data is loaded and available in the scope
    test_info = loinc_data[loinc_data['id'] == test_id]

    if not test_info.empty:
        name = test_info['name'].values[0]
        units = test_info['units'].values[0]
        return name, units
    else:
        return "Test not found", "N/A"

st.title('Clinical Decision Support System')

# Sidebar for function selection
function_choice = st.sidebar.radio("Select Function", ["Get Test Value", "Get Test History", "Update Test Value", "Delete Test Value", "Get Patients States", "Get State Intervals", "Update Good Before/After"])

if function_choice == "Get Test Value":
    st.header("Get Test Value")

    # Allow user to choose between ID and Full Name
    col1, col2 = st.columns([1, 4])

    with col1:
        patient_selection_method = st.radio("Select patient by:", ["ID", "Full Name"])

    with col2:
        if patient_selection_method == "ID":
            patient_id = st.selectbox('Select Patient ID', patients_df['ID'].unique())
        else:
            full_names = [f"{row['First Name']} {row['Last Name']}" for _, row in patients_df.iterrows()]
            selected_name = st.selectbox('Select Patient Name', full_names)
            patient_id = get_patient_id_from_name(selected_name)

    col3, col4 = st.columns([1, 4])

    with col3:
        test_selection_method = st.radio("Select test by:", ["ID", "Name"])

    with col4:
        if test_selection_method == "ID":
            test_choice = st.selectbox('Select Test ID', loinc_data['id'].unique())
        else:
            test_choice = st.selectbox('Select Test Name', loinc_data['name2'].unique())
            test_choice = loinc_data[loinc_data['name2'] == test_choice]['id'].values[0]
    default_date = datetime.now(local_tz).date()
    value_date = st.date_input('Value Date', value=default_date).strftime("%d.%m.%Y")
    value_time = st.time_input('Value Time', value=None)
    if value_time:
        value_time = value_time.strftime("%H:%M")

    default_date = datetime.now(local_tz).date()
    query_date = st.date_input('Query Date', value=default_date).strftime("%d.%m.%Y")
    default_time = datetime.now(local_tz).time()
    query_time = st.time_input('Query Time', value=default_time)
    if query_time:
        query_time = query_time.strftime("%H:%M")

    if st.button('Get Test Value'):
        result = dss.retrival_query(test_choice, patient_id, value_date, query_date, value_time, query_time)
        result = pd.DataFrame(result).reset_index(drop=True)
        if result.empty:
            st.write("No results found for the specified patient, test and time")
        else:
            test_name, units = get_test_info(test_choice)
            st.write(f"Lonic Full Name: {test_name}")
            st.divider()
            st.table(pd.DataFrame(result).reset_index(drop=True))


elif function_choice == "Get Test History":
    st.header("Get Test History")
    # Allow user to choose between ID and Full Name
    col1, col2 = st.columns([1, 4])

    with col1:
        patient_selection_method = st.radio("Select patient by:", ["ID", "Full Name"])

    with col2:
        if patient_selection_method == "ID":
            patient_id = st.selectbox('Select Patient ID', patients_df['ID'].unique())
        else:
            full_names = [f"{row['First Name']} {row['Last Name']}" for _, row in patients_df.iterrows()]
            selected_name = st.selectbox('Select Patient Name', full_names)
            patient_id = get_patient_id_from_name(selected_name)

    col3, col4 = st.columns([1, 4])

    with col3:
        test_selection_method = st.radio("Select test by:", ["ID", "Name"])

    with col4:
        if test_selection_method == "ID":
            test_choice = st.selectbox('Select Test ID', loinc_data['id'].unique())
        else:
            test_choice = st.selectbox('Select Test Name', loinc_data['name2'].unique())
            test_choice = loinc_data[loinc_data['name2'] == test_choice]['id'].values[0]
    default_date = datetime.now(local_tz).date()
    start_date = st.date_input('Start Date', value=default_date).strftime("%d.%m.%Y")
    start_time = st.time_input('Start Time', value=None)
    if start_time:
        start_time = start_time.strftime("%H:%M")

    end_date = st.date_input('End Date', value=default_date).strftime("%d.%m.%Y")
    end_time = st.time_input('End Time', value=None)
    if end_time:
        end_time = end_time.strftime("%H:%M")

    if st.button('Get Test History'):
        result = dss.retrival_historic_query(test_choice, patient_id, end_date, start_date, end_time, start_time)
        result = pd.DataFrame(result).reset_index(drop=True)
        if result.empty:
            st.write("No results found for the specified patient, test and time")
        else:
            test_name, units = get_test_info(test_choice)
            st.write(f"Lonic Full Name: {test_name}")
            st.divider()
            st.table(pd.DataFrame(result).reset_index(drop=True))

elif function_choice == "Update Test Value":
    st.header("Update Test Value")
    # Allow user to choose between ID and Full Name
    col1, col2 = st.columns([1, 4])

    with col1:
        patient_selection_method = st.radio("Select patient by:", ["ID", "Full Name"])

    with col2:
        if patient_selection_method == "ID":
            patient_id = st.selectbox('Select Patient ID', patients_df['ID'].unique())
        else:
            full_names = [f"{row['First Name']} {row['Last Name']}" for _, row in patients_df.iterrows()]
            selected_name = st.selectbox('Select Patient Name', full_names)
            patient_id = get_patient_id_from_name(selected_name)

    col3, col4 = st.columns([1, 4])

    with col3:
        test_selection_method = st.radio("Select test by:", ["ID", "Name"])

    with col4:
        if test_selection_method == "ID":
            test_choice = st.selectbox('Select Test ID', loinc_data['id'].unique())
        else:
            test_choice = st.selectbox('Select Test Name', loinc_data['name2'].unique())
            test_choice = loinc_data[loinc_data['name2'] == test_choice]['id'].values[0]
    default_date = datetime.now(local_tz).date()
    measure_date = st.date_input('Measurement Date', value=default_date).strftime("%d.%m.%Y")
    measure_time = st.time_input('Measurement Time', value=None)
    if measure_time:
        measure_time = measure_time.strftime("%H:%M")

    update_date = st.date_input('Update Date', value=default_date).strftime("%d.%m.%Y")
    default_time = datetime.now(local_tz).time()
    update_time = st.time_input('Update Time', value=default_time)
    if update_time:
        update_time = update_time.strftime("%H:%M")

    updated_value = st.number_input('Updated Value', step=0.1)

    if st.button('Update Test Value'):
        result = dss.update_query(patient_id, test_choice, measure_date, measure_time, update_date, update_time,
                                  updated_value)
        if isinstance(result, pd.DataFrame):
            st.table(result)
        else:
            st.write(result)

elif function_choice == "Delete Test Value":
    st.header("Delete Test Value")
    # Allow user to choose between ID and Full Name
    col1, col2 = st.columns([1, 4])

    with col1:
        patient_selection_method = st.radio("Select patient by:", ["ID", "Full Name"])

    with col2:
        if patient_selection_method == "ID":
            patient_id = st.selectbox('Select Patient ID', patients_df['ID'].unique())
        else:
            full_names = [f"{row['First Name']} {row['Last Name']}" for _, row in patients_df.iterrows()]
            selected_name = st.selectbox('Select Patient Name', full_names)
            patient_id = get_patient_id_from_name(selected_name)

    col3, col4 = st.columns([1, 4])

    with col3:
        test_selection_method = st.radio("Select test by:", ["ID", "Name"])

    with col4:
        if test_selection_method == "ID":
            test_choice = st.selectbox('Select Test ID', loinc_data['id'].unique())
        else:
            test_choice = st.selectbox('Select Test Name', loinc_data['name2'].unique())
            test_choice = loinc_data[loinc_data['name2'] == test_choice]['id'].values[0]
    default_date = datetime.now(local_tz).date()
    measure_date = st.date_input('Measurement Date', value=default_date).strftime("%d.%m.%Y")
    measure_time = st.time_input('Measurement Time', value=None)
    if measure_time:
        measure_time = measure_time.strftime("%H:%M")

    if st.button('Delete Test Value'):
        result = dss.delete_query(patient_id, test_choice, measure_date, measure_time)
        if isinstance(result, pd.DataFrame):
            st.table(result)
        else:
            st.write(result)

elif function_choice == "Get Patients States":
    st.header("Get Patients States")

    default_date = datetime.now(local_tz).date()
    state_date = st.date_input('Date', value=default_date)
    state_time = st.time_input('Time', time(0, 0))
    state_datetime = datetime.combine(state_date, state_time)


    def count_not_found(patient_data):
        return sum(1 for value in patient_data.values() if value == 'Not Found')


    def sort_patients(states, sort_option):
        if sort_option == "ID":
            return sorted(states.items(), key=lambda x: x[0])
        else:  # sort by completeness of data
            return sorted(states.items(), key=lambda x: (count_not_found(x[1]), x[0]))

    # Add sorting option
    sort_option = st.radio("Sort patients by:", ["ID", "Known States"], horizontal=True)

    if st.button('Get Patient States'):
        states = dss.infer_patients_states_for_timepoint(state_datetime.strftime('%d.%m.%Y %H:%M'))
        states = replace_errors_with_not_found(states)
        popup_patients = []

        if not states:
            st.warning("No states returned. Please check the input date and time.")
        else:

            # Sort the patients based on the selected option
            sorted_patients = sort_patients(states, sort_option)

            # Create a 3-column layout
            col1, col2, col3 = st.columns(3)

            # Distribute patient boxes across columns
            for i, (patient_id, patient_data) in enumerate(sorted_patients):
                with [col1, col2, col3][i % 3]:
                    treatment_full = patient_data.get("Treatment", "")
                    treatment_parts = treatment_full.split(maxsplit=1)

                    if len(treatment_parts) > 1:
                        treatment_header = treatment_parts[0]
                        patient_data["Treatment"] = treatment_parts[1]
                    else:
                        treatment_header = treatment_full
                        patient_data["Treatment"] = ""

                    footer = st.container()
                    if treatment_header in ["M_I", "F_I"]:
                        st.subheader(f":green[Patient {patient_id}]", anchor=False)
                    elif treatment_header in ["M_II", "F_II", "M_III", "F_III"]:
                        st.subheader(f":orange[Patient {patient_id}]", anchor=False)
                    elif treatment_header in ["M_IV", "F_IV", "M_V", "F_V"]:
                        st.subheader(f":red[Patient {patient_id}]", anchor=False)
                        if treatment_header in ["M_V", "F_V"]:
                            st.warning(f'Call the family!', icon="⚠️")

                    else:
                        patient_data["Treatment"] = treatment_full
                        st.subheader(f"Patient {patient_id}", anchor=False)
                    for key, value in patient_data.items():
                        if isinstance(value, str):
                            value = value.replace("_", " ")
                        st.write(f"**{key}:** {value}")
                    st.write("---")

elif function_choice == "Get State Intervals":
    st.header("Get State Intervals")


    def plot_state_intervals(intervals, patient_id, state_choice):
        fig = go.Figure()
        states = list(intervals.keys())

        # Define correct sorting orders for each state type
        sorting_orders = {
            "Hemoglobin State": ["Severe_Anemia", "Moderate_Anemia", "Mild_Anemia", "Normal_Hemoglobin",
                                 "Polycythemia"],
            "Hematological State": ["Pancytopenia", "Leukopenia", "Anemia", "Suspected_Leukemia",
                                    "Normal_Hematological", "Leukemoid_Reaction", "Suspected_Polycythemia_Vera",
                                    "Polyhemia"],
            "Systemic Toxicity": ["Grade_IV", "Grade_III", "Grade_II", "Grade_I"]  # Reversed order as requested
        }

        # Sort the states based on the custom order
        sorted_states = sorted(states, key=lambda x: sorting_orders[state_choice].index(x) if x in sorting_orders[
            state_choice] else len(sorting_orders[state_choice]))
        num_states = len(sorted_states)

        # Generate random colors for each state
        colors = {state: f'rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})' for state
                  in sorted_states}

        for i, state in enumerate(sorted_states):
            time_ranges = intervals[state]
            # Calculate the y-position for each state (first state at the top)
            y_position = 1 - (i + 0.5) / num_states

            for start, end in time_ranges:
                fig.add_trace(go.Scatter(
                    x=[start, end, None],  # Add None to create a gap between segments
                    y=[y_position, y_position, None],
                    mode='lines',
                    line=dict(color=colors[state], width=10),
                    name=state.replace('_', ' '),
                    hoverinfo='text',
                    text=f"{state.replace('_', ' ')}<br>Start: {start}<br>End: {end}",
                    showlegend=False
                ))

        fig.update_layout(
            title=f"Patient {patient_id} - {state_choice} Intervals",
            xaxis_title="Time",
            yaxis=dict(
                title="States",
                tickmode='array',
                tickvals=[1 - (i + 0.5) / num_states for i in range(num_states)],
                ticktext=[state.replace('_', ' ') for state in sorted_states],
                range=[-0.1, 1.1]  # Extend the range slightly to show full lines
            ),
            height=400,
            margin=dict(l=0, r=0, t=40, b=0)
        )

        return fig


    # Allow user to choose between ID and Full Name
    col1, col2 = st.columns([1, 4])
    with col1:
        patient_selection_method = st.radio("Select patient by:", ["ID", "Full Name"])
    with col2:
        if patient_selection_method == "ID":
            patient_id = st.selectbox('Select Patient ID', patients_df['ID'].unique())
        else:
            full_names = [f"{row['First Name']} {row['Last Name']}" for _, row in patients_df.iterrows()]
            selected_name = st.selectbox('Select Patient Name', full_names)
            patient_id = get_patient_id_from_name(selected_name)

    state_choice = st.selectbox('Select State', ["Hemoglobin State", "Hematological State", "Systemic Toxicity"])

    if st.button('Get State Intervals'):
        intervals = dss.retrieve_state_intervals(patient_id, state_choice)

        if intervals:
            fig = plot_state_intervals(intervals, patient_id, state_choice)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No intervals found for the specified patient and state.")

elif function_choice == "Update Good Before/After":
    # Convert numpy.timedelta64 to days, hours, minutes
    def timedelta_to_dhm(td):
        days = td.astype('timedelta64[D]').astype(int)
        hours = (td - np.timedelta64(days, 'D')).astype('timedelta64[h]').astype(int)
        minutes = (td - np.timedelta64(days, 'D') - np.timedelta64(hours, 'h')).astype('timedelta64[m]').astype(int)
        return days, hours, minutes
    st.header("Update Good Before/After")

    # Password protection
    password = st.text_input("Enter password", type="password")
    if password:  # Only check the password if the user has entered something
        if password != "admin":  # Replace with your actual password
            st.error("Incorrect password. Access denied.", icon="🚨")
        else:
            # Test selection
            col1, col2 = st.columns([1, 4])
            with col1:
                test_selection_method = st.radio("Select test by:", ["ID", "Name"])
            with col2:
                if test_selection_method == "ID":
                    test_choice = st.selectbox('Select Test ID', loinc_data['id'].unique())
                else:
                    test_choice = st.selectbox('Select Test Name', loinc_data['name2'].unique())
                    test_choice = loinc_data[loinc_data['name2'] == test_choice]['id'].values[0]

            # Create placeholders for current values
            current_before_placeholder = st.empty()
            current_after_placeholder = st.empty()


            def display_current_values():
                current_good_before = \
                dss.db_con.loinc_data[dss.db_con.loinc_data['id'] == test_choice]['good_before'].values[0]
                current_good_after = \
                dss.db_con.loinc_data[dss.db_con.loinc_data['id'] == test_choice]['good_after'].values[0]

                good_before_days, good_before_hours, good_before_minutes = timedelta_to_dhm(current_good_before)
                good_after_days, good_after_hours, good_after_minutes = timedelta_to_dhm(current_good_after)

                current_before_placeholder.write(
                    f"Current Good Before: {good_before_days} days, {good_before_hours} hours, {good_before_minutes} minutes")
                current_after_placeholder.write(
                    f"Current Good After: {good_after_days} days, {good_after_hours} hours, {good_after_minutes} minutes")

                return good_before_days, good_before_hours, good_before_minutes, good_after_days, good_after_hours, good_after_minutes


            # Display initial values
            good_before_days, good_before_hours, good_before_minutes, good_after_days, good_after_hours, good_after_minutes = display_current_values()

            # Input for new values
            st.subheader("Update Good Before")
            col1, col2, col3 = st.columns(3)
            with col1:
                new_good_before_days = st.number_input("Days", min_value=0, value=good_before_days)
            with col2:
                new_good_before_hours = st.number_input("Hours", min_value=0, max_value=23, value=good_before_hours)
            with col3:
                new_good_before_minutes = st.number_input("Minutes", min_value=0, max_value=59,
                                                          value=good_before_minutes)

            st.subheader("Update Good After")
            col1, col2, col3 = st.columns(3)
            with col1:
                new_good_after_days = st.number_input("Days ", min_value=0, value=good_after_days)
            with col2:
                new_good_after_hours = st.number_input("Hours ", min_value=0, max_value=23, value=good_after_hours)
            with col3:
                new_good_after_minutes = st.number_input("Minutes ", min_value=0, max_value=59,
                                                         value=good_after_minutes)

            if st.button('Update Good Before/After'):
                # Convert input to numpy.timedelta64
                new_good_before = np.timedelta64(new_good_before_days, 'D') + np.timedelta64(new_good_before_hours,
                                                                                             'h') + np.timedelta64(
                    new_good_before_minutes, 'm')
                new_good_after = np.timedelta64(new_good_after_days, 'D') + np.timedelta64(new_good_after_hours,
                                                                                           'h') + np.timedelta64(
                    new_good_after_minutes, 'm')

                # Update the loinc_data DataFrame
                dss.db_con.loinc_data.loc[dss.db_con.loinc_data['id'] == test_choice, 'good_before'] = new_good_before
                dss.db_con.loinc_data.loc[dss.db_con.loinc_data['id'] == test_choice, 'good_after'] = new_good_after

                # Save the updated DataFrame back to the data source
                dss.db_con.save_loinc_data()

                # Update the displayed values
                display_current_values()

                st.success("Good Before/After values updated successfully!", icon="✅")
    else:
        st.info("Please enter the password to access this function.", icon="🔑")



# Optionally display raw data
if st.checkbox('Show Raw Data'):
    st.subheader('Patient Data')
    st.write(patients_df)
    st.subheader('Observations Data')
    st.write(observations_df)

