import os
import json
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import google.generativeai as genai
import time
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set your Gemini API key
genai.api_key = os.getenv("GEMINI_API_KEY")

# Create the model
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
generation_config = {
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 64,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    },
)

app = Flask(__name__)


def get_nutrient_recommendations(
    age,
    gender,
    height,
    weight,
    activity_level,
    pregnancy_or_lactation,
    health_condition,
    dietary_preferences,
):
    # Record the start time for wall-clock time inside the function
    start_time = time.time()

    # Record the start time for CPU time inside the function
    start_cpu_time = time.process_time()

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    """Act/consider yourself as expert nutritionist or dietitian.
                    Just consider the below general factors(age, gender, height, weight, and rest others) and provide/advise general nutrient recommendation.
                    Don't ask any specifics, just use some generals factors like age, gender, height, weight, pregnancy or lactation (if female and applicable), health condition (if any) and dietary preferences, and make response.
                    If possible, consider to make response with quantity(amount with "%" or mass or volume) that how much should have to consume/intake that particular nutrients per day;
                    like as an example:
                        Carbohydrates: '45-65%' of daily caloric intake.
                            Focus on whole grains, fruits, vegetables.
                            
                        Proteins: '10-35%' of daily caloric intake.
                            Sources: Lean meats, fish, eggs, dairy, legumes.
                                Histidine: 10 mg
                                Isoleucine: 19 mg
                                
                        Fats: '20-35%' of daily caloric intake.
                            Include healthy fats: Olive oil, nuts, avocados, fatty fish.
                                Linoleic acid (LA Omega-6): 11-17 g
                                Alpha-linolenic acid (ALA Omega-3): 1.1-1.6 g
                                
                        Vitamins:
                            Sources: Citrus fruits, eggs, leafy green vegetables, whole grains.
                                Vitamin A: 700-900 mcg.
                                Vitamin C: 75-90 mg.
                                Vitamin D: 600-800 IU.
                                Vitamin E: 15 mg.
                                Vitamin K: 90-120 mcg.
                                B Vitamins:
                                    B1 (Thiamine): 1.1-1.2 mg.
                                    B2 (Riboflavin): 1.1-1.3 mg.
                                    B3 (Niacin): 14-16 mg.
                                    B5 (Pantothenic Acid): 5 mg.
                                    B6 (Pyridoxine): 1.3-1.7 mg.
                                    B7 (Biotin): 30 mcg.
                                    B9 (Folate): 400 mcg.
                                    B12 (Cobalamin): 2.4 mcg.
                                    
                        Minerals:
                            Sources: Nuts and seeds, avocado, shellfish.
                                Calcium: 1,000-1,300 mg.
                                Iron: 8-18 mg.
                                Magnesium: 310-420 mg.
                                Potassium: 2,500-3,400 mg.
                                Zinc: 8-11 mg.
                        
                                        
                    Age: {age}
                    Gender: {gender}
                    Height: {height} cm
                    Weight: {weight} kg
                    Activity level: {activity_level}
                    Pregnancy or Lactation: {pregnancy_or_lactation}
                    Health Condition: {health_condition}
                    Dietary Preferences: {dietary_preferences}

                    Health Condition includes disabilities, disorders, diseases, allergies, injuries, infections, deficiencies, or any other
                    Dietary Preferences includes veg, vegan and non-veg

                    If possible, please provide response in following below format with proper indentations, exact wording, numbering, and bulleting so it easy for readablity.

                    BMI: [BMI]
                    Calories: [Calories]

                    Nutrients:
                        Macronutrients:
                            1. Carbohydrates: ['%' or 'mass' of daily caloric intake]
                                - Sources: [Sources]
                                Glucose: [Glucose]
                                Fructose: [Fructose]
                                Galactose: [Galactose]
                                Sucrose: [Sucrose]
                                Lactose: [Lactose]
                                Ribose: [Ribose]
                                Amylose: [Amylose]
                                Amylopectin: [Amylopectin]
                                Maltose: [Maltose]


                            2. Proteins (Essential Amino Acids): ['%' or 'mass' of daily caloric intake]
                                - Sources: [Sources]
                                Essential:
                                    Histidine (H): [Histidine]
                                    Isoleucine (I): [Isoleucine]
                                    Leucine (L): [Leucine]
                                    Lysine (K): [Lysine]
                                    Methionine (M): [Methionine]
                                    Phenylalanine (F): [Phenylalanine]
                                    Threonine (T): [Threonine]
                                    Tryptophan (W): [Tryptophan]
                                    Valine (V): [Valine]
                                
                                Conditionally essential:
                                    Arginine (R): [Arginine]
                                    Cysteine (C): [Cysteine]
                                    Glutamine (Q): [Glutamine]
                                    Glycine (G): [Glycine]
                                    Proline (P): [Proline]
                                    Tyrosine (Y): [Tyrosine]
                                    Taurine: [Taurine]


                            3. Fats (Essential Fatty Acids): ['%' or 'mass' of daily caloric intake]
                                - Sources: [Sources]
                                Saturated Fatty Acids (Stable): [Saturated Fatty Acids (Stable)]
                                Monounsaturated Fatty Acids (Semi-stable): [Monounsaturated Fatty Acids (Semi-stable)]
                                Polyunsaturated Fatty Acids (Unstable):
                                    Linoleic acid (LA) Omega-6 fatty acid: [Linoleic acid (LA)]
                                    α-Linolenic acid (ALA) Omega-3 fatty acid: [α-Linolenic acid (ALA)]
                                Dietary Cholesterol: [Dietary Cholesterol]


                        Micronutrients:
                            1. Minerals:
                                - Sources: [Sources]
                                Calcium: [Calcium]
                                Sulfur: [Sulfur]
                                Phosphorus: [Phosphorus]
                                Magnesium: [Magnesium]
                                Sodium: [Sodium]
                                Potassium: [Potassium]
                                Iron: [Iron]
                                Zinc: [Zinc]
                            
                                Trace elements:
                                Boron: [Boron]
                                Copper: [Copper]
                                Chlorine: [Chlorine]
                                Selenium: [Selenium]
                                Chromium: [Chromium]
                                Manganese: [Manganese]
                                Molybdenum: [Molybdenum]
                                Cobalt: [Cobalt]
                                Fluorine: [Fluorine]
                                Iodine: [Iodine]
                                Silicon: [Silicon]
                                Nickel: [Nickel]
                                Vanadium: [Vanadium]


                            2. Vitamins:
                                - Sources: [Sources]
                                Vitamin A (retinol): [Vitamin A (retinol)]
                                Vitamin B complex:
                                    Vitamin B1 (thiamin): [Vitamin B1 (thiamin)]
                                    Vitamin B2 (riboflavin): [Vitamin B2 (riboflavin)]
                                    Vitamin B3 (niacin): [Vitamin B3 (niacin)]
                                    Vitamin B4 (Choline): [Vitamin B4 (Choline)]
                                    Vitamin B5 (pantothenic acid): [Vitamin B5 (pantothenic acid)]
                                    Vitamin B6 (pyridoxine): [Vitamin B6 (pyridoxine)]
                                    Vitamin B7 (biotin): [Vitamin B7 (biotin)]
                                    Vitamin B8 (inositol): [Vitamin B8 (inositol)]
                                    Vitamin B9 (folate & folic acid): [Vitamin B9 (folate & folic acid)]
                                    Vitamin B12 (cobalamin): [Vitamin B12 (cobalamin)]
                                Vitamin C (ascorbic acid): [Vitamin C (ascorbic acid)]
                                Vitamin D complex:
                                    Vitamin D2 (ergocalciferol): [Vitamin D2 (ergocalciferol)]
                                    Vitamin D3 (cholecalciferol): [Vitamin D3 (cholecalciferol)]
                                Vitamin E (tocopherols and tocotrienols): [Vitamin E (tocopherols and tocotrienols)]
                                Vitamin K complex:
                                    Vitamin K1 (phylloquinone): [Vitamin K1 (phylloquinone)]
                                    Vitamin K2 (menaquinone): [Vitamin K2 (menaquinone)]


                    Other related info.:
                        Water: [Water]
                        Fibre: [Fibre]
                        Antioxidants: [Antioxidants' amounts & sources]
                        Electrolytes: [Electrolytes' amounts & sources]
                        Amino Acids (Non-essential): [Amino Acids (Non-essential)'s amounts & sources]
                        Ethanol: [Ethanol's amounts & sources]
                        Phytonutrients (Phytochemicals):
                            Flavonoids: [Flavonoids' amounts & sources]
                            Polyphenols: [Polyphenols' amounts & sources]
                            Carotenoids:
                                Alpha carotene: [Alpha carotene's amounts & sources]
                                Beta carotene: [Beta carotene's amounts & sources]
                                Cryptoxanthin: [Cryptoxanthin's amounts & sources]
                                Lutein: [Lutein's amounts & sources]
                                Lycopene: [Lycopene's amounts & sources]
                                Zeaxanthin: [Zeaxanthin's amounts & sources]
                    #includes sources too with quantity(amounts in '%' or mass or volume) into above followings Other related info.
                        
                        
                    Tips/Extra Recommendations/Advises:
                        - [Tip]
                        - [Recommendations/Advises]
                        - [Advice]
                        - [Recommendations/Advises/Tip related to health condition(s) (if any)]
                        - [List all nutrient deficiencies related to each of the mentioned health conditions (if any)]
                        for "List all nutrient deficiencies related to each of the mentioned health conditions (if any)",
                        format lists should be like this example:
                            - Orthostatic Hypotension:
                            Electrolytes (Sodium and Potassium): Imbalances in these electrolytes can affect blood pressure regulation, potentially contributing to orthostatic hypotension.
                            Fluid Intake: Dehydration, often linked to inadequate water intake or electrolyte imbalances, can exacerbate orthostatic hypotension.
                            
                            - Shortness of Breath (Dyspnea):
                            Iron: Iron deficiency anemia can lead to decreased oxygen-carrying capacity of red blood cells, causing dyspnea.
                            Vitamin B12 and Folate: Deficiencies in these vitamins can affect red blood cell production and oxygen transport, contributing to dyspnea.
                            
                            - Sleep Disorders:
                            Magnesium: Insufficient magnesium levels may interfere with sleep regulation and quality.
                            Vitamin D: Deficiency in vitamin D has been associated with sleep disorders, including insomnia.
                            
                            - Bronchodilator Effects:
                            Vitamin C: Adequate vitamin C levels are crucial for lung function and may support bronchodilation.
                            Omega-3 Fatty Acids: Found in fish oils, these fats have anti-inflammatory effects that can support respiratory function.
                            
                            - Temperature Perception Variability:
                            Thyroid Hormones (Iodine, Selenium): Thyroid hormones regulate metabolism and body temperature. Deficiencies in iodine or selenium can affect thyroid function, leading to temperature perception issues.
                            Vitamin D: Adequate levels of vitamin D are essential for overall metabolic health, potentially impacting temperature regulation.
                        
                    # Add sections for tips and advices (in needed)
                    """
                ],
            }
        ]
    )

    prompt = f"""
    Age: {age}
    Gender: {gender}
    Height: {height} cm
    Weight: {weight} kg
    Activity level: {activity_level}
    Pregnancy or Lactation: {pregnancy_or_lactation}
    Health Condition: {health_condition}
    Dietary Preferences: {dietary_preferences}
    """

    response = chat_session.send_message(
        prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
    )

    # Record the end time for CPU time
    end_cpu_time = time.process_time()

    # Record the end time for wall-clock time
    end_time = time.time()

    # Calculate elapsed times
    elapsed_wall_time = end_time - start_time
    elapsed_cpu_time = end_cpu_time - start_cpu_time

    print(f"CPU times: user {elapsed_cpu_time} seconds")
    print(f"Wall time: {elapsed_wall_time} seconds")

    print(response.text)
    # return response.text

    recommendations = response.text  # Directly get text from response
    return recommendations

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_nutrient_recommendations', methods=['POST'])
def nutrient_recommendations():
    data = request.get_json()

    age = data.get("age")
    gender = data.get("gender")
    height = data.get("height")
    weight = data.get("weight")
    activity_level = data.get("activity_level")
    pregnancy_or_lactation = data.get("pregnancy_or_lactation")
    health_condition = data.get("health_condition")
    dietary_preferences = data.get("dietary_preferences")

    response = get_nutrient_recommendations(
        age, gender, height, weight, activity_level, pregnancy_or_lactation, health_condition, dietary_preferences
    )

    # Save raw text to file (with UTF-8 encoding)
    text_file_path = os.path.join("static", "txt", "nutrient_recommendations.txt")
    os.makedirs(os.path.dirname(text_file_path), exist_ok=True)
    with open(text_file_path, "w", encoding='utf-8') as f:
        f.write(response)

    formatted_recommendations = format_recommendations(response)
    return jsonify({'recommendations': formatted_recommendations})

