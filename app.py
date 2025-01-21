import os
from flask import Flask, render_template, request, send_file
import io
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import math
import re
from flask_cors import CORS  # Import the CORS function


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Define the base directory and the path to the data folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

# Image configurations for different models
IMAGE_CONFIGS = {
    'default': {
        'font_size': 6.5
    },
    'dell': {
        'font_size': 14
    },
    'hp': {
        'font_size': 6.5,
    }
}

HP_keywords = ["HP Laptop", "Victus by HP Gaming Laptop"]

SSD_value = [
    "128GB",
    "256GB",
    "512GB",
    "1TB",
    "2TB"
]

RAM_value = [
    "4GB",
    "8GB",
    "12GB",
    "16GB",
    "20GB",
    "24GB",
    "32GB",
    "36GB",
    "40GB",
    "48GB",
    "64GB",
]

@app.route('/')
def index():
    return render_template('index.html')    


@app.route('/generate-image', methods=['POST'])
def generate_image():
    selected_text_files = request.form.get('text_files')
    selected_ssd = request.form.get('ssd')
    selected_ram = request.form.get('ram')

    print(selected_text_files)

    base_name = re.sub(r'(_\d+)?\.txt$', '', selected_text_files)  # Remove suffix like _1 or _2
    related_files = [
        f for f in os.listdir(DATA_FOLDER)
        if re.match(rf'{re.escape(base_name)}(_\d+)?\.txt$', f, re.IGNORECASE)
    ]

    if not related_files:
        return "No related files found", 404

    # Create an image for each related file
    image_urls = []  # Store URLs of generated images
    for idx, file_name in enumerate(related_files, start=1):
        file_path = os.path.join(DATA_FOLDER, file_name)
        if not os.path.exists(file_path):
            continue

        # Read content of the file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Determine brand and configuration
        brand = selected_text_files.split()[0].lower()
        formatConfigs = brand if brand in ["dell", "hp"] else "default"
        config = IMAGE_CONFIGS[formatConfigs]

        # Create an image in memory
        image = Image.new("RGB", (1100, 480), "white")
        draw = ImageDraw.Draw(image)

        # Load fonts
        try:
            bold_font = ImageFont.truetype("arialbd.ttf", math.floor(config['font_size'] * (600 // 108)))
            regular_font = ImageFont.truetype("arial.ttf", math.floor(config['font_size'] * (600 // 108)))
            title_font = ImageFont.truetype("arialbd.ttf", math.floor( 10.5 * (600 // 108)))
        except IOError:
            bold_font = regular_font = ImageFont.load_default()

        # Draw content onto the image
        lines = content.splitlines()
        x, y = 30, 50
        line_spacing = 10

        for i, line in enumerate(lines):
            # Bold and larger for specific headings
            if brand == "dell":
                font = bold_font if line.strip() in ["Performance", "Software"] else regular_font
            elif brand == "hp":
                # Check if the current line contains "HP Laptop" or "Victus by HP Gaming Laptop"
                if any(keyword in line for keyword in HP_keywords):
                    font = title_font
                else:
                    font = regular_font
            else:
                font = bold_font
                
            if re.search(r'\b(SSD|Storage|STORAGE)\b', line, re.IGNORECASE):
                    if brand in ["msi", "dell"]:
                        line = re.sub(r"(\d+(?:GB|TB) SSD)", lambda m: f"{selected_ssd} SSD", line, flags=re.IGNORECASE)
                    elif brand in ["acer", "lenovo"]:
                        line = "Storage: " + selected_ssd
                    else:
                        if re.search(r'\b(SSD)\b', line, re.IGNORECASE):
                            line = re.sub(r"(SSD.:\s*)(\S+)", lambda m: m.group(1) + selected_ssd, line, flags=re.IGNORECASE)
                        else:
                            line = re.sub(r"(STORAGE:\s*)(\S+)", lambda m: m.group(1) + selected_ssd, line, flags=re.IGNORECASE)
            if re.search(r'\b(Memory|Ram)\b', line, re.IGNORECASE):
                    if brand == "lenovo":
                        line = "RAM: " + selected_ram
                    elif brand == "asus":
                        line = "• RAM: " + selected_ram
                    elif brand == "acer":
                        line = re.sub(r"(Memory:\s*\d+GB)\s*.*", lambda m: f"Memory: {selected_ram}", line, flags=re.IGNORECASE)
                        line = re.sub(r"(Mémoire:\s*\d+GB)\s*.*", lambda m: f"Mémoire: {selected_ram}", line, flags=re.IGNORECASE)
                    elif brand == "dell":
                        line = re.sub(r"\d+GB Memory",  lambda m: f"{selected_ram} Memory", line, flags=re.IGNORECASE)
            if brand == "msi":
                    line = re.sub(r"(DDR[45]) \d+GB(?:\(\d+GB\*\d+\))?",  lambda m: f"{selected_ram} RAM", line, flags=re.IGNORECASE)

            # Draw text and calculate height using textbbox
            draw.text((x, y), line, fill="black", font=font)
            _, _, _, text_height = draw.textbbox((0, 0), line, font=font)  # Get the height of the text
            y += text_height + line_spacing  # Move to the next line

        # Save the image to a static file
        img_name = f"generated_image_{idx}.png"
        img_path = os.path.join(BASE_DIR, 'static', img_name)
        image.save(img_path, format="PNG")
        image_urls.append(f"/static/{img_name}")

    # Serve the list of generated images in the HTML
    # return render_template("display_image.html", image_urls=image_urls)
    return {"image_urls": image_urls}



@app.route('/static/<filename>')
def serve_image(filename):
    return send_file(os.path.join(BASE_DIR, 'static', filename))


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080, ssl_context=("cert.pem", "key.pem")) #For server
    # app.run(debug=True) # For testing 