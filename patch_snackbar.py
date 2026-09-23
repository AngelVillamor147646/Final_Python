import os

helper_code = '''
# ---------------------------------------------------------------------------
# Snackbar helper for KivyMD 1.2.0
# ---------------------------------------------------------------------------
from kivymd.uix.snackbar import Snackbar as KivyMDSnackbar
from kivymd.uix.label import MDLabel

class TasklynSnackbar:
    def __init__(self, text=""):
        self.snackbar = KivyMDSnackbar(MDLabel(text=str(text), theme_text_color="Custom", text_color=(1,1,1,1)))
    def open(self):
        self.snackbar.open()
'''

with open(r'c:\Users\GreyCat\Desktop\PY\tasklyn\utils\helpers.py', 'a', encoding='utf-8') as f:
    f.write(helper_code)

for root, _, files in os.walk(r'c:\Users\GreyCat\Desktop\PY\tasklyn'):
    for file in files:
        if file.endswith('.py') and file != 'patch_snackbar.py':
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'from kivymd.uix.snackbar import Snackbar' in content:
                content = content.replace('from kivymd.uix.snackbar import Snackbar', 'from utils.helpers import TasklynSnackbar as Snackbar')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif 'Snackbar(text=' in content:
                print(f"File {file} uses Snackbar but lacks import!")
