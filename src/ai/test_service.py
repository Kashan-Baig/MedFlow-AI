from src.ai.services.input_service import process_patient_input
from src.ai.services.insight_service import generate_insights

# -------------------------
# SAMPLE FRONTEND INPUT
# -------------------------
raw_input = {
    "name": "Kashan",
    "email": "test@gmail.com",
    "phone": "03001234567",
    "age": 21,
    "gender": "male",
    "symptoms": "chest pain and difficulty breathing"
}

# -------------------------
# STEP 1: CLEAN INPUT
# -------------------------
patient = process_patient_input(raw_input)

# -------------------------
# STEP 2: RUN FULL PIPELINE
# -------------------------
result = generate_insights(patient)

# -------------------------
# OUTPUT
# -------------------------
print("\n🔥 FINAL RESULT:\n")
print(result)