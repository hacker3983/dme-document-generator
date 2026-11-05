from PIL import Image

# Load your existing JPEG logo
img = Image.open("static/images/dme_logo.jpg").convert("RGBA")
datas = img.getdata()

new_data = []
for item in datas:
    # If the pixel is dark/black (background), make it transparent
    if item[0] < 40 and item[1] < 40 and item[2] < 40:
        new_data.append((255, 255, 255, 0))
    else:
        # Convert white/light text and graphics to solid black
        new_data.append((0, 0, 0, item[3]))

img.putdata(new_data)

# Crop out the excess transparent padding around the logo text
bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)

img.save("static/images/dme_logo.png", "PNG")
print("Successfully generated cropped static/images/dme_logo.png!")
