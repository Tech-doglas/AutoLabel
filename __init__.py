import subprocess
import sys
import os

def install_requirements():
    if not os.path.exists('requirements.txt'):
        raise FileNotFoundError('requirements.txt not found')
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", 'requirements.txt'])

install_requirements()

# Continue with other initialization code if necessary
