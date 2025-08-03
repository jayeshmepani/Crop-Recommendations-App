import os
import time
import logging
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


SYSTEM_INSTRUCTION = """
Act as an expert agronomist and provide comprehensive crop recommendations for the place: {place}

First, understand the key agricultural classification systems.

**SEASONAL CLASSIFICATION:**
- Kharif Crops (Monsoon-sown; harvested Sep-Oct): Rice, Maize, Cotton, Soybean, Pearl millet, Sorghum, Groundnut
- Rabi Crops (Winter-sown; harvested Apr-May): Wheat, Barley, Mustard, Gram, Linseed, Peas, Oats  
- Zaid Crops (Summer-grown; harvested Jun-Jul): Watermelon, Muskmelon, Cucumber, Bitter gourd

**USAGE CLASSIFICATION:**
- Cereals: Rice, Wheat, Maize, Barley, Sorghum, Pearl millet
- Pulses: Chickpea, Pigeon pea, Urad, Moong, Lentil, Peas
- Oilseeds: Mustard, Groundnut, Sesame, Soybean, Sunflower, Castor
- And other categories like Fiber, Sugar, Horticultural, Plantation, Fodder crops.

**GLOBAL SOIL CLASSIFICATION CONTEXT:**
You must be aware of the relationships between different major soil classification systems. Use the following context and mapping to provide comprehensive soil information.

**Major Systems:**
| System                         | Used where?          | Top categories                                             |
| ------------------------------ | -------------------- | -------------------------------------------------------------- |
| **Indian Classification**      | India                | Alluvial, Black, Red, Laterite, Desert, etc.                   |
| **WRB (World Reference Base)** | **Global Standard**  | 32 Reference Soil Groups (Fluvisol, Vertisol, Chernozem, etc.) |
| **USDA Soil Taxonomy**         | USA & many countries | 12 Orders (Entisol, Inceptisol, Mollisol, Vertisol, etc.)      |
| **Australian Soil Class.**     | Australia            | 15 Soil Orders (Vertosols, Kurosols, Kandosols, etc.)          |

**Example Mapping Table (Use this as a guide):**
| India         | Australia        | USDA     | WRB (Global)          |
| ------------- | ---------------- | -------- | --------------------- |
| Black Soil    | Vertosol         | Vertisol | **Vertisol**          |
| Alluvial Soil | Rudosol/Tenosol  | Entisol  | **Fluvisol/Cambisol** |
| Laterite Soil | Ferrosol         | Oxisol   | **Ferralsol**         |
| Red Soil      | Kandosol/Chromosol | Ultisol  | **Acrisol/Lixisol**   |
| Desert Soil   | Arenosol/Calcarosol | Aridisol | **Arenosol/Calcisol** |

**Your Task:**
Provide detailed crop recommendations using the exact format below. When filling out the "Soil Profile" section, use the context above to provide the most likely international equivalents for the recommended Indian soil type. Include ALL suitable crops for the region, including exotic fruits, specialty vegetables, and medicinal plants.

**OUTPUT FORMAT (Use this exactly, preserving indentation):**

SEASONAL CROP RECOMMENDATIONS FOR {place}:

KHARIF SEASON (June-October):
Crop: [Crop Name]
    Category: [Cereal/Pulse/Oilseed/Fruit/Vegetable/etc.]
    Season: Kharif (Monsoon Season)
    Weather Requirements:
        Temperature: [Temperature range]
        Humidity: [Humidity range]
        Rainfall: [Rainfall requirement]
    Soil Profile & Global Compatibility:
        Indian Classification: [List compatible soil types from Indian classification, e.g., Black Soil, Alluvial Soil]
        International Equivalents:
            USDA Soil Taxonomy: [e.g., Vertisol, Entisol]
            WRB (Global) Group: [e.g., Vertisol, Fluvisol]
            Australian Soil Order: [e.g., Vertosol, Rudosol]
        Ideal Texture: [Sandy/Loamy/Clay/Silt preferences]
        pH Range: [pH range]
        Nutrient Requirements:
            Macronutrients: [NPK requirements]
            Micronutrients: [Trace elements needed]
    Water Management:
        Irrigation Method: [Method]
        Water Requirement: [Water needs]
        Critical Growth Stages: [When water is most critical]
    Sunlight & Climate:
        Sunlight Hours: [Hours per day]
        Temperature Tolerance: [Min-Max temperatures]
        Humidity Tolerance: [Humidity range]
    Plant Protection:
        Common Pests: [Major pests]
        Common Diseases: [Major diseases]
        Preventive Measures: [Prevention strategies]
    Cultivation Details:
        Seed Rate: [Seeds per acre/hectare]
        Planting Depth: [Depth]
        Row Spacing: [Spacing between rows]
        Plant Spacing: [Spacing between plants]
        Growth Duration: [Days to maturity]
    Harvesting & Yield:
        Harvest Indicators: [Signs of maturity]
        Harvest Method: [Harvesting technique]
        Expected Yield: [Yield per acre/hectare]
        Post-Harvest Care: [Storage/processing tips]
    Economics:
        Market Demand: [High/Medium/Low]
        Average Price Range: [Price per quintal]
        Value Addition Opportunities: [Processing options]
    Sustainability Factors:
        Drought Tolerance: [Tolerance level]
        Pest Resistance: [Natural resistance]
        Soil Health Impact: [Effect on soil]
        Carbon Footprint: [Environmental impact]

RABI SEASON (November-April):
[Repeat format for Rabi crops]

ZAID SEASON (April-June):
[Repeat format for Zaid crops if applicable]

PERENNIAL CROPS (Year-round):
[Repeat format for Perennial crops]

REGION-SPECIFIC RECOMMENDATIONS:
    Climate Zone: [Tropical/Subtropical/Temperate classification]
    Predominant Soil Type: [Based on location]
    Water Availability: [Rainfall pattern and irrigation status]
    Market Access: [Proximity to markets and transportation]
    Government Schemes: [Relevant agricultural schemes]
    Crop Insurance: [Available insurance options]

Provide detailed recommendations for at least 20-25 different crops across all seasons, including both traditional and non-traditional crops suitable for the specific location's climate, soil, and market conditions.
"""

