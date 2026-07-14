from PIL import Image
import numpy as np
import sys
import os

def process_image():
    if not os.path.exists('samurai.png'):
        print("Please save the image as samurai.png in this folder first!")
        return

    # Load image and convert to RGBA
    img = Image.open('samurai.png').convert('RGBA')
    data = np.array(img)

    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    # Calculate brightness (255 is white background, 0 is black ink)
    brightness = 0.299*r + 0.587*g + 0.114*b

    # Alpha is inverse of brightness (white background becomes fully transparent)
    alpha = 255 - brightness

    # Make the ink a subtle dark grey/green (#1e2320) so it looks good on the black background
    # OR make it Red (#e0473e) with low opacity. Let's do a subtle red/grey watermark.
    # We will color the ink Red (224, 71, 62) but lower the overall opacity.
    
    data[:,:,0] = 224
    data[:,:,1] = 71
    data[:,:,2] = 62
    
    # Reduce opacity of the ink so it's a watermark (max alpha ~ 60)
    data[:,:,3] = (alpha * 0.2).astype(np.uint8)

    new_img = Image.fromarray(data)
    new_img.save('hero_bg.png')
    print("Successfully processed image -> hero_bg.png")

if __name__ == '__main__':
    process_image()
