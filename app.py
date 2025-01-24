import os
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import math
import re
from flask_cors import CORS


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Define the base directory and the path to the data folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, 'data')
HP_SPECIAL_MODEL = os.path.join(BASE_DIR, r'data\HP_special\model.txt')
HP_Template = os.path.join(BASE_DIR, r'data\HP_special\HP Template.txt')
TEMPLATE_FOLDER = os.path.join(BASE_DIR, r'data\Template')

# Image configurations for different models
IMAGE_CONFIGS = {
    'default': {
        'font_size': 6.5
    },
    'dell': {
        'font_size': 14
    },
    'hp': {
        'font_size': 9.5,
    }
}

@app.route('/')
def index():
    file_list = os.listdir(TEMPLATE_FOLDER)
    file_contents = []

    for file in file_list:
        file_path = os.path.join(TEMPLATE_FOLDER, file)
        # Ensure it's a file before reading (not a directory)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_contents.append({'name': file, 'content': content})

    return render_template('index.html', files=file_contents)


@app.route('/UploadLabel', methods=['POST'])
def UploadLabel():
    try:
        data = request.get_json()
        model_name = data.get('brand')
        laptop_name = data.get('laptopName')
        selected_files = data.get('selectedFiles', [])  # Default to empty list if not provided

        print(model_name, laptop_name)

        if not selected_files:
            return jsonify({"message": "No files selected."}), 400

        for i, file_info in enumerate(selected_files):
            selected_file = file_info.get('fileName')
            filtered_files = [
                file_info for file_info in selected_files if not 
                re.search(r"_special", file_info.get('fileName'))
            ]
            contains_special = any(re.search(r"_special", file_info.get('fileName')) for file_info in selected_files)

            if contains_special:
                with open(HP_SPECIAL_MODEL, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                
                lines.append(f"{model_name} {laptop_name}\n") 

                with open(HP_SPECIAL_MODEL, 'w', encoding='utf-8') as file:
                    file.writelines(lines)

            selected_files = filtered_files


        for i, file_info in enumerate(selected_files):
            selected_file = file_info.get('fileName')
            content = file_info.get('content')

            if not selected_file or not content:
                return jsonify({"message": "Invalid file data."}), 400

            # Replace "Template" with laptop_name in the file name
            file_name = re.sub(r"Template", laptop_name, selected_file).strip()

            file_name = re.sub(r"\s*\(French\)", "", file_name).strip()

            # Extract base file name and extension separately
            base_name, ext = os.path.splitext(file_name)

            unique_file_name = f"{base_name}{ext}"

            if model_name == "Acer":
                if (len(selected_files) > 1):
                # Create a unique filename with numbering
                    unique_file_name = f"{base_name}_{i + 1}{ext}"
            elif model_name == "HP":
                unique_file_name = re.sub(r"_\d+", "", file_name).strip()
                if "special" in unique_file_name.lower():
                    unique_file_name = re.sub(r"_special+", "", file_name).strip()

            # Save the file to the data folder
            file_path = os.path.join(DATA_FOLDER, unique_file_name)

            print(f"Saving file: {unique_file_name}")

            with open(file_path, "w", encoding='utf-8') as f:
                f.write(content)

        return jsonify({"message": "All files saved successfully!"}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "Error processing the files."}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image():
    selected_text_files = request.form.get('text_files')
    selected_ssd = request.form.get('ssd')
    selected_ram = request.form.get('ram')

    print(selected_text_files)

    base_name = re.sub(r'(_\d+)?\.txt$', '', selected_text_files)  # Remove suffix like _1 or _2

    brand = selected_text_files.split()[0].lower()

    width, height = 1100 , 480

    special_HP_flag = False

    if brand == 'hp':
        with open(HP_SPECIAL_MODEL, 'r') as file:
            model_content = file.read()
            lines = model_content.splitlines()
            for line in lines:
                if line == base_name:
                    special_HP_flag = True

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

        # Determine configuration
        formatConfigs = brand if brand in ["dell", "hp"] else "default"
        config = IMAGE_CONFIGS[formatConfigs]

        # Create an image in memory
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Load fonts
        try:
            bold_font = ImageFont.truetype("arialbd.ttf", math.floor(config['font_size'] * (600 // 108)))
            regular_font = ImageFont.truetype("arial.ttf", math.floor(config['font_size'] * (600 // 108)))
        except IOError:
            bold_font = regular_font = ImageFont.load_default()

        # Draw content onto the image
        lines = content.splitlines()
        x, y = 30, 50
        line_spacing = 10

        for line in lines:

            match = re.search(r"\[(\w+)\]", line)
            
            if match and match.group(1) == "bold":  # Check if the word is 'bold'
                # Remove everything after [bold] (including it)
                font = bold_font
                line = re.sub(r"\[bold\]", "", line).strip()
                if brand == 'hp':
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]  # bbox[2] is the right x-coordinate, bbox[0] is the left
                    x = (width - text_width) / 2  # Center text horizontally
                else:
                    x = 30
            else:
                font = regular_font
                x = 30
            
            
            if match and match.group(1) == "SSD":
                line = re.sub(r"\[SSD\]", selected_ssd, line)
            elif match and match.group(1) == "RAM":
                line = re.sub(r"\[RAM\]", selected_ram, line)


            # Draw text and calculate height using textbbox
            draw.text((x, y), line, fill="black", font=font)
            _, _, _, text_height = draw.textbbox((0, 0), line, font=font)  # Get the height of the text
            y += text_height + line_spacing  # Move to the next line

        # Save the image to a static file
        img_name = f"generated_image_{idx}.png"
        img_path = os.path.join(BASE_DIR, 'static', img_name)
        image.save(img_path, format="PNG")
        image_urls.append(f"/static/{img_name}")

    if special_HP_flag:
        x,y = 30, 150
        try:
            title_font = ImageFont.truetype("arialbd.ttf", math.floor(20 * (600 // 108)))
            content_font = ImageFont.truetype("arial.ttf", math.floor(9 * (600 // 108)))
        except IOError:
            bold_font = regular_font = ImageFont.load_default()

        with open(HP_Template, 'r') as file:

            image1 = Image.new("RGB", (width, height), "white")
            draw_special = ImageDraw.Draw(image1)

            HP_content = file.read()
            lines = HP_content.splitlines()
            for HP_line in lines:
                match = re.search(r"\[(\w+)\]", HP_line)

                if match and match.group(1) == "SSD":
                    HP_line = re.sub(r"\[SSD\]", selected_ssd, HP_line)
                    font = title_font
                elif match and match.group(1) == "RAM":
                    HP_line = re.sub(r"\[RAM\]", selected_ram, HP_line)
                    font = title_font
                elif match and match.group(1) == "BR":
                    HP_line = re.sub(r"\[BR\]", "", HP_line)
                    x = 600
                    y = 150
                else:
                    font = content_font
            
                # Draw text and calculate height using textbbox
                draw_special.text((x, y), HP_line, fill="black", font=font)
                _, _, _, text_height = draw_special.textbbox((0, 0), HP_line, font=font)  # Get the height of the text
                y += text_height + line_spacing  # Move to the next line

        # Save the image to a static file
        img_name = f"generated_special.png"
        img_path = os.path.join(BASE_DIR, 'static', img_name)
        image1.save(img_path, format="PNG")
        image_urls.append(f"/static/{img_name}")

    
    # Serve the list of generated images in the HTML
    return {"image_urls": image_urls}



@app.route('/static/<filename>')
def serve_image(filename):
    return send_file(os.path.join(BASE_DIR, 'static', filename))


if __name__ == '__main__':
    # app.run(host='0.0.0.0',port=8080, ssl_context=("cert.pem", "key.pem")) #For server
    app.run(debug=True) # For testing