CROP_CATEGORIES = {
    "cereals": [
        "Wheat", "Rice", "Basmati Rice", "Japonica Rice", "Indica Rice", "Jasmine Rice", "Arborio Rice",
        "Glutinous Rice", "Black Rice", "Red Rice", "Maize", "Corn", "Sweet Corn", "Popcorn", "Dent Corn",
        "Flint Corn", "Barley", "Two-row Barley", "Six-row Barley", "Hulless Barley", "Oats", "Rye", "Sorghum",
        "Jowar", "Pearl Millet", "Bajra", "Finger Millet", "Ragi", "Foxtail Millet", "Barnyard Millet",
        "Proso Millet", "Kodo Millet", "Little Millet", "Teff", "Quinoa", "Amaranth", "Fonio", "Spelt",
        "Triticale", "Buckwheat", "Wild Rice", "Teosinte", "Emmer", "Kamut", "Farro", "Einkorn", "Khorasan Wheat",
        "Durum Wheat", "Red Wheat", "White Wheat", "Hard Wheat", "Soft Wheat", "Spring Wheat", "Winter Wheat"
    ],
    "pulses": [
        "Chickpea", "Gram", "Kabuli Chickpea", "Desi Chickpea", "Pigeon Pea", "Arhar", "Toor", "Green Gram",
        "Moong", "Black Gram", "Urad", "Lentil", "Masoor", "Red Lentil", "Green Lentil", "Brown Lentil",
        "Yellow Lentil", "Field Pea", "Cowpea", "Lobia", "Moth Bean", "Kidney Bean", "Rajma", "Lima Bean",
        "Fava Bean", "Common Bean", "Azuki Bean", "Horse Gram", "Black-eyed Pea", "Winged Bean", "Navy Bean",
        "Pinto Bean", "Black Bean", "Bambara Groundnut", "Lablab Bean", "Sword Bean", "Jack Bean", "Goa Bean",
        "Rice Bean", "Butter Bean"
    ],
    "oilseeds": [
        "Groundnut", "Peanut", "Soybean", "Mustard", "Yellow Mustard", "Black Mustard", "Rapeseed", "Sesame",
        "Til", "Sunflower", "Safflower", "Castor", "Linseed", "Flax", "Niger Seed", "Hempseed", "Camelina",
        "Perilla", "Chia", "Poppyseed", "Crambe", "Canola"
    ],
    "fiber_crops": [
        "Cotton", "Indian Cotton", "Upland Cotton", "Pima Cotton", "Jute", "Kenaf", "Ramie", "Hemp",
        "Industrial Hemp", "Flax", "Sunn Hemp", "Mesta", "Abaca", "Manila Hemp", "Hibiscus Cannabinus",
        "Agave Sisalana", "Sisal", "Kapok", "Nettle", "Milkweed", "Bamboo", "Lotus", "Okra", "Sugarcane",
        "Esparto Grass", "Phormium"
    ],
    "sugar_crops": [
        "Sugarcane", "Sugar Beet", "Sweet Sorghum", "Palmyra Palm", "Date Palm", "Maple", "Agave", "Stevia",
        "Sorghum", "Yacon"
    ],
    "fodder_forage": [
        "Alfalfa", "Berseem Clover", "Napier Grass", "Maize", "Oat", "Stylo", "Stylosanthes", "Guinea Grass",
        "Para Grass", "Switchgrass", "Rutabaga", "Turnip", "Forage Brassica", "Sudangrass", "Cowpea", "Teosinte",
        "Italian Ryegrass", "Timothy Grass", "Bermuda Grass", "Festulolium", "Clover", "Ryegrass", "Fescue",
        "Orchard Grass", "Bluegrass", "Bromegrass", "Reed Canarygrass", "Buffalo Grass", "Zoysia Grass",
        "Dallis Grass", "Kikuyu Grass", "Pangola Grass"
    ],
    "plantation_crops": [
        "Tea", "Coffee", "Arabica Coffee", "Robusta Coffee", "Rubber", "Coconut", "Oil Palm", "Cashew", "Cocoa",
        "Areca Nut", "Betel Vine", "Cardamom", "Vanilla", "Tobacco", "Bamboo", "Eucalyptus", "Teak", "Mahogany",
        "Sandalwood", "Agarwood"
    ],
    "horticultural_fruits": [
        "Mango", "Alphonso Mango", "Totapuri Mango", "Kesar Mango", "Banana", "Cavendish Banana", "Plantain",
        "Red Banana", "Apple", "Gala Apple", "Fuji Apple", "Orange", "Navel Orange", "Lemon", "Lime", "Papaya",
        "Guava", "Pineapple", "Grapes", "Pomegranate", "Litchi", "Jackfruit", "Sapota", "Aonla", "Fig", "Date Palm",
        "Dragon Fruit", "Star Fruit", "Passion Fruit", "Avocado", "Kiwi", "Strawberry", "Blueberry", "Raspberry",
        "Blackberry", "Cherry", "Peach", "Plum", "Apricot", "Rambutan", "Mangosteen", "Longan", "Durian", "Persimmon",
        "Mulberry", "Custard Apple", "Jamun", "Watermelon", "Cantaloupe", "Breadfruit", "Soursop"
    ],
    "horticultural_vegetables": [
        "Tomato", "Potato", "Onion", "Brinjal", "Chili Pepper", "Bell Pepper", "Okra", "Cabbage", "Cauliflower",
        "Broccoli", "Carrot", "Radish", "Beetroot", "Spinach", "Fenugreek", "Coriander", "Cucumber", "Bottle Gourd",
        "Ridge Gourd", "Bitter Gourd", "Pumpkin", "Ash Gourd", "Sweet Potato", "Yam", "Taro", "Green Beans",
        "Lettuce", "Kale", "Zucchini", "Asparagus", "Celery", "Leek", "Mushrooms", "Artichoke", "Brussels Sprouts",
        "Arugula", "Bok Choy", "Swiss Chard", "Kohlrabi"
    ],
    "horticultural_spices": [
        "Turmeric", "Ginger", "Garlic", "Cumin", "Coriander", "Fenugreek", "Cardamom", "Clove", "Cinnamon",
        "Nutmeg", "Mace", "Fennel", "Ajwain", "Dill", "Saffron", "Vanilla", "Tamarind", "Pepper", "Star Anise",
        "Mustard", "Celery", "Allspice", "Aniseed", "Bay Leaf", "Curry Leaf", "Paprika", "Cayenne Pepper"
    ],
    "medicinal_aromatic": [
        "Aloe Vera", "Ashwagandha", "Tulsi", "Neem", "Senna", "Stevia", "Lemongrass", "Geranium", "Vetiver",
        "Patchouli", "Citronella", "Mint", "Basil", "Rosemary", "Chamomile", "Lavender", "Thyme", "Oregano", "Ginseng",
        "Licorice", "Echinacea", "Sage", "Brahmi", "Shatavari"
    ],
    "nuts_dry_fruits": [
        "Almond", "Walnut", "Pistachio", "Cashew", "Chestnut", "Pecan", "Hazelnut", "Macadamia"
    ],
    "exotic_specialty": [
        "Dragon Fruit", "Star Fruit", "Passion Fruit", "Avocado", "Kiwi", "Strawberry", "Raspberry", "Blackberry",
        "Goji Berry", "Durian", "Mangosteen", "Rambutan", "Longan", "Microgreens", "Shiitake Mushroom", "Oyster Mushroom",
        "Asparagus", "Purple Carrot", "Moringa", "Sea Buckthorn", "Salak", "Pawpaw"
    ],
    "fruit_trees_ornamentals": [
        "Mango", "Guava", "Jackfruit", "Citrus", "Orange", "Lemon", "Lime", "Avocado", "Fig", "Pomegranate", "Olive",
        "Pear", "Apricot", "Peach", "Cherry", "Almond", "Plum", "Persimmon", "Apple", "Walnut", "Pecan"
    ],
    "leguminous_cover": [
        "Cowpea", "Cluster Bean", "Mung Bean", "Black Gram", "Pea", "Lablab Bean", "Sesbania", "Crotalaria", "Vetch",
        "Lupin", "Clover", "Alfalfa", "Buckwheat", "Fenugreek"
    ],
    "root_crops": [
        "Cassava", "Sweet Potato", "Yam", "Taro", "Jicama", "Parsnip", "Turnip", "Rutabaga", "Radish", "Beetroot",
        "Horseradish", "Maca", "Arrowroot", "Ginseng", "Daikon", "Carrot"
    ],
    "tuber_crops": [
        "Potato", "Jerusalem Artichoke", "Ulluco", "Oca", "Mashua", "Yacon", "Chinese Artichoke", "Water Chestnut"
    ],
    "herbs": [
        "Thyme", "Rosemary", "Oregano", "Basil", "Parsley", "Cilantro", "Dill", "Chives", "Marjoram", "Sage", "Mint",
        "Lemon Balm", "Bay Leaf", "Curry Leaf", "Shiso", "Sorrel"
    ],
    "grasses": [
        "Wheatgrass", "Barley Grass", "Oat Grass", "Rye Grass", "Millet Grass", "Sorghum Grass", "Bamboo",
        "Lemongrass", "Citronella", "Vetiver", "Switchgrass"
    ],
    "aquatic_crops": [
        "Watercress", "Lotus", "Water Chestnut", "Wasabi", "Rice", "Taro", "Cattail", "Water Spinach", "Kelp",
        "Spirulina", "Cranberry"
    ],
    "forest_crops": [
        "Wild Berries", "Mushrooms", "Truffles", "Ginseng", "Maple", "Birch", "Wild Nuts", "Fiddleheads"
    ],
    "industrial_crops": [
        "Indigo", "Henna", "Madder", "Woad", "Annatto", "Camphor", "Pyrethrum", "Guayule", "Jojoba", "Flax"
    ],
    "biofuel_crops": [
        "Switchgrass", "Jatropha", "Miscanthus", "Camelina", "Pongamia", "Algae", "Corn", "Sugarcane", "Soybean",
        "Palm Oil", "Willow", "Poplar"
    ],
    "ornamental_crops": [
        "Rose", "Tulip", "Lily", "Orchid", "Chrysanthemum", "Carnation", "Gerbera", "Sunflower", "Marigold",
        "Daffodil", "Hyacinth", "Gladiolus", "Iris", "Dahlia", "Zinnia", "Pansy", "Violet", "Lavender", "Hibiscus",
        "Jasmine"
    ]
}


