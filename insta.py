import os
import sys
import glob
from PIL import Image

INSTAGRAM_DIMENSIONS = [
    {"name": "square", "width": 1080, "height": 1080, "ratio": 1.0},
    {"name": "portrait", "width": 1080, "height": 1350, "ratio": 1080 / 1350},
    {"name": "landscape", "width": 1080, "height": 566, "ratio": 1080 / 566}
]

def get_best_instagram_dimensions(image_paths):
    total_ratio = 0.0
    valid_images = 0
    for path in image_paths:
        try:
            with Image.open(path) as img:
                total_ratio += img.width / img.height
                valid_images += 1
        except Exception as e:
            print(f"Skipping {path}: {e}")
    if valid_images == 0:
        return INSTAGRAM_DIMENSIONS[0]
    avg_ratio = total_ratio / valid_images
    best_dimension = INSTAGRAM_DIMENSIONS[0]
    min_diff = abs(avg_ratio - best_dimension["ratio"])
    for dim in INSTAGRAM_DIMENSIONS:
        diff = abs(avg_ratio - dim["ratio"])
        if diff < min_diff:
            min_diff = diff
            best_dimension = dim
    return best_dimension

def pad_and_resize_image(img_path, target_width, target_height, output_dir):
    try:
        img = Image.open(img_path)
        img = img.convert("RGB")
        width_ratio = target_width / img.width
        height_ratio = target_height / img.height
        scale_factor = min(width_ratio, height_ratio)
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        background_color = (15, 15, 15)
        new_img = Image.new("RGB", (target_width, target_height), background_color)
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        new_img.paste(resized_img, (paste_x, paste_y))
        filename = os.path.basename(img_path)
        output_path = os.path.join(output_dir, filename)
        new_img.save(output_path, quality=95)
        print(f"Processed and saved: {output_path}")
    except Exception as e:
        print(f"Error processing {img_path}: {e}")

def main(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    search_pattern = os.path.join(input_dir, "*.*")
    all_files = glob.glob(search_pattern)
    image_paths = []
    for f in all_files:
        ext = f.lower().split('.')[-1]
        if ext in ['jpg', 'jpeg', 'png', 'webp']:
            image_paths.append(f)
    if len(image_paths) == 0:
        print(f"No images found in the input directory: {os.path.abspath(input_dir)}")
        return
    best_dim = get_best_instagram_dimensions(image_paths)
    target_w = best_dim["width"]
    target_h = best_dim["height"]
    print(f"Selected base dimensions: {target_w}x{target_h} ({best_dim['name']})")
    for img_path in image_paths:
        pad_and_resize_image(img_path, target_w, target_h, output_dir)
    print("Batch processing complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_directory = sys.argv[1]
    else:
        input_directory = os.getcwd()
    output_directory = os.path.join(input_directory, "output_images")
    main(input_directory, output_directory)