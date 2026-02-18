import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from pathlib import Path
import requests #pip install requests  #Python 3.11.3 64-bit
import json
from datetime import datetime
from PIL import Image, ImageTk   # Python 3.11.3 64-bit

# Initialize variables
scenes = [] 
current_json_file = None

# URLs for the Stability AI API 
core_url = 'https://api.stability.ai/v2beta/stable-image/generate/core' #  Stable Image Core API URL
image_to_image_url = 'https://api.stability.ai/v2beta/stable-image/generate/ultra' # Stable Image Ultra Image-to-image API URL 
structure_url = 'https://api.stability.ai/v2beta/stable-image/control/structure' # Structure API URL
outpaint_url = 'https://api.stability.ai/v2beta/stable-image/edit/outpaint'  # Outpaint API URL


# Directory to save all generated images
output_dir = 'generated_images'
Path(output_dir).mkdir(parents=True, exist_ok=True)

def load_json_file():
    global scenes, current_json_file
    file_path = filedialog.askopenfilename(title="Select JSON File", filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            global data
            data = json.load(file)

            if 'scenes' not in data:
                messagebox.showerror("Error", "The JSON file does not contain 'scenes'.")
                return

            scenes = data['scenes']
            
        current_json_file = Path(file_path).name
        messagebox.showinfo("Success", f"Loaded JSON file: {current_json_file}")
        update_scene_options()
    except json.JSONDecodeError:
        messagebox.showerror("Error", "Failed to decode JSON. Please check the file format.")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")


def update_scene_options(event=None):
    if not scenes:
        scene_index_combobox.set('')
        image_index_combobox.set('')
        prompt_text.delete("1.0", tk.END)
        return

    scene_indices = [str(i + 1) for i in range(len(scenes))]
    scene_index_combobox['values'] = scene_indices
    scene_index_combobox.set(scene_indices[0])  # Set default value to 1
    update_image_options()

def update_image_options(event=None):
    if not scenes:
        image_index_combobox['values'] = []
        return

    scene_index = int(scene_index_combobox.get()) - 1
    image_indices = [str(i + 1) for i in range(len(scenes[scene_index]['scene']))]
    image_index_combobox['values'] = image_indices
    image_index_combobox.set(image_indices[0])  # Set default value to 1
    update_prompt()

def update_prompt(event=None):
    if not scenes:
        prompt_text.delete("1.0", tk.END)
        return

    scene_index = int(scene_index_combobox.get()) - 1
    image_index = int(image_index_combobox.get()) - 1
    description = scenes[scene_index]['scene'][image_index]['image_description']
    prompt_text.delete("1.0", tk.END)
    prompt_text.insert("1.0", description)


def save_prompt():
    if not scenes:
        messagebox.showerror("Error", "No JSON file loaded.")
        return

    scene_index = int(scene_index_combobox.get()) - 1
    image_index = int(image_index_combobox.get()) - 1
    new_description = prompt_text.get("1.0", "end-1c")

    scenes[scene_index]['scene'][image_index]['image_description'] = new_description
    with open(current_json_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    messagebox.showinfo("Success", "Prompt description saved.")



def generate_image():
    method = method_var.get()
    prompt = prompt_text.get("1.0", "end-1c")  # Fetch the text from the Text widget
    seed = int(seed_entry.get())
    negative_prompt = negative_prompt_entry.get()  # Get the negative prompt value

    # Get the image strength and control strength values from the entries
    image_strength = image_strength_entry.get()
    control_strength = control_strength_entry.get()

    # Get Outpaint parameters
    outpaint_left = int(outpaint_left_entry.get() or 0)
    outpaint_right = int(outpaint_right_entry.get() or 0)
    outpaint_up = int(outpaint_up_entry.get() or 0)
    outpaint_down = int(outpaint_down_entry.get() or 0)

    if method == 'Image Generation':
        generate_image_from_prompt(prompt, seed, negative_prompt)
    elif method == 'Image-to-Image':
        reference_image_path = filedialog.askopenfilename(title="Select Reference Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;")])
        if reference_image_path:
            generate_image_to_image(prompt, reference_image_path, seed, float(image_strength),negative_prompt)
    elif method == 'Image with Structure':
        reference_image_path = filedialog.askopenfilename(title="Select Reference Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;")])
        if reference_image_path:
            generate_image_structure(prompt, reference_image_path, float(control_strength), seed, negative_prompt)
    elif method == 'Outpaint':
        reference_image_path = filedialog.askopenfilename(title="Select Reference Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;")])
        if reference_image_path:
            generate_outpaint(reference_image_path, outpaint_left, outpaint_right, outpaint_up, outpaint_down, prompt, seed)
    else:
        messagebox.showerror("Error", "Please select a generation method.")



