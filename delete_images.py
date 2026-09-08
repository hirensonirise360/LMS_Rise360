import os
try:
    os.remove(r"c:\Users\Hiren Soni\Desktop\New Coding\LMS_EA\static\img\rise360-logo.png")
    os.remove(r"c:\Users\Hiren Soni\Desktop\New Coding\LMS_EA\static\img\og-image.png")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
