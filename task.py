import io, re, json
import pytesseract 
import pandas as pd
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from itertools import zip_longest

x_start = 0 # for get_table_details

def get_table_details(image, col_pos):
   global x_start 
   
   if image.width < 800 and image.height < 600:
      image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
      image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize
      image = image.filter(ImageFilter.SHARPEN)
      col_pos = int(col_pos * 2)
   
   x_end = int(col_pos)
   image = ImageOps.autocontrast(image) 

   cropped_image = image.crop((x_start, 0, x_end, image.height))
   x_start = x_end
      
   if cropped_image.width < 800 and cropped_image.height < 600: 
      cropped_image = cropped_image.resize((cropped_image.width * 2, cropped_image.height * 2), Image.Resampling.LANCZOS)
      cropped_image = cropped_image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize
      cropped_image = cropped_image.filter(ImageFilter.SHARPEN)
      
   cropped_image.save(f'./table_columns_split/image{cropped_image.width}.jpg', 'JPEG', dpi=(300, 300)) 
   
   custom_config = r'--oem 3 --psm 6'
   parsed =  pytesseract.image_to_string(cropped_image, config=custom_config)
   cleaned_content = "\n".join([line.strip() for line in parsed.splitlines() if line.strip()])
   
   return cleaned_content.split('\n')

def get_company_details(image):

   if image.width < 800 or image.height < 600:
      image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS) 
      image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize
      image = image.filter(ImageFilter.SHARPEN)
      
   image = ImageOps.autocontrast(image) 
   
   custom_config = r'--oem 3 --psm 6'
   parsed =  pytesseract.image_to_string(image, config=custom_config)
   cleaned_content = "\n".join([line.strip() for line in parsed.splitlines() if line.strip()]) 
   
   return cleaned_content.split('\n') # convert into list

def get_PO(image):
   
   if image.width < 800 or image.height < 600:
      image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS) 
      image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize
      image = image.filter(ImageFilter.SHARPEN)
   
   image = ImageOps.autocontrast(image) 

   parsed =  pytesseract.image_to_string(image)
   pattern = r'PO#[^\[]*\[([^\]]+)' # ignore everythings that comes between 'PO#' and '[' and keep reading upto ']'
   
   match = re.search(pattern, parsed)
   if not match: 
      return
   return match.group(1)

if __name__ == "__main__":
   
   ''' 
      Image preprocessing
      The best color of text for recognition by Tesseract OCR (and most OCR engines) is black text on a white background.
         - Resizing: Resizes the image if its dimensions are smaller than 800x600.
         - Grayscale Conversion: Converts the image to grayscale for better recognition.
         - Sharpening: Uses ImageFilter.SHARPEN to enhance the edges of text.
         - Contrast Enhancement: Enhances contrast to make the text stand out.
         - Binarization: Converts the image to black and white (apply while resizing)
         - Tesseract Configurations:
            - custom_config = r'--oem 3 --psm 6'
               --oem 3: Uses the default OCR engine.
               --psm 6: Treats the image as a block of text.
   '''
   
   image = Image.open('image.jpg')

   image = image.convert("L")  # Convert to grayscale
   image = ImageOps.invert(image)  # Invert colors if text is white on black
   image = image.filter(ImageFilter.SHARPEN) # Apply sharpening filter (optional for blurry images)   
   
   # ! 2.1
   company_cropped_img = image.crop((image.width-4020, image.height-5070, image.width-3100, image.height-4350)) # (L T R B)
   company_details = get_company_details(image=company_cropped_img)
   
   # ! 2.2
   table_img = image.crop((image.width-4020, image.height-3034, image.width-340, image.height-2680)) # (L T R B)
   cols_pos = [table_img.width-3015, table_img.width-1640, table_img.width-1136, table_img.width-607, table_img.width]

   columns = []

   for col_pos in cols_pos:
      col_data = get_table_details(image=table_img, col_pos=col_pos)
      columns.append(col_data)

   merged_data = [row for row in zip_longest(*columns, fillvalue='')] 
   filtered_data = [row for row in merged_data if any(cell.strip() for cell in row)]
   
   # df = pd.DataFrame(filtered_data)
   # json_result = df.to_json(orient='records')  # 'records' gives a list of dictionaries

   # ! 2.3
   PO_no = get_PO(image=image)
   
   
   data = {
      "fixed_text_positiob": company_details,
      "data_table": filtered_data, # pending
      "PO_token": str(PO_no),
      "Test Spaces": pytesseract.image_to_string(Image.open('./test_spaces.png'), config= r'--oem 3 --psm 6 -c preserve_interword_spaces=1')
   }
   
   with open("data.json", "w") as json_file:
      json.dump(data, json_file, indent=4)
