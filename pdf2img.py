from pdf2image import convert_from_path

images = convert_from_path('./purchase.pdf', dpi=500)

images[0].save(f'image.jpg', 'JPEG') 