# USDA mineral texture classes (12)
USDA_TEXTURE_CLASSES = [
    "Sand", "Loamy Sand", "Sandy Loam", "Loam", "Silt Loam", "Silt",
    "Sandy Clay Loam", "Clay Loam", "Silty Clay Loam",
    "Sandy Clay", "Silty Clay", "Clay"
]

# Major Indian soil types (14)
INDIAN_SOIL_TYPES = [
    "Bangar Alluvial", "Khadar Alluvial", "Black (Regur)", "Red",
    "Yellow", "Laterite", "Desert", "Saline-Alkaline", "Peaty-Marshy",
    "Forest", "Mountain", "Colluvial", "Aeolian", "Regosol/Entisol"
]

# Generate all texture-by-soil combinations
SOIL_COMPATIBILITY_CLASSES = [
    f"{texture} {soil} Soil"
    for soil in INDIAN_SOIL_TYPES
    for texture in USDA_TEXTURE_CLASSES
]

SEASONS = ['kharif', 'rabi', 'zaid', 'perennial']

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def get_crop_recommendation(prompt_text: str) -> str:
    """Enhanced recommendation function with flexible crop support"""
    start_wall = time.time()
    start_cpu = time.process_time()
    
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.3,
        top_p=0.9,
        top_k=40,
        response_mime_type="text/plain",
        tools=[types.Tool(googleSearch=types.GoogleSearch())],
    )

    response_text = ""
    try:
        for chunk in client.models.generate_content_stream(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=config
        ):
            if chunk.text:
                response_text += chunk.text
    except Exception as e:
        logging.error(f"Error in generating content: {e}")
        raise

    logging.info(f"Wall: {time.time()-start_wall:.2f}s | CPU: {time.process_time()-start_cpu:.2f}s")
    return response_text

