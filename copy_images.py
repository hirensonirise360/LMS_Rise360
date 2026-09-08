import shutil
try:
    shutil.copy(r"C:\Users\Hiren Soni\.gemini\antigravity\brain\f197d034-ae34-4a69-b6b2-39afc6f45fdd\hks_logo_fixed_1777822324177.png", r"c:\Users\Hiren Soni\Desktop\New Coding\LMS_EA\static\img\rise360-logo.png")
    shutil.copy(r"C:\Users\Hiren Soni\.gemini\antigravity\brain\f197d034-ae34-4a69-b6b2-39afc6f45fdd\hks_og_image_fixed_1777822346828.png", r"c:\Users\Hiren Soni\Desktop\New Coding\LMS_EA\static\img\og-image.png")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
