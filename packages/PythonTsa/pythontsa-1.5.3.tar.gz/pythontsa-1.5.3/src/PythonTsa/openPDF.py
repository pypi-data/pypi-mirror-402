# Open PDFs on your computer by default viewer
import os
import platform
def open_pdf(file_path):
      if platform.system() == 'Windows':
          os.startfile(file_path)  # Windows 
      elif platform.system() == 'Darwin':
          os.system(f'open {file_path}')  # macOS 
      else:
          os.system(f'xdg-open {file_path}')  # Linux 