def get_weather_info(place: str) -> dict:
    """Get current weather information for better recommendations"""
    current_month = datetime.now().month
    if current_month in [6, 7, 8, 9]:
        season = "Monsoon (Kharif)"
    elif current_month in [11, 12, 1, 2]:
        season = "Winter (Rabi)"
    elif current_month in [3, 4, 5]:
        season = "Summer (Zaid)"
    else:
        season = "Transition"
    
    return {
        "temperature": "25-35°C",
        "humidity": "60-80%",
        "rainfall": "Moderate",
        "season": season
    }

@app.route('/')
def index():
    return render_template('index.html', 
                         categories=list(CROP_CATEGORIES.keys()),
                         seasons=SEASONS)

@app.route('/get_crop_recommendation', methods=['POST'])
def crop_recommendation():
    data = request.get_json(silent=True) or {}
    place = data.get("place", "").strip()
    category = data.get("category", "").strip()
    season = data.get("season", "").strip()
    custom_crop = data.get("custom_crop", "").strip()
    
    if not place:
        return jsonify({"error": "Place is required"}), 400

    try:
        weather_info = get_weather_info(place)
        
        prompt_lines = [f"Place: {place}"]
        
        if custom_crop:
            prompt_lines.append(f"Specific crop of interest: {custom_crop}")
        elif category:
            if category in CROP_CATEGORIES:
                crops_in_category = ", ".join(CROP_CATEGORIES[category])
                prompt_lines.append(f"Focus on {category} crops including: {crops_in_category}")
            else:
                prompt_lines.append(f"Focus on crops in the category: {category}")
        
        if season:
            prompt_lines.append(f"Emphasize {season} season crops")
        
        prompt_lines.append(f"Current weather context: {weather_info}")
        prompt_text = "\n".join(prompt_lines)
        
        raw_text = get_crop_recommendation(prompt_text)
        
        os.makedirs("static/txt", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recommendations_{place.replace(' ', '_')}_{timestamp}.txt"
        
        with open(f"static/txt/{filename}", "w", encoding="utf-8") as f:
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Location: {place}\n")
            f.write(f"Category Filter: {category or 'All'}\n")
            f.write(f"Season Filter: {season or 'All'}\n")
            f.write(f"Custom Crop: {custom_crop or 'None'}\n")
            f.write(f"Weather Context: {weather_info}\n")
            f.write("-" * 50 + "\n\n")
            f.write(raw_text)

        formatted = format_recommendations(raw_text)
        
        return jsonify({
            "recommendations": formatted,
            "weather": weather_info,
            "download_file": filename,
            "generated_at": datetime.now().isoformat(),
            "prompt_used": prompt_text
        })

    except Exception as e:
        logging.exception("GenAI request failed")
        return jsonify({"error": f"Failed to fetch recommendations: {str(e)}"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_file(f"static/txt/{secure_filename(filename)}", 
                        as_attachment=True, 
                        download_name=filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route('/compare_crops', methods=['POST'])
def compare_crops():
    """Compare multiple crops for the given location"""
    data = request.get_json(silent=True) or {}
    place = data.get("place", "").strip()
    crops = data.get("crops", [])
    
    if not place or not crops:
        return jsonify({"error": "Place and crops list required"}), 400
    
    try:
        # **REVISED PROMPT** - More strict and provides a clear example
        comparison_prompt = f"""
        Act as an expert agronomist and agricultural economist. Your task is to compare the following crops for cultivation in **{place}**.
        Crops to compare: {', '.join(crops)}

        **Output Instructions:**
        1.  Generate a **single, complete HTML `<table>`**.
        2.  The table must have a `<thead>` with the first column header as "Metric" and subsequent headers as the crop names.
        3.  The `<tbody>` must contain one `<tr>` for each of the following metrics:
            - Suitability Score (1-10)
            - Initial Investment
            - Expected ROI & Profitability
            - Risk Factors & Challenges
            - Market Demand & Price Trends
            - Seasonal Advantages
            - Soil & Climate Requirements
            - Water & Irrigation Needs
            - Labor & Mechanization
            - Post-Harvest & Storage
        4.  For each metric, provide a concise, location-specific comparison for each crop in its respective `<td>`.
        5.  If a `<td>` contains a list of items, use a simple `<ul>` with `<li>` tags. Do not use `<br>` or `<div>` tags inside table cells.
        6.  **CRITICAL: Your entire response must be ONLY the HTML `<table>` element and nothing else. Do not include `<html>`, `<body>`, `<!DOCTYPE>`, markdown fences (```html), or any explanatory text before or after the table.**

        **Example Structure:**
        ```html
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>[Crop 1 Name]</th>
              <th>[Crop 2 Name]</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>Suitability Score (1-10)</th>
              <td>[Details for Crop 1]</td>
              <td>[Details for Crop 2]</td>
            </tr>
            <tr>
              <th>Risk Factors & Challenges</th>
              <td><ul><li>Risk 1</li><li>Risk 2</li></ul></td>
              <td><ul><li>Risk A</li><li>Risk B</li></ul></td>
            </tr>
          </tbody>
        </table>
        ```

        Now, generate the comparison table for **{place}** comparing **{', '.join(crops)}**.
        """     
        
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=comparison_prompt)])]
        config = types.GenerateContentConfig(
            system_instruction="Act as an agricultural consultant providing comprehensive crop comparison analysis. Output only clean HTML as requested.",
            temperature=0.3,
            top_p=0.8,
            tools=[types.Tool(googleSearch=types.GoogleSearch())],
        )
        
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-2.0-flash-lite",
            contents=contents,
            config=config
        ):
            if chunk.text:
                response_text += chunk.text
        
        formatted_comparison = format_comparison(response_text)
        
        return jsonify({
            "comparison": formatted_comparison,
            "crops_compared": crops,
            "location": place
        })
        
    except Exception as e:
        logging.exception("Crop comparison failed")
        return jsonify({"error": f"Failed to compare crops: {str(e)}"}), 500

