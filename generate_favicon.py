from PIL import Image
import os

def create_favicons():
    logo_path = r"c:\Users\Hiren Soni\Desktop\New Coding\LMS_EA\static\img\rise360-logo.png"
    public_dir = r"c:\Users\Hiren Soni\Desktop\New Coding\LMS_EA\public"
    
    if not os.path.exists(public_dir):
        os.makedirs(public_dir)
        
    img = Image.open(logo_path)
    width, height = img.size
    
    favicon_img = img
    
    # Save PNG
    favicon_png_path = os.path.join(public_dir, "favicon.png")
    favicon_img.resize((192, 192), Image.Resampling.LANCZOS).save(favicon_png_path, "PNG")
    print(f"Created {favicon_png_path}")
    
    # Save ICO (multiple sizes)
    favicon_ico_path = os.path.join(public_dir, "favicon.ico")
    favicon_img.save(favicon_ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"Created {favicon_ico_path}")

if __name__ == "__main__":
    try:
        create_favicons()
        print("Success")
    except Exception as e:
        print(f"Error: {e}")
