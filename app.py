import os
import json
import logging
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
    "temperature": 0.5,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-002",
    generation_config=generation_config,
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    },
)

app = Flask(__name__)

def get_crop_recommendation(place):
    start_time = time.time()
    start_cpu_time = time.process_time()

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    """
                    Act/consider yourself as expert.
                    
                    If possible, consider to make response like as an below formatted example:
                    
                    Crop: Cotton
                    Season: Kharif
                    Weather:
                        Temperature: 25-35°C
                        Humidity: 60-80%
                        Rainfall: 500-750 mm
                    Soil Type & Nutrients:
                        Type: Well-drained sandy loam or clay loam
                        Nutrients:
                            Micronutrients: Boron, Magnesium, Sulfur
                            Macronutrients: Nitrogen, Phosphorus, Potassium
                    Water Requirements:
                        Watering Frequency: Regularly during the growing season, especially during flowering and boll formation
                        Watering Method: Furrow irrigation or drip irrigation
                    Sunlight Requirements:
                        Sunlight Hours: 6-8 hours per day
                        Shade Tolerance: Low
                    Pest and Disease Resistance:
                        Common Pests: Bollworms, Aphids, Whiteflies
                        Common Diseases: Leaf spot, Root rot, Bacterial blight
                    Growth Duration:
                        Time to Maturity: 150-180 days
                    Planting Guidelines:
                        Planting Depth: 3-4 cm
                        Planting Spacing: 60-90 cm
                    Harvesting Information:
                        Harvest Time: When bolls open and cotton fibers are exposed
                        Harvest Method: Handpicking
                    Agricultural productivity:
                        Yield: 250-350 kg lint/acre
                        Seed Ratio: Varies depending on the variety
                    Special Considerations:
                        Drought Tolerance: Moderate
                        Frost Tolerance: Low
                    
                    
                    
                    Place: {place}
                    
                    If possible, please provide response in following below format with proper indentations, exact wording so it easy for readablity.
                    Provide crop recommendations in the following format:

                    Crop: [Crop Name]
                        Season: [Season]
                        Weather:
                            Temperature: [Temperature]
                            Humidity: [Humidity]
                            Rainfall: [Rainfall]
                        Soil Type & Nutrients:
                            Type: [Soil Type]
                            Nutrients: 
                                Micronutrients: [Micronutrients]
                                Macronutrients: [Macronutrients]
                        Water Requirements:
                            Watering Frequency: [Frequency]
                            Watering Method: [Method]
                        Sunlight Requirements:
                            Sunlight Hours: [Hours per day]
                            Shade Tolerance: [Tolerance level]
                        Pest and Disease Resistance:
                            Common Pests: [Pests]
                            Common Diseases: [Diseases]
                        Growth Duration:
                            Time to Maturity: [Days/Weeks/Months]
                        Planting Guidelines:
                            Planting Depth: [Depth]
                            Planting Spacing: [Spacing]
                        Harvesting Information:
                            Harvest Time: [Time]
                            Harvest Method: [Method]
                        Agricultural productivity:
                            Yield: [Yield in kg/acre]
                            Seed Ratio: [no. of seeds to be produced from a single seed when it is sown and harvested.]
                        Special Considerations:
                            Drought Tolerance: [Tolerance level]
                            Frost Tolerance: [Tolerance level]

                    #Please list out all the crops, which used to cultivated at that place, as much as possible
                    """
                ],
            }
        ]
    )

    prompt = f"""
    Place: {place}
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

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/get_crop_recommendation', methods=['POST'])
def crop_recommendation():
    data = request.get_json()
    place = data.get("place")

    response = get_crop_recommendation(place)

    # if response is None:
    #     return jsonify({'error': 'Failed to fetch recommendations'}), 500

    # Save raw text to file (with UTF-8 encoding)
    text_file_path = os.path.join("static", "txt", "crop_recommendations.txt")
    os.makedirs(os.path.dirname(text_file_path), exist_ok=True)
    with open(text_file_path, "w", encoding='utf-8') as f:
        f.write(response)

    formatted_recommendations = format_recommendations(response)
    return jsonify({'recommendations': formatted_recommendations})



def format_recommendations(recommendations):
    formatted = ""
    crops = recommendations.split("\n\n")
    for crop in crops:
        if crop.strip():
            formatted += "<div class='crop'>"
            lines = crop.split("\n")
            for line in lines:
                if line.strip():
                    line = line.replace("**", "")
                    if "Crop:" in line:
                        formatted += f"<p><strong>{line}</strong></p>"
                    elif any(line.startswith(prefix) for prefix in ["Season:", "Weather:", "Soil Type & Nutrients:", "Water Requirements:", "Sunlight Requirements:", "Pest and Disease Resistance:", "Growth Duration:", "Planting Guidelines:", "Harvesting Information:", "Agricultural productivity:", "Special Considerations:"]):
                        formatted += f"<p><strong>{line}</strong></p>"
                    else:
                        formatted += f"<p style='font-weight:555'>{line}</p>"
            formatted += "</div>"
    return formatted

if __name__ == "__main__":
    app.run(debug=True)
