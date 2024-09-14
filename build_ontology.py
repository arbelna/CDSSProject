from owlready2 import *

# Load or create ontology
onto = get_ontology("http://example.com/CDSSproject")


# Define the classes with namespace
class Patient(Thing):
    namespace = onto


class Symptom(Thing):
    namespace = onto

class HemoglobinState(Thing):
    namespace = onto

class HematologicalState(Thing):
    namespace = onto


class SystemicToxicity(Thing):
    namespace = onto


class Treatment(Thing):
    namespace = onto


# Define individuals for HemoglobinState
with onto:
    severe_anemia = HemoglobinState("Severe_Anemia")
    moderate_anemia = HemoglobinState("Moderate_Anemia")
    mild_anemia = HemoglobinState("Mild_Anemia")
    normal_hemoglobin = HemoglobinState("Normal_Hemoglobin")
    polycythemia = HemoglobinState("Polycythemia")

# Define individuals for HematologicalState
with onto:
    pancytopenia = HematologicalState("Pancytopenia")
    anemia = HematologicalState("Anemia")
    leukopenia = HematologicalState("Leukopenia")
    suspected_leukemia = HematologicalState("Suspected_Leukemia")
    leukemoid_reaction = HematologicalState("Leukemoid_Reaction")
    suspected_polycythemia_vera = HematologicalState("Suspected_Polycythemia_Vera")
    normal_hematological = HematologicalState("Normal_Hematological")
    polyhemia = HematologicalState("Polyhemia")

# Define individuals for SystemicToxicity
with onto:
    grade_i = SystemicToxicity("Grade_I")
    grade_ii = SystemicToxicity("Grade_II")
    grade_iii = SystemicToxicity("Grade_III")
    grade_iv = SystemicToxicity("Grade_IV")

# Define individuals for Treatment
with onto:
    M_I = Treatment("M_I Measure_BP_once_a_week")
    M_II = Treatment("M_II Measure_BP_every_3_days_Give_aspirin_5g_twice_a_week")
    M_III = Treatment("M_III Measure_BP_every_day_Give_aspirin_15g_every_day_Diet_consultation")
    M_IV = Treatment("M_IV Measure_BP_twice_a_day_Give_aspirin_15g_every_day_Exercise_consultation_Diet_consultation")
    M_V = Treatment("M_V Measure_BP_every_hour_Give_1gr_magnesium_every_hour_Exercise_consultation_Call_family")
    F_I = Treatment("F_I Measure_BP_every_3_days")
    F_II = Treatment("F_II Measure_BP_every_3_days_Give_Celectone_2g_twice_a_day_for_two_days_drug_treatment")
    F_III = Treatment("F_III Measure_BP_every_day_Give_1gr_magnesium_every_3_hours_Diet_consultation")
    F_IV = Treatment("F_IV Measure_BP_twice_a_day_Give_1gr_magnesium_every_hour_Exercise_consultation_Diet_consultation")
    F_V = Treatment("F_V Measure_BP_every_hour_Give_1gr_magnesium_every_hour_Exercise_consultation_Call_help")

# Define object properties and explicitly add them to the ontology
with onto:
    class has_hemoglobin_state(ObjectProperty):
        domain = [Patient]
        range = [HemoglobinState]


    class has_hematological_state(ObjectProperty):
        domain = [Patient]
        range = [HematologicalState]


    class has_systemic_toxicity(ObjectProperty):
        domain = [Patient]
        range = [SystemicToxicity]


    class has_treatment(ObjectProperty):
        domain = [Patient]
        range = [Treatment]


    class has_symptom(ObjectProperty):
        domain = [Patient]
        range = [Symptom]

# Define data properties and explicitly add them to the ontology
with onto:
    class gender(DataProperty):
        domain = [Patient]
        range = [str]


    class hemoglobin_level(DataProperty):
        domain = [Patient]
        range = [float]


    class wbc_level(DataProperty):
        domain = [Patient]
        range = [float]


    class fever(DataProperty):
        domain = [Symptom]
        range = [float]


    class chills(DataProperty):
        domain = [Symptom]
        range = [str]


    class skin_look(DataProperty):
        domain = [Symptom]
        range = [str]


    class allergic_state(DataProperty):
        domain = [Symptom]
        range = [str]


# Define functions to determine states
def determine_hemoglobin_state(patient):
    if not patient.gender or not patient.hemoglobin_level:
        raise ValueError("Gender and hemoglobin level cannot be None")
    hemoglobin_level = patient.hemoglobin_level[0]
    gender = patient.gender[0]
    if gender == "Male":
        if hemoglobin_level < 9:
            return severe_anemia
        elif hemoglobin_level < 11:
            return moderate_anemia
        elif hemoglobin_level < 13:
            return mild_anemia
        elif hemoglobin_level < 16:
            return normal_hemoglobin
        else:
            return polycythemia
    elif gender == "Female":
        if hemoglobin_level < 8:
            return severe_anemia
        elif hemoglobin_level < 10:
            return moderate_anemia
        elif hemoglobin_level < 12:
            return mild_anemia
        elif hemoglobin_level < 14:
            return normal_hemoglobin
        else:
            return polycythemia