def resize_image(image_path, max_size=(1536, 1536)):
    with Image.open(image_path) as img:
        # Check if the image size exceeds the max_size
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)  # Use Image.LANCZOS for high-quality resizing
            resized_path = image_path.replace('.', '_resized.')
            img.save(resized_path)
            return resized_path
        else:
            return image_path

def get_filename(suffix, method='Image Generation'):
    """
    Generate the filename based on the current method and whether a JSON file is loaded or not.
    """

    # Get the current timestamp in the desired format
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')


    if scenes and current_json_file:
        scene_index = int(scene_index_combobox.get()) - 1
        image_index = int(image_index_combobox.get()) - 1
        if method == 'Image Generation':
            return f"{output_dir}/scene_{scene_index + 1}_image_{image_index + 1}_{timestamp}{suffix}"
        elif method == 'Image-to-Image':
            return f"{output_dir}/scene_{scene_index + 1}_image_{image_index + 1}_sample_1_{timestamp}{suffix}"
        elif method == 'Image with Structure':
            return f"{output_dir}/scene_{scene_index + 1}_image_{image_index + 1}_structure_{timestamp}{suffix}"
        elif method == 'Outpaint':
            return f"{output_dir}/scene_{scene_index + 1}_image_{image_index + 1}_outpaint_{timestamp}{suffix}"
        else:
            return f"{output_dir}/scene_{scene_index + 1}_image_{image_index + 1}_{timestamp}{suffix}"
    else:
        if method == 'Image Generation':
            return f"{output_dir}/generated_image_{int(seed_entry.get())}_{timestamp}{suffix}"
        elif method == 'Image-to-Image':
            return f"{output_dir}/generated_image_{int(seed_entry.get())}_sample_1_{timestamp}{suffix}"
        elif method == 'Image with Structure':
            return f"{output_dir}/generated_image_{int(seed_entry.get())}_structure_{timestamp}{suffix}"
        elif method == 'Outpaint':
            return f"{output_dir}/generated_image_{int(seed_entry.get())}_outpaint_{timestamp}{suffix}"
        else:
            return f"{output_dir}/generated_image_{int(seed_entry.get())}_{timestamp}{suffix}"


def generate_image_from_prompt(prompt, seed='', negative_prompt=''):
    api_key = api_key_entry.get()
    if not api_key:
        messagebox.showerror("Error", "API key is required.")
        return

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'image/*',
    }

    files = {
        'prompt': (None, prompt),
        'negative_prompt': (None, negative_prompt),  # Include the negative prompt in the request
        'output_format': (None, 'png'),
        'size': (None, '1024x1024'),
        'seed': (None, str(seed))
    }

    response = requests.post(core_url, headers=headers, files=files)

    if response.status_code != 200:
        messagebox.showerror("Error", f"Error {response.status_code}: {response.text}")
    else:
        filename = get_filename('.png', method='Image Generation')
        with open(filename, 'wb') as file:
            file.write(response.content)
        
        display_image(filename)
        messagebox.showinfo("Success", f"Image saved as {filename}")


