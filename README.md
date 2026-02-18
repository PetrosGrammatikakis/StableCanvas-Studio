# StableCanvas Studio

**StableCanvas Studio** is a desktop GUI application built with **Python (Tkinter)** that leverages the **Stability AI API** for advanced image generation. It supports multiple generation modes, including text-to-image, image-to-image, structural guidance, and outpainting. The app also features **JSON-based scene management** for organized prompt workflows, making it ideal for structured creative projects and portfolio demonstrations.

---

## Features

- **Multi-mode Image Generation**
  - **Text-to-Image**: Generate images directly from textual prompts.
  - **Image-to-Image**: Modify an existing image using prompts and influence strength.
  - **Image with Structure**: Use structural guidance to control the image output.
  - **Outpainting**: Expand images beyond their original borders.

- **JSON Scene Management**
  - Load scenes from JSON files.
  - Each scene can contain multiple images with editable prompts.
  - Easily update prompts and save back to JSON.

- **Customizable Parameters**
  - Negative prompts to exclude elements.
  - Image strength, control strength, and outpaint dimensions.
  - Seed value for reproducible results.

- **Integrated Image Display**
  - Preview generated images directly in the app.
  - Resize and manage outputs automatically in `generated_images/` folder.

---
## Save Files
- **All generated images are saved inside:generated_images/

- **File names are automatically generated based on:
 - Scene index
 - Image index
 - Method
 - Timestamp
 - Seed