@app.route('/suggest_crops', methods=['POST'])
def suggest_crops():
    """Suggest crops based on partial input"""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip().lower()
    
    if len(query) < 2:
        return jsonify({"suggestions": []})
    
    suggestions = []
    
    for category, crops in CROP_CATEGORIES.items():
        for crop in crops:
            if query in crop.lower():
                suggestions.append({
                    "crop": crop,
                    "category": category.replace('_', ' ').title()
                })
    
    return jsonify({"suggestions": suggestions[:10]})

def format_recommendations(text: str) -> str:
    """Enhanced formatting with better HTML structure"""
    html = ""
    current_season = ""
    
    for block in text.strip().split("\n\n"):
        if not block.strip():
            continue
            
        lines = block.strip().split("\n")
        first_line = lines[0].strip()
        
        if any(season.upper() in first_line.upper() for season in ['KHARIF', 'RABI', 'ZAID', 'PERENNIAL']):
            if current_season:
                html += "</div>"
            html += f"<div class='season-section'><h2 class='season-header'>{first_line}</h2>"
            current_season = first_line
            continue
        
        if first_line.startswith("Crop:"):
            html += "<div class='crop-card'>"
            html += f"<div class='crop-title'>{first_line}</div>"
            
            for line in lines[1:]:
                stripped = line.strip()
                if not stripped: continue
                    
                indent_level = len(line) - len(line.lstrip())
                
                if any(stripped.startswith(pref) for pref in [
                    "Category:", "Season:", "Weather Requirements:", "Soil Compatibility:",
                    "Water Management:", "Sunlight & Climate:", "Plant Protection:",
                    "Cultivation Details:", "Harvesting & Yield:", "Economics:",
                    "Sustainability Factors:", "Region-Specific Recommendations:"
                ]):
                    html += f"<div class='section-header-detail' style='margin-left: {indent_level * 10}px'>{stripped}</div>"
                elif ":" in stripped and not stripped.endswith(":"):
                    key, value = stripped.split(":", 1)
                    html += f"<div class='detail-item' style='margin-left: {indent_level * 10}px'><span class='detail-key'>{key}:</span><span class='detail-value'>{value.strip()}</span></div>"
                else:
                    html += f"<div class='detail-text' style='margin-left: {indent_level * 10}px'>{stripped}</div>"
            
            html += "</div>"
    
    if current_season:
        html += "</div>"
    
    return html