def generate_image_to_image(prompt, reference_image_path, seed=0, image_strength=0.5, output_format='png', negative_prompt=''):
    # Validate `image_strength`
    try:
        image_strength = float(image_strength)
    except ValueError:
        messagebox.showerror("Error", "Image Strength must be a numeric value.")
        return

    if not (0 <= image_strength <= 1):
        messagebox.showerror("Error", "Image Strength must be between 0 and 1.")
        return

    # Validate API key
    api_key = api_key_entry.get()
    if not api_key:
        messagebox.showerror("Error", "API key is required.")
        return

    # Determine MIME type
    file_extension = Path(reference_image_path).suffix.lower()
    mime_type = (
        'image/png' if file_extension == '.png' else
        'image/jpeg' if file_extension in ['.jpg', '.jpeg'] else
        'image/webp' if file_extension == '.webp' else None
    )
    if not mime_type:
        messagebox.showerror("Error", f"Unsupported image format: {file_extension}")
        return

    # Resize image if necessary
    resized_image_path = resize_image(reference_image_path, max_size=(1536, 1536))

    # Prepare headers and payload
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'image/*',  # Accept raw image response
    }

    data = {
        'prompt': prompt,
        'strength': str(image_strength),
        'output_format': 'png',
        'aspect_ratio': '1:1',
        'seed': str(seed),
        'negative_prompt':negative_prompt
    }


    # Read and upload image file
    with open(resized_image_path, 'rb') as file:
        files = {
            'image': ('reference' + file_extension, file, mime_type)
        }

        # Make POST request to Stable Image Ultra API
        response = requests.post(image_to_image_url, headers=headers, files=files, data=data)

    # Handle response
    if response.status_code != 200:
        messagebox.showerror("Error", f"Error {response.status_code}: {response.text}")
    else:
        filename = get_filename(f'.{output_format}', method='Image-to-Image')
        with open(filename, 'wb') as file:
            file.write(response.content)
        
        display_image(filename)
        messagebox.showinfo("Success", f"Image saved as {filename}")



def generate_image_structure(prompt, reference_image_path, control_strength=0.5, seed='',negative_prompt=''):
       
    # Έλεγχος αν το control_strength είναι αριθμός και εντός του εύρους [0, 1]
    try:
        control_strength = float(control_strength)  # Προσπάθεια μετατροπής σε float
    except ValueError:
        messagebox.showerror("Error", "Image Strength must be a numeric value.")
        return

    if not (0 <= control_strength <= 1):
        messagebox.showerror("Error", "Image Strength must be between 0 and 1.")
        return


    api_key = api_key_entry.get()
    if not api_key:
        messagebox.showerror("Error", "API key is required.")
        return

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'image/*',
    }

    file_extension = Path(reference_image_path).suffix.lower()
    mime_type = 'image/png' if file_extension == '.png' else (
        'image/jpeg' if file_extension in ['.jpg', '.jpeg'] else (
        'image/webp' if file_extension == '.webp' else None))
    if not mime_type:
        raise ValueError(f"Unsupported image format: {file_extension}")

    # Resize image if it's too large
    resized_image_path = resize_image(reference_image_path, max_size=(1536, 1536))

    with open(resized_image_path, 'rb') as file:
        files = {
            'image': ('reference' + file_extension, file, mime_type)
        }

        data = {
            'prompt': prompt,
            'negative_prompt': (None, negative_prompt),
            'output_format': 'png',
            'size': '1024x1024',
            'control_strength': str(control_strength),
            'seed': str(seed)
        }

        response = requests.post(structure_url, headers=headers, files=files, data=data)

   
    if response.status_code != 200:
        messagebox.showerror("Error", f"Error {response.status_code}: {response.text}")
    else:
        filename = get_filename('.png', method='Image with Structure')
        with open(filename, 'wb') as file:
            file.write(response.content)
        
        display_image(filename)
        messagebox.showinfo("Success", f"Image saved as {filename}")
 

def generate_outpaint(reference_image_path, left, right, up, down, prompt='', seed=''):
    api_key = api_key_entry.get()
    if not api_key:
        messagebox.showerror("Error", "API key is required.")
        return

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'image/*',  # Expect image content
    }

    file_extension = Path(reference_image_path).suffix.lower()
    mime_type = 'image/png' if file_extension == '.png' else (
        'image/jpeg' if file_extension in ['.jpg', '.jpeg'] else (
        'image/webp' if file_extension == '.webp'  else None))
    
    if not mime_type:
        messagebox.showerror("Error", f"Unsupported image format: {file_extension}")
        return

    # Resize image if it's too large
    resized_image_path = resize_image(reference_image_path, max_size=(1536, 1536))

    with open(resized_image_path, 'rb') as file:
        files = {
            'image': ('reference' + file_extension, file, mime_type)
        }

        data = {
            'left': str(left),
            'right': str(right),
            'up': str(up),
            'down': str(down),
            'prompt': prompt,
            'seed': str(seed),
            'output_format': 'png',  # Specify the desired output format
            'creativity': '0.7'  # Optional: adjust creativity
        }

        # Debugging output
        print(f"Sending request to {outpaint_url} with data: {data}")
        print(f"Files to send: {files}")

        response = requests.post(outpaint_url, headers=headers, files=files, data=data)

        # Debugging output
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")

    if response.status_code != 200:
        messagebox.showerror("Error", f"Error {response.status_code}: {response.text}")
    else:
        # Check if the response content is indeed image data
        if 'image' in response.headers.get('Content-Type', ''):
            filename = get_filename('.png', method='Outpaint')
        with open(filename, 'wb') as file:
            file.write(response.content)
        
        display_image(filename)
        messagebox.showinfo("Success", f"Image saved as {filename}")


