import os
from flask import Flask, render_template, request, send_file
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import math
import re

app = Flask(__name__)

# Define the base directory and the path to the data folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

# Image configurations for different models
IMAGE_CONFIGS = {
    'default': {
        'width': 1100,
        'height': 480,
        'dpi': 600,
        'font_size': 7
    },
    'dell': {
        'width': 1100,
        'height': 480,
        'dpi': 600,
        'font_size': 14
    }
}

SSD_value = [
    "128GB",
    "256GB",
    "512GB",
    "1TB",
    "2TB"
]

RAM_value = [
    "64GB",
    "8GB",
    "4GB",
    "48GB",
    "40GB",
    "36GB",
    "32GB",
    "24GB",
    "20GB",
    "16GB",
    "12GB",
]

SSD_keywords = {
    "ssd.:": 1,
    "storage:": 2,
    "ssd:": 3
}

RAM_keywords = {
    "ram:": 1,
    "memory:": 2
}

def find_keyword(sentence, keywords):
    for keyword, value in keywords.items():
        if keyword in sentence:
            return value
    return 0  # Return 0 if none of the keywords are found

@app.route('/')
def index():
    ssd_values = SSD_value  # SSD options
    ram_values = RAM_value  # RAM options
    text_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.txt')]
    return render_template('index.html', ssd_values=ssd_values, ram_values=ram_values, text_files=text_files)


@app.route('/generate-image', methods=['POST'])
def generate_image():
    selected_text_files = request.form.get('text_files')
    selected_ssd = request.form.get('ssd')
    selected_ram = request.form.get('ram')

    brand = selected_text_files.split()

    brand = brand[0].lower()

    formatConfigs = brand

    if formatConfigs != "dell":
        formatConfigs = "default"
    else:
        formatConfigs = "dell"

    config = IMAGE_CONFIGS[formatConfigs]
    file_path = os.path.join(DATA_FOLDER, selected_text_files)
    if not os.path.exists(file_path):
        return "File not found", 404

    # Read text from the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    splittext = content.splitlines()

    for line in splittext:
        if re.search(r'\b(SSD|Storage)\b', line, re.IGNORECASE):
            if brand in ["msi", "dell"]:
                line = re.sub(r"(\d+(?:GB|TB) SSD)", lambda m: f"{selected_ssd} SSD", line, flags=re.IGNORECASE)
                print(line)
        if re.search(r'\b(Ram|Memory)\b', line, re.IGNORECASE):
            print(line)
    

    SSD_result = find_keyword(content.lower(), SSD_keywords)
    # 1 = "SSD.:" , 2 = "storage:", 3 = "ssd:"
    if SSD_result == 1:
        content = re.sub(r"(SSD.:\s*)(\S+)", lambda m: m.group(1) + selected_ssd, content, flags=re.IGNORECASE)
    elif SSD_result == 2:
        content = re.sub(r"(Storage:\s*)(\S+)", lambda m: m.group(1) + selected_ssd, content, flags=re.IGNORECASE)
    elif SSD_result == 3:
        content = re.sub(r"(SSD:\s*)(\S+)", lambda m: m.group(1) + selected_ssd, content, flags=re.IGNORECASE)
    elif SSD_result == 0:
        # Replace storage with "GB" or "TB" and SSD
        content = re.sub(r"(\d+(?:GB|TB) SSD)", selected_ssd, content, flags=re.IGNORECASE)
    
    RAM_result = find_keyword(content.lower(), RAM_keywords)

    # 1 = "ram:" , 2 = "memory:"
    if brand == "asus":
        print("yes")
    elif brand == "msi":
        content = re.sub(r"(DDR[45]) \d+GB(?:\(\d+GB\*\d+\))?",  lambda m: f"{selected_ram} RAM", content, flags=re.IGNORECASE)
    else:
        if RAM_result == 1: #Lenovo
            # Replace RAM format: "Ram: 16GB DDR4" -> "Ram: <selected_ram>"
            content = re.sub(r"(Ram:\s*\d+GB)\s*.*", lambda m: f"Ram: {selected_ram}", content, flags=re.IGNORECASE)
        elif RAM_result == 2:
            # Replace Memory format: "Memory: 32GB DDR5" -> "Memory: <selected_ram>"
            content = re.sub(r"(Memory:\s*\d+GB)\s*.*", lambda m: f"Memory: {selected_ram}", content, flags=re.IGNORECASE)
        elif RAM_result == 0:
            content = re.sub(r"\d+GB Memory",  lambda m: f"{selected_ram} Memory", content, flags=re.IGNORECASE)

    # Create an image in memory
    image = Image.new("RGB", (config['width'], config['height']), "white")
    draw = ImageDraw.Draw(image)

    # Load fonts
    try:
        bold_font = ImageFont.truetype("arialbd.ttf", math.floor(config['font_size'] * (config['dpi'] // 108)))
        regular_font = ImageFont.truetype("arial.ttf", math.floor(config['font_size'] * (config['dpi'] // 108)))
    except IOError:
        bold_font = regular_font = ImageFont.load_default()

    # Define text properties
    lines = content.splitlines()
    x, y = 30, 30  # Starting position
    line_spacing = 10  # Additional space between lines

    for line in lines:
        # Bold and larger for specific headings
        if line.strip() in ["Performance", "Software"]:
            font = bold_font
        else:
            font = regular_font

        # Draw text and calculate height using textbbox
        draw.text((x, y), line, fill="black", font=font)
        _, _, _, text_height = draw.textbbox((0, 0), line, font=font)  # Get the height of the text
        y += text_height + line_spacing  # Move to the next line

    # Save the image in memory
    img_buffer = BytesIO()
    image.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # Save the image to the static folder to display in HTML
    img_path = os.path.join(BASE_DIR, 'static', 'generated_image.png')
    image.save(img_path, format="PNG")

    # Serve the generated image in the HTML
    img_url = "/static/generated_image.png"
    return render_template("display_image.html", image_url=img_url)


@app.route('/static/<filename>')
def serve_image(filename):
    return send_file(os.path.join(BASE_DIR, 'static', filename))


if __name__ == '__main__':
    app.run(debug=True)
