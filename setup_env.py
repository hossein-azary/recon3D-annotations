import subprocess
import sys
import os

def create_venv(env_name='env'):
    """Create a virtual environment."""
    subprocess.check_call([sys.executable, '-m', 'venv', env_name])

def activate_venv(env_name='env'):
    """Return the path to the activate script."""
    if os.name == 'nt':  # Windows
        return os.path.join(env_name, 'Scripts', 'activate.bat')
    else:
        return os.path.join(env_name, 'bin', 'activate')

def install_packages(env_name='env', packages=['cobra', 'requests', 'cobramod']):
    """Install packages in the virtual environment."""
    pip_path = os.path.join(env_name, 'Scripts', 'pip') if os.name == 'nt' else os.path.join(env_name, 'bin', 'pip')
    subprocess.check_call([pip_path, 'install'] + packages)

if __name__ == '__main__':
    env_name = 'env'
    print("Creating virtual environment...")
    create_venv(env_name)
    print("Installing packages...")
    install_packages(env_name)
    print(f"Virtual environment '{env_name}' created and packages installed.")
    print(f"To activate: {activate_venv(env_name)}")