def display_image(image_path):
    try:
        # Load and display the image
        img = Image.open(image_path)
        img = img.resize((512, 512), Image.LANCZOS)  # Resize the image to fit the label
        img_tk = ImageTk.PhotoImage(img)
        image_label.configure(image=img_tk)
        image_label.image = img_tk  # Keep a reference to avoid garbage collection
    except Exception as e:
        print(f"Error displaying image: {e}")
        messagebox.showerror("Error", f"Failed to display image: {e}")


def update_method_selection(event=None):
    method = method_var.get()
    image_strength_label.grid_forget()
    image_strength_entry.grid_forget()
    control_strength_label.grid_forget()
    control_strength_entry.grid_forget()
    outpaint_left_label.grid_forget()
    outpaint_left_entry.grid_forget()
    outpaint_right_label.grid_forget()
    outpaint_right_entry.grid_forget()
    outpaint_up_label.grid_forget()
    outpaint_up_entry.grid_forget()
    outpaint_down_label.grid_forget()
    outpaint_down_entry.grid_forget()
    negative_prompt_label.grid_forget()
    negative_prompt_entry.grid_forget()

    if method == "Image Generation":
        negative_prompt_label.grid(row=5, column=0, padx=5, pady=5, sticky="e")
        negative_prompt_entry.grid(row=5, column=1, padx=5, pady=5)
    elif method == "Image-to-Image":
        image_strength_label.grid(row=8, column=0, padx=10, pady=5, sticky="e")
        image_strength_entry.grid(row=8, column=1, padx=10, pady=5)
        negative_prompt_label.grid(row=5, column=0, padx=5, pady=5, sticky="e")
        negative_prompt_entry.grid(row=5, column=1, padx=5, pady=5)
    elif method == "Image with Structure":
        negative_prompt_label.grid(row=5, column=0, padx=5, pady=5, sticky="e")
        negative_prompt_entry.grid(row=5, column=1, padx=5, pady=5)
        control_strength_label.grid(row=9, column=0, padx=10, pady=5, sticky="e")
        control_strength_entry.grid(row=9, column=1, padx=10, pady=5)
    elif method == "Outpaint":
        outpaint_left_label.grid(row=8, column=0, padx=10, pady=5, sticky="e")
        outpaint_left_entry.grid(row=8, column=1, padx=10, pady=5)
        outpaint_right_label.grid(row=9, column=0, padx=10, pady=5, sticky="e")
        outpaint_right_entry.grid(row=9, column=1, padx=10, pady=5)
        outpaint_up_label.grid(row=10, column=0, padx=10, pady=5, sticky="e")
        outpaint_up_entry.grid(row=10, column=1, padx=10, pady=5)
        outpaint_down_label.grid(row=11, column=0, padx=10, pady=5, sticky="e")
        outpaint_down_entry.grid(row=11, column=1, padx=10, pady=5)
    


# Create the main window
root = tk.Tk()
root.title("Image Generation App")
root.geometry("800x700")  # Adjusted size for Outpaint parameters

# Left Panel
left_frame = tk.Frame(root, padx=10, pady=10)
left_frame.pack(side="left", fill="y")

# JSON File Selection
load_json_button = tk.Button(left_frame, text="Load JSON File", command=load_json_file, width=25)
load_json_button.grid(row=0, column=0, pady=5)