def determine_hematological_state(patient):
    if not patient.gender or not patient.hemoglobin_level or not patient.wbc_level:
        raise ValueError("Gender, hemoglobin level, and WBC level cannot be None")
    hemoglobin_level = patient.hemoglobin_level[0]
    wbc_level = patient.wbc_level[0]
    gender = patient.gender[0]
    if gender == "Male":
        if hemoglobin_level < 13:
            if wbc_level < 4000:
                return pancytopenia
            elif wbc_level < 10000:
                return anemia
            else:
                return suspected_leukemia
        elif hemoglobin_level < 16:
            if wbc_level < 4000:
                return leukopenia
            elif wbc_level < 10000:
                return normal_hematological
            else:
                return leukemoid_reaction
        else:
            if wbc_level < 4000:
                return suspected_polycythemia_vera
            elif wbc_level < 10000:
                return polyhemia
            else:
                return suspected_polycythemia_vera
    elif gender == "Female":
        if hemoglobin_level < 12:
            if wbc_level < 4000:
                return pancytopenia
            elif wbc_level < 10000:
                return anemia
            else:
                return suspected_leukemia
        elif hemoglobin_level < 14:
            if wbc_level < 4000:
                return leukopenia
            elif wbc_level < 10000:
                return normal_hematological
            else:
                return leukemoid_reaction
        else:
            if wbc_level < 4000:
                return suspected_polycythemia_vera
            elif wbc_level < 10000:
                return polyhemia
            else:
                return suspected_polycythemia_vera


def determine_systemic_toxicity(patient):
    if not patient.has_symptom:
        raise ValueError("Patient does not have symptoms")
    grades = []
    symptom = patient.has_symptom[0]

    if symptom.fever:
        fever = symptom.fever[0]
        if fever >= 40.0:
            grades.append(grade_iii)
        elif fever >= 38.5:
            grades.append(grade_ii)
        else:
            grades.append(grade_i)

    if symptom.chills:
        chills = symptom.chills[0]
        if chills == "Rigor":
            grades.append(grade_iii)
        elif chills == "Shaking":
            grades.append(grade_ii)
        else:
            grades.append(grade_i)

    if symptom.skin_look:
        skin_look = symptom.skin_look[0]
        if skin_look == "Exfoliation":
            grades.append(grade_iv)
        elif skin_look == "Desquamation":
            grades.append(grade_iii)
        elif skin_look == "Vesiculation":
            grades.append(grade_ii)
        else:
            grades.append(grade_i)

    if symptom.allergic_state:
        allergic_state = symptom.allergic_state[0]
        if allergic_state == "Anaphylactic Shock":
            grades.append(grade_iv)
        elif allergic_state == "Severe Bronchospasm":
            grades.append(grade_iii)
        elif allergic_state == "Bronchospasm":
            grades.append(grade_ii)
        else:
            grades.append(grade_i)

    if grades:
        return max(grades, key=lambda x: ["Grade_I", "Grade_II", "Grade_III", "Grade_IV"].index(x.name))


def determine_treatment(patient):
    if not patient.gender or not patient.has_hemoglobin_state or not patient.has_hematological_state or not patient.has_systemic_toxicity:
        raise ValueError("Gender, hemoglobin state, hematological state, and systemic toxicity cannot be None")

    gender = patient.gender[0]
    hemoglobin_state = patient.has_hemoglobin_state[0]
    hematological_state = patient.has_hematological_state[0]
    systemic_toxicity = patient.has_systemic_toxicity[0]

    # Define treatment based on the classification table
    if gender == "Male":
        if hemoglobin_state == severe_anemia and hematological_state == pancytopenia and systemic_toxicity == grade_i:
            return M_I
        elif hemoglobin_state == moderate_anemia and hematological_state == anemia and systemic_toxicity == grade_ii:
            return M_II
        elif hemoglobin_state == mild_anemia and hematological_state == suspected_leukemia and systemic_toxicity == grade_iii:
            return M_III
        elif hemoglobin_state == normal_hemoglobin and hematological_state == leukemoid_reaction and systemic_toxicity == grade_iv:
            return M_IV
        elif hemoglobin_state == polycythemia and hematological_state == suspected_polycythemia_vera and systemic_toxicity == grade_iv:
            return M_V

    elif gender == "Female":
        if hemoglobin_state == severe_anemia and hematological_state == pancytopenia and systemic_toxicity == grade_i:
            return F_I
        elif hemoglobin_state == moderate_anemia and hematological_state == anemia and systemic_toxicity == grade_ii:
            return F_II
        elif hemoglobin_state == mild_anemia and hematological_state == suspected_leukemia and systemic_toxicity == grade_iii:
            return F_III
        elif hemoglobin_state == normal_hemoglobin and hematological_state == leukemoid_reaction and systemic_toxicity == grade_iv:
            return F_IV
        elif hemoglobin_state == polycythemia and hematological_state == suspected_polycythemia_vera and systemic_toxicity == grade_iv:
            return F_V

    raise ValueError("No matching treatment found for the given conditions.")


# Save the ontology
onto.save(file="cdss.owl", format="rdfxml")