def format_comparison(text: str) -> str:
    """
    Cleans the model's output to extract just the HTML table for crop comparison.
    Handles cases where the model might still include markdown fences or explanatory text.
    """
    # Remove markdown fences and surrounding whitespace
    cleaned_text = text.strip().removeprefix('```html').removesuffix('```').strip()
    
    # Use regex to find the table, which is more robust
    table_match = re.search(r'(<table.*?>.*?</table\s*>)', cleaned_text, re.DOTALL | re.IGNORECASE)
    
    if table_match:
        # If a table is found, return it directly. This is the ideal case.
        return table_match.group(1)
    else:
        # Fallback for unexpected format: return a formatted error.
        return f"""
        <div class="no-data">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Comparison Error</h3>
            <p>The AI model returned data in an unexpected format. Please try your query again.</p>
        </div>
        """



@app.route('/api/crop_categories')
def get_crop_categories():
    """API endpoint to get crop categories"""
    return jsonify(CROP_CATEGORIES)

@app.route('/api/seasons')
def get_seasons():
    """API endpoint to get seasons"""
    return jsonify(SEASONS)

@app.route('/api/soil_types')
def get_soil_types():
    """API endpoint to get soil types"""
    return jsonify({
        "texture_classes": USDA_TEXTURE_CLASSES,
        "indian_soil_types": INDIAN_SOIL_TYPES,
        "compatibility_classes": SOIL_COMPATIBILITY_CLASSES[:20]  # Return first 20 for demo
    })

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.run(debug=True, host='0.0.0.0', port=5000)