def format_recommendations(recommendations):
    formatted = ""
    sections = recommendations.split("\n\n")
    for section in sections:
        if section.strip():
            formatted += "<div class='section'>"
            lines = section.split("\n")
            for line in lines:
                if line.strip():
                    # Remove markdown symbols and add indentation
                    # line = line.replace("**", "").replace("##", "").strip()
                    
                    if "BMI:" in line or "Calories:" in line:
                        formatted += f"<p><strong>{line}</strong></p>"
                    elif "Nutrients:" in line or "Macronutrients:" in line or "Micronutrients:" in line or "Proteins:" in line or "Fats:" in line or "Carbohydrates:" in line or "3. Fats (Essential Fatty Acids):" in line or "2. Proteins (Essential Amino Acids):" in line or "Essential:" in line or "Essential Amino Acids:" in line or "Conditionally essential:" in line or "Minerals:" in line or "Vitamins:" in line or "Trace elements:" in line:
                        formatted += f"<p><strong>{line}</strong></p>"
                    elif "Other related info.:" in line or "Tips/Extra Recommendations/Advises:" in line:
                        formatted += f"<p><strong>{line}</strong></p>"
                    else:
                        formatted += f"<p style='font-weight:555'>{line}</p>"

            formatted += "</div>"
    return formatted


if __name__ == "__main__":
    app.run(debug=True)