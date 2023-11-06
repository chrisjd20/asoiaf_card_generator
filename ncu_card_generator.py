#!/usr/bin/env python
import csv
import os
import tkinter as tk
import pdb
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageStat
from collections import defaultdict
import sys
import re

#pip install pillow

FactionColors = {
    "Martell":"#a96438",
    "Neutral":"#544334",
    "Night's Watch":"#212425",
    "Stark":"#515a62",
    "Targaryen":"#5e102b",
    "Baratheon":"#242829",
    "Bolton":"#855953",
    "Free Folk":"#2f2922",
    "Greyjoy":"#02363a",
    "Lannister":"#861b25",
}

ArmyAttackAndAbilitiesBorderColors = {
    "Neutral":"Silver",
    "Night's Watch":"Gold",
    "Stark":"Gold",
    "Targaryen":"Gold",
    "Baratheon":"Silver",
    "Bolton":"Gold",
    "Free Folk":"Gold",
    "Greyjoy":"Gold",
    "Martell":"Gold",
    "Lannister":"Silver",
}

def add_rounded_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, "white")
    w,h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(90), (0, h - rad))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(180), (w - rad, h - rad))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(270), (w - rad, 0))
    alpha.paste(255, (rad, 0, w - rad, h - rad))
    alpha.paste(255, (0, rad, rad, h - rad))
    alpha.paste(255, (w - rad, rad, w, h - rad))
    alpha.paste(255, (rad, rad, w - rad, h - rad))
    im = im.convert("RGBA")
    im.putalpha(alpha)
    return im

def load_fonts(fonts_folder):
    font_files = [f for f in os.listdir(fonts_folder) if f.lower().endswith(('.otf', '.ttf'))]
    fonts = {}
    for font_file in font_files:
        try:
            font_path = os.path.join(fonts_folder, font_file)
            fonts[font_file.split(".")[0]] = ImageFont.truetype(font_path, size=44)
            for i in range(2,61):
                fonts[font_file.split(".")[0]+f'-{i}'] = ImageFont.truetype(font_path, size=i)
            print(f"Successfully loaded font: {font_file}")
        except Exception as e:
            print(f"Failed to load font {font_file}: {str(e)}")
    return fonts

def import_csvs_to_dicts(assets_data_folder):
    csv_files = [f for f in os.listdir(assets_data_folder) if f.endswith('.csv')]
    all_data = {}
    for csv_file in csv_files:
        file_path = os.path.join(assets_data_folder, csv_file)
        with open(file_path, mode='r', encoding='utf-8') as f:
            # Read the first line to get the headers
            original_headers = next(csv.reader(f))
            # Replace empty headers with incremental numbers as strings
            headers = [header if header else str(i) for i, header in enumerate(original_headers, 1)]
            # Go back to the start of the file before reading the rest
            f.seek(0)
            # Create a DictReader with the modified headers
            reader = csv.DictReader(f, fieldnames=headers)
            # Skip the original header row, since we already processed it
            next(reader)
            # Convert the content of the CSV file to a list of dictionaries
            data = [row for row in reader]
        all_data[csv_file.split('.')[0]] = data
    return all_data

# I use this so I can load the unit card and get x + y on the card so I can more easily get coordinates of images on click
class ImageEditor:
    def __init__(self, master, ncu_card_image):
        self.master = master
        master.title("Image Editor")

        self.ncu_card_image = ncu_card_image
        self.tk_image = ImageTk.PhotoImage(self.ncu_card_image)
        
        self.label = tk.Label(master, image=self.tk_image)
        self.label.pack()

        self.label.bind("<Button-1>", self.log_coordinates)

    def log_coordinates(self, event):
        x = event.x
        y = event.y
        print(f"Clicked at: {x}, {y}")


def draw_centered_text(draw, position, text_lines_list, font, fill, line_padding=0):
    """
    Draw multi-line text centered at the specified position.

    :param draw: ImageDraw object.
    :param position: Tuple (x, y) representing the position to center the text at.
    :param text: The text to draw.
    :param font: The font to use.
    :param fill: Color to use for the text.
    :param padding: Padding between lines of text.
    """
    total_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in text_lines_list]) + line_padding * (len(text_lines_list) - 1)

    x, y = position
    y -= total_height / 2  # Adjust y-coordinate to start drawing from.

    for line in text_lines_list:
        text_width, text_height = font.getbbox(line)[2], font.getbbox(line)[3] - font.getbbox(line)[1]
        draw.text((x - text_width / 2, y), line, font=font, fill=fill)
        y += text_height + line_padding