# API Key Entry
tk.Label(left_frame, text="API Key:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
api_key_entry = tk.Entry(left_frame, show="*", width=30)
api_key_entry.grid(row=1, column=1, padx=5, pady=5)

# Scene Selection
tk.Label(left_frame, text="Scene Index:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
scene_index_combobox = ttk.Combobox(left_frame, state='readonly', width=27)
scene_index_combobox.grid(row=2, column=1, padx=5, pady=5)
scene_index_combobox.bind("<<ComboboxSelected>>", update_image_options)

# Image Selection
tk.Label(left_frame, text="Image Index:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
image_index_combobox = ttk.Combobox(left_frame, state='readonly', width=27)
image_index_combobox.grid(row=3, column=1, padx=5, pady=5)
image_index_combobox.bind("<<ComboboxSelected>>", update_prompt)


# Prompt Text Area
tk.Label(left_frame, text="Prompt:").grid(row=4, column=0, padx=5, pady=5, sticky="ne")
prompt_text = tk.Text(left_frame, width=30, height=5, wrap="word")
prompt_text.grid(row=4, column=1, padx=5, pady=5)
# Prompt Text Area with Scrollbar
prompt_frame = tk.Frame(left_frame)
prompt_frame.grid(row=4, column=1, padx=5, pady=5)

prompt_text = tk.Text(prompt_frame, width=30, height=5, wrap="word")
prompt_text.pack(side="left", fill="both", expand=True)

prompt_scrollbar = tk.Scrollbar(prompt_frame, command=prompt_text.yview)
prompt_scrollbar.pack(side="right", fill="y")

prompt_text.configure(yscrollcommand=prompt_scrollbar.set)


# Negative Prompt Entry
negative_prompt_label = tk.Label(left_frame, text="Negative Prompt:")
negative_prompt_entry = tk.Entry(left_frame, width=30)

# Save Prompt Button
save_prompt_button = tk.Button(left_frame, text="Save Prompt Description", command=save_prompt, width=25)
save_prompt_button.grid(row=6, column=0, columnspan=2, pady=10)

# Image Generation Method
tk.Label(left_frame, text="Generation Method:").grid(row=7, column=0, padx=5, pady=5, sticky="e")
method_var = tk.StringVar(value="Image Generation")
method_combobox = ttk.Combobox(left_frame, textvariable=method_var, state='readonly', width=27)
method_combobox['values'] = ['Image Generation', 'Image-to-Image', 'Image with Structure', 'Outpaint']
method_combobox.grid(row=7, column=1, padx=5, pady=5)
method_combobox.bind("<<ComboboxSelected>>", update_method_selection)


# Labels and Entries for Image Strength, Control Strength, and Outpaint Parameters
image_strength_label = tk.Label(left_frame, text="Image Strength (0 to 1):")
image_strength_entry = tk.Entry(left_frame, width=30)
image_strength_entry.insert(0, '0.5')  # Default value

control_strength_label = tk.Label(left_frame, text="Control Strength (0 to 1):")
control_strength_entry = tk.Entry(left_frame, width=30)
control_strength_entry.insert(0, '0.5')  # Default value

# Outpaint Parameters
outpaint_left_label = tk.Label(left_frame, text="Outpaint Left:")
outpaint_left_entry = tk.Entry(left_frame, width=30)
outpaint_left_entry.insert(0, '0')  # Default value

outpaint_right_label = tk.Label(left_frame, text="Outpaint Right:")
outpaint_right_entry = tk.Entry(left_frame, width=30)
outpaint_right_entry.insert(0, '0')  # Default value

outpaint_up_label = tk.Label(left_frame, text="Outpaint Up:")
outpaint_up_entry = tk.Entry(left_frame, width=30)
outpaint_up_entry.insert(0, '0')  # Default value

outpaint_down_label = tk.Label(left_frame, text="Outpaint Down:")
outpaint_down_entry = tk.Entry(left_frame, width=30)
outpaint_down_entry.insert(0, '0')  # Default value

# Seed Entry
tk.Label(left_frame, text="Seed:").grid(row=12, column=0, padx=5, pady=5, sticky="e")
seed_entry = tk.Entry(left_frame, width=30)
seed_entry.grid(row=12, column=1, padx=5, pady=5)
seed_entry.insert(0,'0')

# Call update_method_selection to reflect the default selection when the program starts
update_method_selection()  

# Generate Image Button
generate_image_button = tk.Button(left_frame, text="Generate Image", command=generate_image, width=25)
generate_image_button.grid(row=14, column=0, columnspan=2, pady=10)


# Center Panel
center_frame = tk.Frame(root, padx=10, pady=10)
center_frame.pack(side="left", fill="both", expand=True)

# Image Display
image_label = tk.Label(center_frame, bg="gray")
image_label.pack(pady=10, fill="both", expand=True)

# Bottom Panel
bottom_frame = tk.Frame(root, padx=10, pady=10)
bottom_frame.pack(side="bottom", fill="x")

# Status Label
status_label = tk.Label(bottom_frame, text="Status: Ready", anchor="w")
status_label.pack(fill="x")



def show_help():
    # Create Help Window
    help_window = tk.Toplevel(root)
    help_window.title("Help - Instructions")
    help_window.geometry("800x800")
    help_window.resizable(False, False)

    # Add a frame for scrollable content
    frame = tk.Frame(help_window, padx=10, pady=10)
    frame.pack(fill="both", expand=True)

    # Scrollbar
    scrollbar = tk.Scrollbar(frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    # Text widget for instructions
    help_text = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, padx=10, pady=10, font=("Arial", 10))
    help_text.pack(fill="both", expand=True)

    # Connect scrollbar to Text widget
    scrollbar.config(command=help_text.yview)

    # Instructions content
    instructions = (
        "Instructions for Parameters:\n\n"
        "1. JSON File:\n"
        "   Load a file containing scenes and prompts and it need to be in the following format:\n\n"
        "   {\n"
        "       \"title\": \"The Night of the UFOs\",\n"
        "       \"audience\": \"First grades\",\n"
        "       \"genre\": \"Entertainment\",\n"
        "       \"scenes\": [\n"
        "           {\n"
        "               \"scene\": [\n"
        "                   {\n"                   
        "                       \"image_description\": \"A view of a city with lightning and rain, Retro comic style artwork.\"\n"
        "                   },\n"
        "                   {\n"
        "                       \"image_description\": \"A group of kids in pajamas and sleeping bags in a living room, Retro comic style artwork.\"\n"
        "                   }\n"
        "               ]\n"
        "           }\n"
        "       ]\n"
        "   }\n\n"
        "2. API Key:\n"
        "   Enter the API key for the Stable Diffusion API.\n\n"
        "3. Scene Index:\n"
        "   Select a scene from the loaded JSON file.\n\n"
        "4. Image Index:\n"
        "   Select an image within the chosen scene.\n\n"
        "5. Prompt:\n"
        "   Enter the description for generating the image.\n\n"
        "6. Negative Prompt:\n"
        "   Specify elements to avoid in the image.\n\n"
        "7. Generation Method:\n"
        "   - *Image Generation:* Generate an image from a text prompt.(Stable Image Core)\n"
        "   - *Image-to-Image:* Modify an existing image.(Stable Image Ultra)\n"
        "   - *Image with Structure:* Use structural guidance for generation.(Structure)\n"
        "   - *Outpaint:* Expand an existing image.(Outpaint)\n\n"
        "8. Image Strength &  Strength:\n"
        " - Image Strength:Sometimes referred to as denoising, this parameter controls how much influence the image parameter has on the generated image. "
        "A value of 0 would give an image that is identical to the input. A value of 1 would be as if you passed to no image. \n\n"
        "- Strength:How much influence or control does the image have on the generation. Represented as a float between 0 and 1, where 0 is the minimum influence and 1 is the maximum."
          "so the bigger the value the less the prompt is important and I reverse it\n\n"
        "9. Outpaint Parameters:\n"
        "   Set expansion dimensions for each side (Left, Right, Up, Down).\n\n"
        "10. Seed:\n"
        "    Set a seed value for reproducibility.\n\n"
        "Click 'Generate Image' to create the output based on the provided parameters."
    )

    # Insert instructions and disable editing
    help_text.insert("1.0", instructions)
    help_text.config(state="disabled")  # Prevent user edits

    # Close Button
    close_button = tk.Button(help_window, text="Close", command=help_window.destroy, bg="#f0f0f0", font=("Arial", 10, "bold"))
    close_button.pack(pady=10)

# Add the Help button next to the JSON button
help_button = tk.Button(left_frame, text="Help", command=show_help, width=10, bg="#d9e8fb", font=("Arial", 10, "bold"))
help_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")



# Run the main loop
root.mainloop()