def add_shadow(original_image, shadow_size, shadow_strength, sides=('left', 'top', 'right', 'bottom')):
    if original_image.mode != 'RGBA':
        original_image = original_image.convert('RGBA')
    original_width, original_height = original_image.size
    # Calculate new image size
    new_width = original_width + shadow_size * ('left' in sides) + shadow_size * ('right' in sides)
    new_height = original_height + shadow_size * ('top' in sides) + shadow_size * ('bottom' in sides)
    # Create a new image with the new size and a transparent background
    new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    # Create the shadow gradient
    shadow_gradient = [i * (255 - shadow_strength) // shadow_size for i in range(shadow_size)]
    # Create the shadow on each side
    for side in sides:
        for i, alpha in enumerate(shadow_gradient):
            if side == 'left':
                band = Image.new('RGBA', (1, original_height), (0, 0, 0, alpha))
                new_image.paste(band, (i, shadow_size * ('top' in sides)))
            elif side == 'right':
                band = Image.new('RGBA', (1, original_height), (0, 0, 0, alpha))
                new_image.paste(band, (new_width - i - 1, shadow_size * ('top' in sides)))
            elif side == 'top':
                band = Image.new('RGBA', (original_width, 1), (0, 0, 0, alpha))
                new_image.paste(band, (shadow_size * ('left' in sides), i))
            elif side == 'bottom':
                band = Image.new('RGBA', (original_width, 1), (0, 0, 0, alpha))
                new_image.paste(band, (shadow_size * ('left' in sides), new_height - i - 1))
    # Place the original image on top of the shadow
    original_position = (shadow_size * ('left' in sides), shadow_size * ('top' in sides))
    new_image.paste(original_image, original_position, original_image)
    return new_image


def split_name_string(s, amnt=15):
    # Split the string by comma if it exists
    if ',' in s:
        return s.split(','), True
    # Split the string if it's longer than 18 characters
    if len(s) > amnt:
        # Find the middle index of the string
        middle_idx = len(s) // 2
        # Search for the nearest space character to the middle
        left_space = s.rfind(' ', 0, middle_idx)  # search space to the left of the middle
        right_space = s.find(' ', middle_idx)  # search space to the right of the middle
        # Determine which space character is closer to the middle
        if left_space == -1:  # if there's no space to the left of the middle
            split_idx = right_space
        elif right_space == -1:  # if there's no space to the right of the middle
            split_idx = left_space
        else:
            # Choose the space that's closer to the middle
            split_idx = left_space if (middle_idx - left_space) < (right_space - middle_idx) else right_space
        # Split the string at the chosen space
        return [s[:split_idx], s[split_idx+1:]], False
    # If string doesn't need splitting
    return [s], False

def split_on_center_space(text):
    # If the length of the text is less than 10 or there's no space, return the text in a single-item list
    if len(text) < 10 or ' ' not in text:
        return [text]
    # Find the middle index of the string
    middle = len(text) // 2
    left_index = text.rfind(' ', 0, middle)  # Search for space going left from the middle
    right_index = text.find(' ', middle)     # Search for space going right from the middle
    # Determine the closest space to the middle to use as the split point
    # If no space to the left, use the right one; if both exist, choose the closest
    if left_index == -1 or (right_index != -1 and (middle - left_index) > (right_index - middle)):
        split_index = right_index
    else:
        split_index = left_index
    # Split the string into two parts
    part1 = text[:split_index]
    part2 = text[split_index+1:]  # +1 to exclude the space itself
    # Return the parts in a list
    return [part1, part2]

def draw_circle(draw, center, radius, fill):
    """Draws a circle on the ImageDraw object"""
    left_up_point = (center[0] - radius, center[1] - radius)
    right_down_point = (center[0] + radius, center[1] + radius)
    draw.ellipse([left_up_point, right_down_point], fill=fill)

def draw_icon(image, icon, x_current, y_current, max_height):
    # Scale the icon to fit the max_height while maintaining aspect ratio
    aspect_ratio = icon.width / icon.height
    scaled_height = max_height
    scaled_width = int(aspect_ratio * scaled_height)
    # Resize the icon using LANCZOS resampling
    icon = icon.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
    # Calculate the mean color of the icon
    stat = ImageStat.Stat(icon)
    mean_color = stat.mean[:3]  # Get the mean of the R, G, B channels
    # Determine if the color is close to white
    if all(x > 100 for x in mean_color):  # You can adjust the threshold value
        # Create a black image of the same size
        black_icon = Image.new('RGB', icon.size, color='black')
        # Use the alpha channel of the original icon to apply it to the black image
        black_icon.putalpha(icon.getchannel('A'))
        icon = black_icon
    # Get the coordinates for the icon's top-left corner
    icon_top_left = (x_current, y_current - (scaled_height // 2))  # Center vertically with the text
    # Paste the icon onto the image, using the alpha channel of the icon as the mask
    image.paste(icon, icon_top_left, mask=icon)
    # Return the new x position, which is to the right of the icon we just drew
    return x_current + scaled_width

def draw_markdown_text(image, bold_font, bold_font2, regular_font, regular_font_italic, title, text_body, color, y_top, x_left, x_right, graphics_folder, padding=2):
    # Initialize the drawing context
    draw = ImageDraw.Draw(image)
    
    # Draw the title using the bold font
    draw.text((x_left, y_top), title.strip(), font=bold_font, fill=color)
    
    # Get title height and update y-coordinate for text body
    title_bbox = draw.textbbox((x_left, y_top), title.strip(), font=bold_font)
    title_height = title_bbox[3] - title_bbox[1]
    y_current = y_top + title_height + int(padding * 2)
    
    # Define line height using the regular font
    max_height = draw.textbbox((0, 0), 'Hy', font=regular_font)[3]  # 'Hy' for descenders and ascenders

    # Split the text body by lines
    lines = [x.strip() for x in text_body.split('\n')]

    # Function to handle the drawing of text parts with the appropriate style
    def draw_text_part(draw, x_current, y_current, word, font, fill):
        word += ' '  # Add space after each word for separation
        bbox = draw.textbbox((x_current, y_current), word, font=font)
        width = bbox[2] - bbox[0]
        if x_current + width > x_right:
            # If the word exceeds the line, move to the next line
            x_current = x_left
            y_current += max_height + padding
        draw.text((x_current, y_current), word, font=font, fill=fill)
        return x_current + width, y_current

    for line in lines:
        # Initialize x-coordinate for line
        x_current = x_left

        # Check for markdown bold and italic syntax
        bold_parts = line.split('**')
        for b, bold_part in enumerate(bold_parts):
            if b % 2 == 1:
                # This part is bold
                font = bold_font2
            else:
                font = regular_font  # Reset to regular font for non-bold parts

            # Split the part into italic parts and draw each one
            italic_parts = bold_part.split('*')
            for i, italic_part in enumerate(italic_parts):
                if i % 2 == 1:
                    # This part is italic
                    font = regular_font_italic
                else:
                    font = bold_font2 if b % 2 == 1 else regular_font

                words = italic_part.split(' ')
                for word in words:
                    if '[' in word and ']' in word:
                        # Handle icons in text
                        icon_key = word.split('[')[1].split(']')[0]
                        word = word.split('[')[0]
                        # Draw the word before the icon
                        x_current, y_current = draw_text_part(draw, x_current, y_current, word, font, "black")
                        # Load and draw the icon
                        icon = Image.open(f"{graphics_folder}/{icon_key}.png").convert('RGBA')
                        if icon:
                            x_current = draw_icon(image, icon, x_current, y_current+14, max_height+18)
                        continue  # Skip the rest of the loop and don't draw this word as text
                    # Draw the word
                    x_current, y_current = draw_text_part(draw, x_current, y_current, word, font, "black")
        # After a line is processed, move to the next line
        y_current += max_height + padding
    return image, y_current

def draw_markdown_text_centerv2(image, bold_font, bold_font2, regular_font, regular_font_italic, title, text_body, color, y_top, x_left, x_right, graphics_folder, padding=2):
    # Initialize the drawing context
    draw = ImageDraw.Draw(image)
    draw.text((x_left, y_top), title.strip(), font=bold_font, fill=color)
    # Define line height using the tallest font (usually the bold one) for consistency
    max_height = max(draw.textbbox((0, 0), 'Hy', font=font)[3] for font in [bold_font, bold_font2, regular_font, regular_font_italic])
    # Calculate the y-coordinate for the text body
    y_current = y_top + max_height + padding
    # Split the text body by lines
    lines = [x.strip() for x in text_body.split('\n')]
    for line in lines:
        words_and_icons = re.findall(r'\*\*.*?\*\*|\*.*?\*|\[.*?\]|\S+', line)
        x_current = x_left
        for word_or_icon in words_and_icons:
            # Strip markdown symbols for width calculation
            stripped_word = word_or_icon.strip('[]*')
            word_width = draw.textlength(stripped_word, font=regular_font) + padding
            # Check for line width overflow and wrap to the next line
            if x_current + word_width > x_right:
                y_current += max_height + padding  # Move to next line
                x_current = x_left  # Reset to left bound
            if word_or_icon.startswith('[') and word_or_icon.endswith(']'):
                # Handle icons in text
                icon_key = word_or_icon.strip('[]')
                icon_path = f"{graphics_folder}/{icon_key}.png"
                icon = Image.open(icon_path).convert('RGBA')
                aspect_ratio = icon.width / icon.height
                new_width = int(aspect_ratio * max_height)
                icon = icon.resize((new_width, max_height), Image.Resampling.LANCZOS)
                stat = ImageStat.Stat(icon)
                mean_color = stat.mean[:3] 
                if all(x > 100 for x in mean_color):
                    black_icon = Image.new('RGB', icon.size, color='black')
                    black_icon.putalpha(icon.getchannel('A'))
                    icon = black_icon
                icon_x_center = x_current
                icon_y_center = int(y_current + (max_height - icon.height) // 2)
                image.paste(icon, (int(icon_x_center), int(icon_y_center)), icon)
                x_current += new_width
            else:
                # Determine the font for this segment of text
                if '**' in word_or_icon:
                    font = bold_font2
                    word_or_icon = word_or_icon.strip('*')
                elif '*' in word_or_icon:
                    font = regular_font_italic
                    word_or_icon = word_or_icon.strip('*')
                else:
                    font = regular_font
                # Draw the text
                draw.text((x_current, y_current), stripped_word, font=font, fill=color)
                x_current += word_width
        # After a line is processed, move to the next line
        y_current += max_height + padding
    return image, y_current

def CreateTextImage(draw, astring, max_height, FontObj, color, padding):
    line_width = draw.textlength(astring, font=FontObj)
    line_image = Image.new('RGBA', (int(line_width), int(max_height)), (255, 255, 255, 0))
    line_draw = ImageDraw.Draw(line_image)
    line_draw.text((0, int(padding/2)), astring, font=FontObj, fill=color)
    return line_image

def create_icon_image(graphics_folder, icon_key, max_height):
    # './assets/graphics/ATTACK:Ranged:Ranged Volley:3+3.png'
    icon_path = f"{graphics_folder}/{icon_key}.png"
    if not os.path.isfile(icon_path):
        print(f"Invalid icon image {icon_path}")
        icon_path = f"{graphics_folder}/IconQuestion.png"
    icon = Image.open(icon_path).convert('RGBA')
    aspect_ratio = icon.width / icon.height
    new_width = int(aspect_ratio * max_height)
    icon = icon.resize((new_width, max_height), Image.Resampling.LANCZOS)
    stat = ImageStat.Stat(icon)
    mean_color = stat.mean[:3] 
    if all(x > 100 for x in mean_color):
        black_icon = Image.new('RGB', icon.size, color='black')
        black_icon.putalpha(icon.getchannel('A'))
        icon = black_icon
    return icon, new_width

def draw_markdown_text_centerv3(image, bold_font, bold_font2, regular_font, regular_font_italic, title, text_body, color, y_top, x_left, x_right, graphics_folder, padding=2):
    all_image_lines = []
    draw = ImageDraw.Draw(image)
    # Define line height using the tallest font (usually the bold one) for consistency
    max_height = max(draw.textbbox((0, 0), 'Hy', font=font)[3] for font in [bold_font, bold_font2, regular_font, regular_font_italic])
    line_image = CreateTextImage(draw, title.strip(), max_height, bold_font, color, padding)
    all_image_lines.append( {'img':line_image,'y':y_top, 'x':x_left} )
    #image.paste(line_image, (x_left, y_top), line_image)
    middle_x = (x_right + x_left) / 2
    # Calculate the y-coordinate for the text body
    y_current = y_top + max_height + padding
    # Split the text body by lines
    lines = [x.strip() for x in text_body.split('\n')]
    for line in lines:
        words_and_icons = re.findall(r'\*\*.*?\*\*|\*.*?\*|\[.*?\]|\S+', line)
        x_current = x_left
        for word_or_icon in words_and_icons:
            # Strip markdown symbols for width calculation
            stripped_word = word_or_icon.strip('[]*')
            word_width = draw.textlength(stripped_word, font=regular_font) + padding
            # Check for line width overflow and wrap to the next line
            if x_current + word_width > x_right:
                y_current += max_height + padding  # Move to next line
                x_current = x_left  # Reset to left bound
            if word_or_icon.startswith('[') and word_or_icon.endswith(']'):
                # Handle icons in text
                icon_key = word_or_icon.strip('[]')
                icon, new_width = create_icon_image(graphics_folder, icon_key, max_height)
                icon_x_center = x_current
                icon_y_center = int(y_current + (max_height - icon.height) // 2)
                #image.paste(icon, (int(icon_x_center), int(icon_y_center)), icon)
                all_image_lines.append( {'img':icon,'y':int(icon_y_center), 'x':int(icon_x_center)} )
                x_current += new_width
            else:
                # Determine the font for this segment of text
                if '**' in word_or_icon:
                    font = bold_font2
                    word_or_icon = word_or_icon.strip('*')
                elif '*' in word_or_icon:
                    font = regular_font_italic
                    word_or_icon = word_or_icon.strip('*')
                else:
                    font = regular_font
                # Draw the text
                #draw.text((x_current, y_current), stripped_word, font=font, fill=color)
                line_image = CreateTextImage(draw, f"{stripped_word} ", max_height, font, color, padding)
                all_image_lines.append( {'img':line_image,'y':y_current, 'x':x_current} )
                x_current += word_width
        # After a line is processed, move to the next line
        y_current += max_height + padding
    # First, group all images by their y-coordinate
    lines_by_y = defaultdict(list)
    for img_dict in all_image_lines:
        lines_by_y[img_dict['y']].append(img_dict)
    # Now iterate over each line and center-align the words
    middle_x = (x_right + x_left) / 2
    for y, line_images in lines_by_y.items():
        # Calculate the total width of the line
        total_line_width = sum(img_dict['img'].width for img_dict in line_images)
        # Calculate the starting x-coordinate for the line
        line_start_x = middle_x - (total_line_width // 2)
        # Paste each image, offsetting each one to the right of the previous
        current_x = line_start_x
        for img_dict in line_images:
            img = img_dict['img']
            # Paste the image onto the background image
            image.paste(img, (int(current_x), int(y)), img)
            # Update the current x-coordinate
            current_x += img.width
    return image, y_current

def draw_markdown_text_centerv1(image, bold_font, bold_font2, regular_font, regular_font_italic, title, text_body, color, y_top, x_left, x_right, graphics_folder, padding=2):
    # Initialize the drawing context
    draw = ImageDraw.Draw(image)
    # Draw the title using the bold font and center it
    title_width = draw.textbbox((0, 0), title.strip(), font=bold_font)[2]
    title_x = x_left + (x_right - x_left - title_width) // 2
    draw.text((title_x, y_top), title.strip(), font=bold_font, fill=color)
    
    # Calculate the y-coordinate for the text body
    title_height = bold_font.getmask(title.strip()).getbbox()[3]
    y_current = y_top + title_height + padding

    max_height = draw.textbbox((0, 0), 'Hy', font=regular_font)[3]  # 'Hy' for descenders and ascenders
    
    # Split the text body by lines
    lines = [x.strip() for x in text_body.split('\n')]

    for line in lines:
        # Get the width of the entire line and calculate the starting x-coordinate for centering
        line_width = draw.textlength(line, font=regular_font)
        x_current = x_left + (x_right - x_left - line_width) // 2

        # Split the line into words and icons
        words_and_icons = re.findall(r'\[.*?\]|\S+', line)  # Split line into words and [icons]

        for word_or_icon in words_and_icons:
            if '[' in word_or_icon and ']' in word_or_icon:
                # Handle icons in text
                icon_key = word_or_icon.strip('[]')
                icon = Image.open(f"{graphics_folder}/{icon_key}.png").convert('RGBA')
                if icon:
                    # Center the icon vertically and adjust x_current
                    icon_y_center = y_current + (max_height - icon.height) // 2
                    image.paste(icon, (x_current, icon_y_center), mask=icon)
                    x_current += icon.width
                continue  # Skip the rest of the loop and don't draw this word as text
            
            # Check for markdown bold and italic syntax
            if '**' in word_or_icon:
                font = bold_font2
                word_or_icon = word_or_icon.strip('*')
            elif '*' in word_or_icon:
                font = regular_font_italic
                word_or_icon = word_or_icon.strip('*')
            else:
                font = regular_font

            # Draw the word
            word_or_icon += ' '  # Add space after each word for separation
            word_width = draw.textlength(word_or_icon, font=font)
            draw.text((x_current, y_current), word_or_icon, font=font, fill=color)
            x_current += word_width

        # After a line is processed, move to the next line
        y_current += max_height + padding

    return image, y_current


class LayeredImageCanvas:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []

    def add_layer(self, image, x, y, depth):
        self.layers.append({
            'image': image,
            'x': x,
            'y': y,
            'depth': depth
        })
        # Sort layers by depth so that higher depth layers are rendered last (on top)
        self.layers.sort(key=lambda layer: layer['depth'])

    def render(self):
        # Create a blank canvas
        canvas = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        for layer in self.layers:
            canvas.paste(layer['image'], (layer['x'], layer['y']), layer['image'])
        return canvas

def make_bottom_transparent(image, rows):
    # Check if the image has an alpha channel, if not, add one
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    # Load the alpha channel (mask) of the image
    alpha = image.split()[3]
    # Create a new alpha channel with the same size as the original image, fully opaque
    new_alpha = Image.new('L', image.size, 255)
    # Process the bottom 20 rows
    for y in range(image.height - rows, image.height):
        for x in range(image.size[0]):
            new_alpha.putpixel((x, y), 0)
    # Put the new alpha channel back into the image
    image.putalpha(new_alpha)
    return image

def crop_transparent_edges(image):
    # Ensure image has an alpha channel
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    # Get the alpha channel of the image
    alpha = image.split()[-1]
    # Get the bounding box of the non-zero regions in the alpha channel
    bbox = alpha.getbbox()
    # If the image is completely transparent, return the original image
    if bbox is None:
        return image
    # Crop the image with the bounding box
    cropped_image = image.crop(bbox)
    return cropped_image

def add_background_to_image(original_image, faction):
    faction_color = False
    if faction in FactionColors:
        faction_color = FactionColors[faction]
    # Set default background color to transparent if faction_color is None or False
    background_color = (0, 0, 0, 0) if not faction_color else faction_color
    # Create a new image with the same size as the original and the specified background color
    new_image = Image.new("RGBA", original_image.size, background_color)
    # Since the original image may have transparency, we use it as the mask for itself
    new_image.paste(original_image, (0, 0), original_image)
    return new_image

def generate_ncu_bar(hor_bar1, hor_large_bar):
    # Step 1 & 2
    first_new_image_height = int(hor_large_bar.height * 1.5)
    first_new_image = Image.new('RGBA', (hor_large_bar.width, first_new_image_height))
    first_new_image.paste(hor_large_bar, (0, 0))
    first_new_image.paste(hor_large_bar, (0, hor_large_bar.height))

    # Step 3 to 6
    second_new_image_height = first_new_image_height + hor_bar1.height
    second_new_image = Image.new('RGBA', (hor_large_bar.width, second_new_image_height))

    # Center the first new image vertically on the second new image
    offset_y = (second_new_image_height - first_new_image_height) // 2
    second_new_image.paste(first_new_image, (0, offset_y))

    # Paste hor_bar1 at the top and bottom
    second_new_image.paste(hor_bar1, (0, 0))
    second_new_image.paste(hor_bar1, (0, second_new_image_height - hor_bar1.height))

    # Calculate the positions for the additional hor_large_bar images
    third_bar_position = int(second_new_image_height * 0.333)
    sixth_bar_position = int(second_new_image_height * 0.666)

    second_new_image.paste(hor_bar1, (0, third_bar_position - hor_bar1.height // 2))
    second_new_image.paste(hor_bar1, (0, sixth_bar_position - hor_bar1.height // 2))
    return second_new_image


def BuildNcuCardFactionWithData(NcuData, units_folder, attachments_folder, graphics_folder, tactics_folder, AsoiafFonts, AsoiafData, ncus_folder):
    print(f"Creating {NcuData['Name']}")
    # {'Faction': 'Neutral', 'Name': 'Lord Varys, The Spider', 'Character': 'Lord Varys', 'Cost': '4', 'Names': 'Little Birds', 'Descriptions': 
    # 'Varys begins the iendly unit.\n[SWORDS]: 1 enemy suffers 3 Hits.\n[LETTER]: Draw 1 Tactics card.\n[HORSE]: 1 friendly unit shifts 3".', 
    # 'Requirements': '', 'Boxes': 'SIF505', 'Id': '30403', 'Version': '2021-S03', 'Quote': '"Varys has ."', 'Restrictions': ''}
    #pdb.set_trace()
    faction = NcuData['Faction']
    faction_text_clean = re.sub(r'[^A-Za-z]', '', faction)
    NcuId = NcuData['Id']
    faction_crest = False
    scaled_faction_crest = False
    if f"{faction_text_clean}".strip() != "":
        faction_crest = Image.open(f"{tactics_folder}Crest{faction_text_clean}.webp").convert('RGBA').rotate(-11, expand=True)
        width, height = [int(x*0.63) for x in faction_crest.size]
        scaled_faction_crest = faction_crest.resize((width, height))
    ncu_faction_bg_image = Image.open(f"{tactics_folder}Bg_{faction_text_clean}.jpg").convert('RGBA')
    FactionColor = "#7FDBFF" 
    if faction in FactionColors:
        FactionColor = FactionColors[faction]
    ArmyAttackAndAbilitiesBorderColor = "Gold"
    if faction in ArmyAttackAndAbilitiesBorderColors:
        ArmyAttackAndAbilitiesBorderColor = ArmyAttackAndAbilitiesBorderColors[faction]
    canvas = LayeredImageCanvas(ncu_faction_bg_image.size[0], ncu_faction_bg_image.size[1])

    vert_bar1 = Image.open(f"{attachments_folder}Bar{faction_text_clean}.webp").convert('RGBA').rotate(90, expand=True)
    vert_bar2 = vert_bar1.copy()
    vert_bar3 = vert_bar1.copy()
    hor_large_bar = Image.open(f"{units_folder}LargeBar{faction_text_clean}.webp").convert('RGBA')
    hor_bar1 = Image.open(f"{attachments_folder}Bar{faction_text_clean}.webp").convert('RGBA')
    hor_bar2 = hor_bar1.copy()
    hor_bar3 = hor_bar1.copy()
    hor_bar4 = hor_bar1.copy()
    ncu_portrait = Image.open(f"{ncus_folder}{NcuId}.jpg").convert('RGBA').resize((273, 312))
    UnitTypeNcuForFactionImage = Image.open(f"{ncus_folder}UnitTypeNCU{faction_text_clean}.webp").convert('RGBA') 
    width, height = [int(x*0.98) for x in UnitTypeNcuForFactionImage.size]
    UnitTypeNcuForFactionImage = UnitTypeNcuForFactionImage.resize((width, height))
    UnitTypeNcuForFactionImage = UnitTypeNcuForFactionImage.crop((0,10,UnitTypeNcuForFactionImage.size[0],UnitTypeNcuForFactionImage.size[1]))
    #We'll add these in from left to right from top to bottom
    DecorStar1 = Image.open(f"{tactics_folder}Decor{faction_text_clean}.webp").convert('RGBA')
    DecorStar2 = DecorStar1.copy()
    DecorStar3 = DecorStar1.copy()
    DecorStar4 = DecorStar1.copy()
    DecorStar5 = DecorStar1.copy()
    DecorStar6 = DecorStar1.copy()
    DecorStar7 = DecorStar1.copy()
    DecorStar8 = DecorStar1.copy()
    DecorStar9 = DecorStar1.copy()
    DecorStar10 = DecorStar1.copy()
    DecorStar11 = DecorStar1.copy()
    DecorStar12 = DecorStar1.copy()
    tan_background_for_text = Image.open(f"{units_folder}SkillsBg.webp").convert('RGBA')
    hor_natticed_bar_below_portrait = generate_ncu_bar(hor_bar1, hor_large_bar)

    left_right_top_offset = 40
    top_to_bottom_border_height = ncu_faction_bg_image.size[1] - int(left_right_top_offset * 2)
    left_to_right_border_width = ncu_faction_bg_image.size[0] - int(left_right_top_offset * 2)
    vert_bar1 = vert_bar1.crop( (0, 0, vert_bar1.size[0], top_to_bottom_border_height) )
    vert_bar2 = vert_bar2.crop( (0, 0, vert_bar2.size[0], top_to_bottom_border_height) )
    vert_bar3 = vert_bar3.crop( (0, 0, vert_bar3.size[0], ncu_portrait.size[1]) )
    hor_bar1 = hor_bar1.crop((0, 0, left_to_right_border_width, hor_bar1.size[1]))
    hor_bar2 = hor_bar2.crop((0, 0, left_to_right_border_width, hor_bar2.size[1]))
    hor_bar3 = hor_bar3.crop((0, 0, left_to_right_border_width, hor_bar3.size[1]))

    hor_natticed_bar_below_portrait = hor_natticed_bar_below_portrait.crop((0,0, left_to_right_border_width - ncu_portrait.size[0], hor_natticed_bar_below_portrait.size[1]))
    hor_bar4 = hor_bar4.crop((0, 0, hor_natticed_bar_below_portrait.size[0], hor_bar3.size[1]))

    half_height_width = int(hor_bar1.size[1]/2)
    canvas.add_layer(ncu_faction_bg_image, 0, 0, depth=0)
    canvas.add_layer(ncu_portrait, left_right_top_offset, left_right_top_offset, depth=0)
    xoff = left_right_top_offset+ ncu_portrait.size[0]
    yoff = left_right_top_offset+ncu_portrait.size[1]-hor_natticed_bar_below_portrait.size[1]+half_height_width
    canvas.add_layer(hor_natticed_bar_below_portrait, xoff, yoff, depth=1)
    canvas.add_layer(UnitTypeNcuForFactionImage, xoff+half_height_width, yoff, depth=2)
    if scaled_faction_crest:
        canvas.add_layer(scaled_faction_crest, ncu_faction_bg_image.size[0]-left_right_top_offset-scaled_faction_crest.size[0]+2, yoff- (half_height_width*2), depth=4)
    canvas.add_layer(hor_bar4, xoff, yoff, depth=3)

    canvas.add_layer(vert_bar1, left_right_top_offset-half_height_width, left_right_top_offset, depth=1)
    canvas.add_layer(vert_bar2, ncu_faction_bg_image.size[0]-half_height_width-left_right_top_offset, left_right_top_offset, depth=1)
    canvas.add_layer(vert_bar3, left_right_top_offset+ncu_portrait.size[0]-half_height_width, left_right_top_offset, depth=1)

    canvas.add_layer(hor_bar1, left_right_top_offset, left_right_top_offset, depth=1)
    canvas.add_layer(hor_bar2, left_right_top_offset, left_right_top_offset+ncu_portrait.size[1]-half_height_width, depth=1)
    canvas.add_layer(hor_bar3, left_right_top_offset, ncu_faction_bg_image.size[1] - left_right_top_offset - half_height_width, depth=1)
    
    decorOffset = int(DecorStar1.size[0]/2)
    xoff = left_right_top_offset-decorOffset
    yoff = left_right_top_offset-decorOffset+half_height_width
    canvas.add_layer(DecorStar1, xoff, yoff, depth=5)
    canvas.add_layer(DecorStar5, xoff, yoff + int(ncu_portrait.size[1]/2)-half_height_width, depth=5)
    top_left_coords = [xoff+0, yoff + ncu_portrait.size[1]-half_height_width]
    canvas.add_layer(DecorStar7, top_left_coords[0], top_left_coords[1], depth=5)
    canvas.add_layer(DecorStar9, xoff+left_to_right_border_width, yoff, depth=5)
    top_right_coords = [xoff+left_to_right_border_width, yoff+ncu_portrait.size[1]-half_height_width]
    canvas.add_layer(DecorStar10, top_right_coords[0], top_right_coords[1], depth=5)
    xoff += ncu_portrait.size[0]
    canvas.add_layer(DecorStar2, xoff, yoff, depth=5)
    canvas.add_layer(DecorStar6, xoff, yoff + int(ncu_portrait.size[1]/2)-half_height_width, depth=5)
    canvas.add_layer(DecorStar8, xoff, yoff + ncu_portrait.size[1]-half_height_width, depth=5)
    
    xoff -= int(ncu_portrait.size[0]/2)
    canvas.add_layer(DecorStar3, xoff, yoff, depth=5)
    canvas.add_layer(DecorStar4, xoff, yoff + ncu_portrait.size[1]-half_height_width, depth=5)
    bottom_left_coords = [left_right_top_offset-decorOffset, left_right_top_offset + top_to_bottom_border_height-decorOffset]
    canvas.add_layer(DecorStar11, bottom_left_coords[0], bottom_left_coords[1], depth=5)
    bottom_right_coords = [left_right_top_offset-decorOffset+left_to_right_border_width, left_right_top_offset + top_to_bottom_border_height-decorOffset]
    canvas.add_layer(DecorStar12, bottom_right_coords[0], bottom_right_coords[1], depth=5)

    # Calculate the width and height based on the coordinates
    target_width = top_right_coords[0] - top_left_coords[0]  # Assuming top_right and top_left have the same 'y' value
    target_height = bottom_left_coords[1] - top_left_coords[1] 
    tan_background_for_text = tan_background_for_text.resize((target_width, target_height), Image.Resampling.LANCZOS)
    canvas.add_layer(tan_background_for_text, top_left_coords[0]+decorOffset, top_left_coords[1]+decorOffset, depth=0)
    #return canvas.render()
    ncu_card = canvas.render()
    GBFont = AsoiafFonts.get('Tuff-Bold-40',ImageFont.load_default())
    TN = AsoiafFonts.get('Tuff-Bold-40',ImageFont.load_default())
    TN30 = AsoiafFonts.get('Tuff-Normal-34',ImageFont.load_default())
    TN30I = AsoiafFonts.get('Tuff-Italic-34',ImageFont.load_default())
    descriptions_names = [x.strip() for x in NcuData['Names'].strip().split('/') if not any([x.strip().startswith("Loyalty:"), x.strip().startswith("Rules:")]) ]
    descriptions = [x.strip() for x in NcuData['Descriptions'].strip().split('/')]
    textBoundLeft = 100
    textBoundRight = 650
    yAbilityOffset = 380
    for i in range(len(descriptions_names)):
        nm = descriptions_names[i]
        ds = descriptions[i]
        if i + 1 == len(descriptions_names) and len(descriptions_names) != len(descriptions):
            ds = "\n".join( descriptions[i:] )
        ncu_card, yAbilityOffset = draw_markdown_text_centerv3(ncu_card, GBFont, TN, TN30, TN30I, nm.upper(), ds, FactionColor, yAbilityOffset-4, textBoundLeft, textBoundRight, graphics_folder, padding=4)
    draw = ImageDraw.Draw(ncu_card)

    TuffBoldFont = AsoiafFonts.get('Tuff-Bold-47', ImageFont.load_default()) 
    TuffBoldFontSmall = AsoiafFonts.get('Tuff-Bold-30', ImageFont.load_default())
    nameOffsetX = -26
    nameOffsetY = 20
    if ',' in NcuData['Name'].upper():
        lines = NcuData['Name'].upper().split(',')
        text_lines_list, hadAComma = split_name_string(lines[0], amnt=11)
        text_lines_list2, hadAComma = split_name_string(lines[1], amnt=18)
        if len(text_lines_list) == 1:
            draw_centered_text(draw, (540+nameOffsetX, 100+nameOffsetY), [lines[0]], TuffBoldFont, "white", line_padding=10)
            if len(text_lines_list2) == 1:
                draw_centered_text(draw, (540+nameOffsetX, 104+nameOffsetY + TuffBoldFont.size ), [lines[1]], TuffBoldFontSmall, "white", line_padding=10)
            else:
                draw_centered_text(draw, (540+nameOffsetX, 104+nameOffsetY + TuffBoldFont.size ), [text_lines_list2[0]], TuffBoldFontSmall, "white", line_padding=10)
                draw_centered_text(draw, (540+nameOffsetX, 104+nameOffsetY + TuffBoldFont.size + TuffBoldFontSmall.size), [text_lines_list2[1]], TuffBoldFontSmall, "white", line_padding=10)
        else:
            draw_centered_text(draw, (540+nameOffsetX, 80+nameOffsetY), [text_lines_list[0]], TuffBoldFont, "white", line_padding=10)
            draw_centered_text(draw, (540+nameOffsetX, 80+nameOffsetY + TuffBoldFont.size), [text_lines_list[1]], TuffBoldFont, "white", line_padding=10)
            if len(text_lines_list2) == 1:
                draw_centered_text(draw, (540+nameOffsetX, 88+nameOffsetY + (TuffBoldFont.size*1) + TuffBoldFontSmall.size+2 ), [lines[1]], TuffBoldFontSmall, "white", line_padding=10)
            else:
                #draw_centered_text(draw, (540+nameOffsetX, 88+nameOffsetY + (TuffBoldFont.size*2) ), [lines[1]], TuffBoldFontSmall, "white", line_padding=10)
                draw_centered_text(draw, (540+nameOffsetX, 88+nameOffsetY + (TuffBoldFont.size*1) + TuffBoldFontSmall.size+2 ), [text_lines_list2[0]], TuffBoldFontSmall, "white", line_padding=10)
                draw_centered_text(draw, (540+nameOffsetX, 88+nameOffsetY + (TuffBoldFont.size*1) + (TuffBoldFontSmall.size*2)+2 ), [text_lines_list2[1]], TuffBoldFontSmall, "white", line_padding=10)
    else:
        text_lines_list, hadAComma = split_name_string(NcuData['Name'].upper(), amnt=11)
        if len(text_lines_list) == 1:
            draw_centered_text(draw, (540+nameOffsetX, 120+nameOffsetY), [text_lines_list[0]], TuffBoldFont, "white", line_padding=10)
        else:
            draw_centered_text(draw, (540+nameOffsetX, 100+nameOffsetY), [text_lines_list[0]], TuffBoldFont, "white", line_padding=10)
            draw_centered_text(draw, (540+nameOffsetX, 104+nameOffsetY + TuffBoldFont.size ), [text_lines_list[1]], TuffBoldFont, "white", line_padding=10)

    return ncu_card
    # 

    vert_bar1 = Image.open(f"{attachments_folder}Bar{faction_text_clean}.webp").convert('RGBA').rotate(90, expand=True)
    fp = f"{tactics_folder}LargeBar{faction_text_clean}.webp"
    if not os.path.isfile(fp):
        fp = f"{units_folder}LargeBar{faction_text_clean}.webp"
    vert_large_bar1 = Image.open(fp).convert('RGBA').rotate(90, expand=True)
    vert_bar2 = vert_bar1.copy()
    vert_bar3 = vert_bar1.copy()
    vert_bar4 = vert_bar1.copy()
    vert_bar5 = vert_bar1.copy()
    vert_large_bar2 = vert_large_bar1.copy()
    hor_bar1 = vert_bar1.copy().rotate(-90, expand=True)
    hor_bar2 = hor_bar1.copy()
    hor_bar3 = hor_bar1.copy()
    hor_large_bar1 = vert_large_bar1.copy().rotate(-90, expand=True)
    if f"{UnitType}" != 'None':
        fp = f"{attachments_folder}UnitType.{UnitTypeClean}{faction_text_clean}.webp"
        if not os.path.isfile(fp):
            fp = f"{units_folder}UnitType.{UnitTypeClean}{faction_text_clean}.webp"
        unit_type_image = Image.open(fp).convert('RGBA')
    faction_crest = Image.open(f"{tactics_folder}Crest{faction_text_clean}.webp").convert('RGBA')
    width, height = [int(x*0.7) for x in faction_crest.size]
    scaled_faction_crest = faction_crest.resize((width, height))
    ncu_portrait = Image.open(f"{attachments_folder}{AttachId}.jpg").convert('RGBA')

    frame_corner_right = Image.open(f"{units_folder}Corner{faction_text_clean}.webp").convert('RGBA').transpose(Image.FLIP_TOP_BOTTOM).resize((229, 702))
    frame_corner_left = frame_corner_right.copy().transpose(Image.FLIP_LEFT_RIGHT)
    skills_tan_background_for_text = Image.open(f"{units_folder}SkillsBg.webp").convert('RGBA')
    width, height = [int(x*1.1) for x in skills_tan_background_for_text.size]
    skills_tan_background_for_text = skills_tan_background_for_text.resize((width, height))
    SkillBottom = Image.open(f"{units_folder}SkillBottom{faction_text_clean}.webp").convert('RGBA')
    SkillBottom = SkillBottom.resize((int(SkillBottom.size[0]*1.05), int(SkillBottom.size[1]*1.2)))
    SkillDivider = Image.open(f"{units_folder}Divider{faction_text_clean}.webp").convert('RGBA')
    SkillDivider = SkillDivider.resize((int(SkillDivider.size[0]*1.1), SkillDivider.size[1]))
    DecorStar1 = Image.open(f"{tactics_folder}Decor{faction_text_clean}.webp").convert('RGBA')
    DecorStar2 = DecorStar1.copy()
    DecorStar3 = DecorStar1.copy()
    DecorStar4 = DecorStar1.copy()
    DecorStar5 = DecorStar1.copy()
    DecorStar6 = DecorStar1.copy()
    DecorStar7 = DecorStar1.copy()


    left_right_top_offset = 45
    yAbilityOffset = 348
    dividerOffset = 20
    SkillBarsOffset = 131
    textBoundLeft, textBoundRight = [150, 740]
    canvas.add_layer(ncu_faction_bg_image, 0, 0, depth=0)
    if isCommander:
        ncu_portrait = ncu_portrait.resize(( 243, 252 ))
        canvas.add_layer(vert_large_bar1, ncu_portrait.size[0], -(vert_large_bar1.size[1]-ncu_portrait.size[1]), depth=3)
        canvas.add_layer(unit_type_image, ncu_portrait.size[0]-9, 0, depth=5)
        if faction == 'Neutral':
            scaled_faction_crest = scaled_faction_crest.resize( ( scaled_faction_crest.size[0], int(scaled_faction_crest.size[1]*0.9) ) )
        canvas.add_layer(scaled_faction_crest, ncu_portrait.size[0]-24, ncu_portrait.size[1] - 65, depth=5)
        xoff = ncu_portrait.size[0] - int(vert_bar1.size[0]/2)
        canvas.add_layer(vert_bar1, xoff, -(vert_bar1.size[1]-ncu_portrait.size[1]), depth=4)
        xoff2 = ncu_portrait.size[0] + vert_large_bar1.size[0] - int(vert_bar2.size[0]/2)
        canvas.add_layer(vert_bar2, xoff2, -(vert_bar2.size[1]-ncu_portrait.size[1]), depth=4)
        canvas.add_layer(frame_corner_left, xoff - frame_corner_left.size[0] + vert_bar1.size[0] - 8, -frame_corner_left.size[1]+ncu_portrait.size[1]+8, depth=2)
        canvas.add_layer(frame_corner_right, xoff2 + 8, -frame_corner_left.size[1]+ncu_portrait.size[1]+8, depth=2)
        canvas.add_layer(hor_bar1, 0, ncu_portrait.size[1] -4, depth=4)
        canvas.add_layer(hor_large_bar1, 0, ncu_portrait.size[1], depth=3)
        half_height_width = int(hor_bar2.size[1]/2)
        yoff = hor_large_bar1.size[1] +  ncu_portrait.size[1] - half_height_width
        canvas.add_layer(hor_bar2, 0, yoff, depth=4)
        canvas.add_layer(vert_bar3, left_right_top_offset, yoff + half_height_width, depth=3)
        canvas.add_layer(vert_large_bar2, left_right_top_offset, yoff + half_height_width, depth=2)
        xoff3 = left_right_top_offset + vert_large_bar2.size[0] - half_height_width
        yoff3 = yoff + half_height_width
        canvas.add_layer(vert_bar4, xoff3, yoff3, depth=3)
        canvas.add_layer(skills_tan_background_for_text, xoff3, yoff3-6, depth=2 )
        canvas.add_layer(ncu_portrait, 0, 0, depth=1)
        canvas.add_layer(DecorStar1, left_right_top_offset - 12, 315, depth=5 )
        canvas.add_layer(DecorStar2, left_right_top_offset + vert_large_bar1.size[0] - 20, 315, depth=5 )
    else:
        ncu_portrait = ncu_portrait.resize(( 197, 248 ))
        boundary_width = ncu_faction_bg_image.size[0] - (left_right_top_offset * 2)
        # got to do some cropping of horozontal bars
        hor_bar1 = hor_bar1.crop( (0, 0, boundary_width, hor_bar1.size[1]) ) # crop past boundary width
        hor_bar2 = hor_bar2.crop( (0, 0, boundary_width, hor_bar2.size[1]) )
        hor_bar3 = hor_bar3.crop( (0, 0, boundary_width, hor_bar3.size[1]) )
        half_height_width = int(hor_bar2.size[1]/2)
        canvas.add_layer(ncu_portrait, left_right_top_offset, left_right_top_offset, depth=1)
        canvas.add_layer(vert_bar1, left_right_top_offset-half_height_width, left_right_top_offset, depth=4)
        yoff = left_right_top_offset-half_height_width+ncu_portrait.size[1]-half_height_width
        left_line_inner_offset = 50
        canvas.add_layer(vert_large_bar2, left_right_top_offset-half_height_width, yoff+left_line_inner_offset, depth=2)
        xoff = left_right_top_offset-half_height_width + vert_large_bar2.size[0] - (half_height_width*2)
        canvas.add_layer(vert_bar5, xoff, left_right_top_offset + ncu_portrait.size[1] + left_line_inner_offset - half_height_width, depth=4) # second vert bar from left


        canvas.add_layer(hor_bar1, left_right_top_offset, left_right_top_offset-half_height_width+half_height_width, depth=4)
        canvas.add_layer(hor_bar2, left_right_top_offset, yoff, depth=4)
        hor_large_bar1 = hor_large_bar1.crop((0, 0, hor_bar2.size[0], int(hor_large_bar1.height // 2)))
        #hor_bar3 = hor_bar3.crop((0,0, hor_large_bar1.size[0], hor_large_bar1.size[1]))
        canvas.add_layer(hor_large_bar1, left_right_top_offset, yoff, depth=3)
        canvas.add_layer(hor_bar3, left_right_top_offset, yoff + hor_large_bar1.size[1], depth=3)
        vert2_x = boundary_width+left_right_top_offset-half_height_width
        vert2_y = left_right_top_offset
        #canvas.add_layer(vert_bar2, boundary_width+left_right_top_offset-half_height_width, left_right_top_offset, depth=2)
        canvas.add_layer(vert_large_bar1, left_right_top_offset+ncu_portrait.size[0]-half_height_width, left_right_top_offset, depth=2)
        canvas.add_layer(vert_bar3, left_right_top_offset+ncu_portrait.size[0]-half_height_width, left_right_top_offset, depth=2)
        canvas.add_layer(vert_bar4, left_right_top_offset+ncu_portrait.size[0]-(half_height_width*2)+vert_large_bar1.size[0], left_right_top_offset, depth=2)
        if f"{UnitType}" != 'None':
            crop_rectangle = (0, 20, unit_type_image.width, unit_type_image.height)
            unit_type_image = unit_type_image.crop(crop_rectangle)
            width, height = [int(x*0.9) for x in unit_type_image.size]
            unit_type_image = unit_type_image.resize((width, height))
            canvas.add_layer(unit_type_image, left_right_top_offset+ncu_portrait.size[0]-9, left_right_top_offset+half_height_width, depth=3)
        width, height = [int(x*0.6) for x in faction_crest.size]
        scaled_faction_crest = faction_crest.resize((width, height))
        if faction == 'Neutral':
            scaled_faction_crest = scaled_faction_crest.resize( ( scaled_faction_crest.size[0], int(scaled_faction_crest.size[1]*0.9) ) )
        canvas.add_layer(scaled_faction_crest, left_right_top_offset+ncu_portrait.size[0]-18, left_right_top_offset + int(ncu_portrait.size[1]/1.55) - 5, depth=5)
        left = frame_corner_left.width - 80
        upper = frame_corner_left.height - 80
        right = frame_corner_left.width
        lower = frame_corner_left.height
        # Define the crop rectangle
        crop_rectangle = (left, upper, right, lower)
        # Perform the crop
        frame_corner_left = frame_corner_left.crop(crop_rectangle)
        frame_corner_right = frame_corner_left.transpose(Image.FLIP_LEFT_RIGHT)
        canvas.add_layer(frame_corner_left, left_right_top_offset + ncu_portrait.size[0] - frame_corner_left.size[0]+4, left_right_top_offset + ncu_portrait.size[1] - frame_corner_left.size[1]-4, depth=1)
        canvas.add_layer(frame_corner_right, left_right_top_offset + ncu_portrait.size[0] + vert_large_bar1.size[0]-8, left_right_top_offset + ncu_portrait.size[1] - frame_corner_right.size[1]-4, depth=1)
        skills_tan_background_for_text = skills_tan_background_for_text.resize((skills_tan_background_for_text.size[0]-80, skills_tan_background_for_text.size[1]))
        SkillBottom = SkillBottom.crop((0,0, skills_tan_background_for_text.size[0], int(SkillBottom.size[1])))
        SkillDivider = SkillDivider.crop((0,0, skills_tan_background_for_text.size[0]+40,SkillDivider.size[1]))

        yAbilityOffset = 332
        SkillBarsOffset = 117
        textBoundLeft, textBoundRight = [134, 704]

        canvas.add_layer(skills_tan_background_for_text, xoff, yAbilityOffset-6, depth=2 )
        leftd_X = 24
        canvas.add_layer(DecorStar1, leftd_X, 33, depth=5 )
        canvas.add_layer(DecorStar2, leftd_X, 265, depth=5 )
        canvas.add_layer(DecorStar3, leftd_X, 306, depth=5 )
        canvas.add_layer(DecorStar4, 95, 306, depth=5 )
        #canvas.add_layer(DecorStar5, 113, 352, depth=5 )
        #canvas.add_layer(DecorStar6, 698, 284, depth=5 )
        #canvas.add_layer(DecorStar7, xoff, yoff, depth=5 )

    FactionColor = "#7FDBFF" 
    if faction in FactionColors:
        FactionColor = FactionColors[faction]
    ArmyAttackAndAbilitiesBorderColor = "Gold"
    if faction in ArmyAttackAndAbilitiesBorderColors:
        ArmyAttackAndAbilitiesBorderColor = ArmyAttackAndAbilitiesBorderColors[faction]

    ncu_card = canvas.render()
    yAbilityOffset += dividerOffset
    def MakeAttackIcon(atktype):
        # Load the images
        AtkTypeBg = Image.open(f"{units_folder}AttackTypeBg{ArmyAttackAndAbilitiesBorderColor}.webp").convert('RGBA')
        AtkTypeIcon = Image.open(f"{units_folder}AttackType.{atktype}{ArmyAttackAndAbilitiesBorderColor}.webp").convert('RGBA')
        # Resize border to be slightly larger than its original size
        border_scaling_factor = 1.1  # 10% larger than the original size
        new_border_width, new_border_height = [int(x * border_scaling_factor) for x in AtkTypeIcon.size]
        AtkTypeIcon = AtkTypeIcon.resize((new_border_width, new_border_height), resample=Image.LANCZOS)
        # Create a new image with the same size as the resized border
        new_image = Image.new('RGBA', (new_border_width, new_border_height), (255, 255, 255, 0))
        # Calculate the position to paste the sword image so it is centered left and right
        sword_width, sword_height = AtkTypeBg.size
        x_position = (new_image.width - sword_width) // 2
        y_position = (new_image.height - sword_height) // 2
        # Paste the sword image onto the new image
        new_image.paste(AtkTypeBg, (x_position, y_position), AtkTypeBg)
        # Paste the resized border image onto the new image with sword
        new_image.paste(AtkTypeIcon, (0, 0), AtkTypeIcon)
        width, height = [int(x*0.95) for x in new_image.size]
        new_image = new_image.resize((width, height))
        return new_image
    def CheckImagePath(imgtype):
        imagepath = f"{units_folder}Skill{imgtype}{ArmyAttackAndAbilitiesBorderColor}.webp"
        if not os.path.exists(imagepath):
            if ArmyAttackAndAbilitiesBorderColor == "Gold":
                imagepath = f"{units_folder}Skill{imgtype}Silver.webp"
            else:
                imagepath = f"{units_folder}Skill{imgtype}Gold.webp"
        return imagepath
    SkillsAndAbiitiesIconsTable = {
        "F": Image.open(CheckImagePath("Faith")).convert('RGBA'),
        "Fire": Image.open(CheckImagePath("Fire")).convert('RGBA'),
        "M":MakeAttackIcon("Melee"),
        "Morale":Image.open(f"{graphics_folder}/IconMorale.png").convert('RGBA'),
        "P":Image.open(CheckImagePath("Pillage")).convert('RGBA'),
        "R":MakeAttackIcon("Ranged"),
        "V":Image.open(CheckImagePath("Venom")).convert('RGBA'),
        "W":Image.open(CheckImagePath("Wounds")).convert('RGBA'),
    }

    def create_combined_vertical_image(skill_icon_image, skill_stat_image, font, text):
        # Calculate the width and height needed for the new image
        width = max(skill_icon_image.width, skill_stat_image.width)
        height = skill_icon_image.height + skill_stat_image.height - 20  # Overlap by 20px
        # Create a new image with the calculated width and height
        combined_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))  # Transparent background
        # Calculate X-axis and Y-axis centering for the text on the stat image
        draw = ImageDraw.Draw(skill_stat_image)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        # Calculate the X and Y position to center the text
        text_x = (skill_stat_image.width - text_width) // 2
        text_y = (skill_stat_image.height - text_height) // 2
        # Draw the text onto the stat image
        draw.text((text_x, text_y), text, font=font, fill="white")
        # Calculate X-axis centering for the Morale image
        Morale_x_center = (width - skill_icon_image.width) // 2
        # Paste the Morale image onto the combined image, centered
        # Calculate X-axis centering for the stat image
        stat_x_center = (width - skill_stat_image.width) // 2
        # Calculate the Y-axis position for the stat image (right below the Morale image -20px)
        stat_y_position = skill_icon_image.height - 20
        # Paste the stat image onto the combined image, centered and below the Morale image
        combined_image.paste(skill_stat_image, (stat_x_center, stat_y_position), skill_stat_image)
        combined_image.paste(skill_icon_image, (Morale_x_center, 0), skill_icon_image)
        width, height = [int(x*0.9) for x in combined_image.size]
        combined_image = combined_image.resize((width, height))
        return combined_image

    def split_string_by_trailing_digits(s):
        match = re.search(r'^(.*?)(\d+)$', s)
        if match:
            return True, match.group(1), match.group(2)
        else:
            return False, s, ''
    dividerYPadding = 0
    def addDivider(x, y):
        div = SkillDivider.copy()
        ncu_card.paste(div, (x, y+dividerYPadding), div)
        return div.size[1] + dividerOffset + int(dividerYPadding/2)
    if 'Abilities' in NcuData and NcuData['Abilities']:
        backofcardabilities = [x.lower() for x in ['adaptive']] # There is nothing in the data that differentiates a back of card ability so we will have to manually set it here.
        all_abilities = [x.strip() for x in NcuData['Abilities'].strip().split('/') if x.strip().lower() not in backofcardabilities and not x.strip().lower().startswith('loyalty:')]
        copy_all_abilities = all_abilities.copy()
        for ability_text in copy_all_abilities:
            try:
                [x for x in AsoiafData['newskills'] if x['Name'].lower() == ability_text.lower()][0]
            except IndexError as e:
                all_abilities.remove(ability_text)
                continue
        if len(all_abilities) > 3: # only one card with this that caused problems but this fixed it
            SkillDivider = SkillDivider.resize(( SkillDivider.size[0], int(SkillDivider.size[1]/2) ))
        for index in range(len(all_abilities)):
            ability = all_abilities[index]
            skillability_icon_images = []
            try:
                skilldata = [x for x in AsoiafData['newskills'] if x['Name'].strip().lower() == ability.lower()][0]
            except Exception as e:
                print("Ran into an error at:\nskilldata = [x for x in AsoiafData['newskills'] if x['Name'].lower() == ability.lower()][0]")
                print(str(e))
                sys.exit(1)
                #pdb.set_trace()
            skillScalePercent = 0.9
            if ability.startswith(f"Order:"):
                sk = Image.open(f"{units_folder}SkillOrder{ArmyAttackAndAbilitiesBorderColor}.webp").convert('RGBA')
                width, height = [int(x*skillScalePercent) for x in sk.size]
                sk = sk.resize((width, height))
                skillability_icon_images.append( [sk,[10,0]] )
            elif 'Icons' in skilldata and skilldata['Icons']:
                split_skills = skilldata['Icons'].split(',')
                for skill in split_skills:
                    # Some units have a Morale5 ability which is unique so we have to handle that (but I made it so it can handle other situations too just in case)
                    ended_with_digits, text, digits = split_string_by_trailing_digits(skill)
                    if ended_with_digits:
                        skill_icon_image = Image.open(f"{units_folder}{text}.webp").convert('RGBA')
                        skill_stat_image = Image.open(f"{units_folder}StatBg.webp").convert('RGBA')
                        sk = create_combined_vertical_image(skill_icon_image, skill_stat_image, AsoiafFonts.get('Garamond-Bold'), f"{digits}+")
                        width, height = [int(x*skillScalePercent) for x in sk.size]
                        sk = sk.resize((width, height))
                        skillability_icon_images.append( [sk,[12,-25]] )
                    elif skill in SkillsAndAbiitiesIconsTable:
                        off = [10,-10]
                        if skill in ['M','R']: # if melee or ranged
                            off = [18,-5]
                        sk = SkillsAndAbiitiesIconsTable[skill].copy()
                        width, height = [int(x*skillScalePercent) for x in sk.size]
                        sk = sk.resize((width, height))
                        skillability_icon_images.append( [sk,off] )
            GBFont = AsoiafFonts.get('Tuff-Bold-33',ImageFont.load_default())
            TN = AsoiafFonts.get('Tuff-Bold-32',ImageFont.load_default())
            TN30 = AsoiafFonts.get('Tuff-Normal-28',ImageFont.load_default())
            TN30I = AsoiafFonts.get('Tuff-Italic-28',ImageFont.load_default())
            starty = yAbilityOffset+0
            ncu_card, yAbilityOffset = draw_markdown_text(ncu_card, GBFont, TN, TN30, TN30I, ability.upper().split('(')[0].strip(), skilldata['Description'].strip(), FactionColor, yAbilityOffset-4, textBoundLeft, textBoundRight, graphics_folder, padding=10)
            yAbilityOffset -= 4
            midy = starty + int((yAbilityOffset-starty) / 2 )
            if len(skillability_icon_images) > 0:
                if len(skillability_icon_images) == 1:
                    icon = skillability_icon_images[0][0]
                    offx, offy = skillability_icon_images[0][1]
                    if index < len(all_abilities)-1:
                        yAbilityOffset += addDivider(SkillBarsOffset - 52, yAbilityOffset)
                    ncu_card.paste(icon, (SkillBarsOffset - icon.size[0] + offx, midy - int(icon.size[0]/2)+ offy), icon)
                elif len(skillability_icon_images) == 2:
                    icon1 = skillability_icon_images[0][0]
                    icon2 = skillability_icon_images[1][0]
                    offx1, offy1 = skillability_icon_images[0][1]
                    offx2, offy2 = skillability_icon_images[1][1]
                    #if NcuData['Name'].upper() == "PYROMANCERS":
                    #    pdb.set_trace()
                    if index < len(all_abilities)-1:
                        yAbilityOffset += addDivider(SkillBarsOffset - 52, yAbilityOffset)
                    ncu_card.paste(icon1, (SkillBarsOffset - icon1.size[0] + offx1, midy - icon1.size[1] + offy1), icon1)
                    ncu_card.paste(icon2, (SkillBarsOffset - icon2.size[0] + offx2, midy + offy2), icon2)
                else:
                    pass # found no occurence where a single ability panel had more than 2 icons
            elif index < len(all_abilities)-1:
                yAbilityOffset += addDivider(SkillBarsOffset - 52, yAbilityOffset)

    ncu_card.paste(SkillBottom, (SkillBarsOffset, yAbilityOffset + dividerYPadding), SkillBottom)
    if not isCommander:
        ncu_card.paste(vert_bar2, (vert2_x, vert2_y), vert_bar2)
        rightdecorX = 685
        ncu_card.paste(DecorStar5, (rightdecorX, 33), DecorStar5)
        ncu_card.paste(DecorStar6, (rightdecorX, 263), DecorStar6)
        ncu_card.paste(DecorStar7, (rightdecorX, 306), DecorStar7)

    draw = ImageDraw.Draw(ncu_card)

    TuffBoldFont = AsoiafFonts.get('Tuff-Bold-47', ImageFont.load_default()) 
    TuffBoldFontSmall = AsoiafFonts.get('Tuff-Bold-30', ImageFont.load_default())
    nameOffsetX = 0 if isCommander else -24
    nameOffsetY = 0 if isCommander else 32
    # THIS IS REALLY BAD BUT IT WORKS AND IM BEING LAZY:
    if ',' in NcuData['Name'].upper():
        lines = NcuData['Name'].upper().split(',')
        text_lines_list, hadAComma = split_name_string(lines[0], amnt=11)
        text_lines_list2, hadAComma = split_name_string(lines[1], amnt=18)
        if len(text_lines_list) == 1:
            draw_centered_text(draw, (540+nameOffsetX, 100+nameOffsetY), [lines[0]], TuffBoldFont, "white", line_padding=10)
            if len(text_lines_list2) == 1:
                draw_centered_text(draw, (540+nameOffsetX, 104+nameOffsetY + TuffBoldFont.size ), [lines[1]], TuffBoldFontSmall, "white", line_padding=10)
            else:
                draw_centered_text(draw, (540+nameOffsetX, 104+nameOffsetY + TuffBoldFont.size ), [text_lines_list2[0]], TuffBoldFontSmall, "white", line_padding=10)
                draw_centered_text(draw, (540+nameOffsetX, 104+nameOffsetY + TuffBoldFont.size + TuffBoldFontSmall.size), [text_lines_list2[1]], TuffBoldFontSmall, "white", line_padding=10)
        else:
            draw_centered_text(draw, (540+nameOffsetX, 80+nameOffsetY), [text_lines_list[0]], TuffBoldFont, "white", line_padding=10)
            draw_centered_text(draw, (540+nameOffsetX, 80+nameOffsetY + TuffBoldFont.size), [text_lines_list[1]], TuffBoldFont, "white", line_padding=10)
            if len(text_lines_list2) == 1:
                draw_centered_text(draw, (540+nameOffsetX, 88+nameOffsetY + (TuffBoldFont.size*1) + TuffBoldFontSmall.size+2 ), [lines[1]], TuffBoldFontSmall, "white", line_padding=10)
            else:
                #draw_centered_text(draw, (540+nameOffsetX, 88+nameOffsetY + (TuffBoldFont.size*2) ), [lines[1]], TuffBoldFontSmall, "white", line_padding=10)
                draw_centered_text(draw, (540+nameOffsetX, 88+nameOffsetY + (TuffBoldFont.size*1) + TuffBoldFontSmall.size+2 ), [text_lines_list2[0]], TuffBoldFontSmall, "white", line_padding=10)
                draw_centered_text(draw, (540+nameOffsetX, 88+nameOffsetY + (TuffBoldFont.size*1) + (TuffBoldFontSmall.size*2)+2 ), [text_lines_list2[1]], TuffBoldFontSmall, "white", line_padding=10)
    else:
        text_lines_list, hadAComma = split_name_string(NcuData['Name'].upper(), amnt=11)
        if len(text_lines_list) == 1:
            draw_centered_text(draw, (540+nameOffsetX, 120+nameOffsetY), [text_lines_list[0]], TuffBoldFont, "white", line_padding=10)
        else:
            draw_centered_text(draw, (540+nameOffsetX, 100+nameOffsetY), [text_lines_list[0]], TuffBoldFont, "white", line_padding=10)
            draw_centered_text(draw, (540+nameOffsetX, 104+nameOffsetY + TuffBoldFont.size ), [text_lines_list[1]], TuffBoldFont, "white", line_padding=10)
    VersionFont = AsoiafFonts.get('Tuff-Italic-25', ImageFont.load_default())
    text_image = Image.new('RGBA', [160, 40], (255, 255, 255, 0))  # transparent background
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((0, 0), NcuData['Version'], font=VersionFont, fill="white")
    # Rotate the text image
    rotated_text_image = text_image.rotate(90, expand=1)
    # Paste the rotated text image onto your main image (consider using the alpha channel for proper transparency)
    ncu_card.paste(rotated_text_image, (rotated_text_image.width - 28, ncu_card.size[1] - rotated_text_image.height - 35), rotated_text_image)
    return ncu_card


def main():
    # Currently, this assumes you are running it from the assets/flutter_assets folder
    assets_folder="./assets/"
    fonts_dir=f"./fonts/"
    AsoiafFonts = load_fonts(fonts_dir)
    data_folder=f"{assets_folder}data/"
    units_folder=f"{assets_folder}Units/"
    attachments_folder=f"{assets_folder}Attachments/"
    graphics_folder = f"{assets_folder}graphics"
    tactics_folder = f"{assets_folder}Tactics/"
    ncus_folder = f"{assets_folder}NCUs/"
    NcuCardsOutputDir  = "./ncucards/"
    if not os.path.exists(NcuCardsOutputDir):
        os.mkdir(NcuCardsOutputDir)
    AsoiafData = import_csvs_to_dicts(data_folder) # contains the keys: attachments,boxes,ncus,newskills,rules,special,tactics,units
    #SelectedNcuCardData = [x for x in AsoiafData['ncus'] if x['Name'] == "Lord Varys, The Spider"][0]
    #SelectedNcuCardData = [x for x in AsoiafData['ncus'] if x['Name'] == "Eddard Stark, Hand of The King"][0]
    #ncu_card = BuildNcuCardFactionWithData(SelectedNcuCardData, units_folder, attachments_folder, graphics_folder, tactics_folder, AsoiafFonts, AsoiafData, ncus_folder)
    for SelectedNcuCardData in AsoiafData['ncus']:
        is_any_value_true = any(bool(value) for value in SelectedNcuCardData.values()) # check for empty dicts
        if not is_any_value_true:
            continue
        ncu_card = BuildNcuCardFactionWithData(SelectedNcuCardData, units_folder, attachments_folder, graphics_folder, tactics_folder, AsoiafFonts, AsoiafData, ncus_folder)
        ncu_card = add_rounded_corners(ncu_card, 20)
        ncu_card_output_path = os.path.join(NcuCardsOutputDir, f"{SelectedNcuCardData['Id'].replace(' ', '_')}.png")
        ncu_card.save(ncu_card_output_path)

    # If You Want to View the Card AND click debug to find positioning uncommont these lines:
    #root = tk.Tk()
    #app = ImageEditor(root, ncu_card)
    #root.mainloop()


if __name__ == "__main__":
    main()
