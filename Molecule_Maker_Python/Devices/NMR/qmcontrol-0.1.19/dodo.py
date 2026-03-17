from pathlib import Path
import subprocess
from doit.action import CmdAction
import os

DOIT_CONFIG = {'default_tasks': ['qmcontrol']}
QMC_VERSION = "development"
def task_compile_ui():
    """Compiles the .ui files"""

    p = Path(__file__).parent /"qmcontrol" / "ui"
    deps = list(p.glob("*.ui"))
    
    for ui_file in deps:
        py_file = ui_file.with_suffix('.py')
        yield {
            'name': py_file.name,
            'actions': [['pipenv','run','pyside6-uic', '-o', py_file, ui_file]],
            'file_dep': [ui_file],
            'targets': [py_file],
        }

def task_licenses():
    """Generate 'licenses.txt'"""
    target = Path('qmcontrol') / 'licenses.txt'
    return {
        'actions': [['pipenv','run', 'pip-licenses', '--format=plain-vertical', '--with-license-file', '--no-license-path', '--ignore-packages', 'pyinstaller', 'pyinstaller-hooks-contrib', '--output-file', target]],
        'file_dep': ['Pipfile.lock'],
        'targets': [target]
    }

def task_get_version():
    """Update version.py with the git tag version"""
    def fetch_version(targets):
        global QMC_VERSION
        try:
            p = subprocess.Popen(['git','describe','--dirty'],stdout=subprocess.PIPE)
            (stdout,err) = p.communicate()
            QMC_VERSION = stdout.decode().strip()
        except Exception:
            print("Problem grabbing version from git. Defaulting to 'development'")
            QMC_VERSION = "development"

        with open(targets[0],'w') as fout:
            fout.write("Version='%s'\n"%QMC_VERSION)
        
    return {
        'actions': [fetch_version],
        'targets': [Path('qmcontrol')/'version.py']
    }

def task_clean_version():
    """Remove version.py"""
    def remove_version_file():
        p = Path('qmcontrol')/'version.py'
        if p.exists():
            os.unlink(p)
            
    
   
    return {
        'actions': [remove_version_file],        
    }

    
    
def task_qmcontrol():
    """Starts QMControl application"""
    return {
        'actions': [['pipenv','run', 'python', 'run.py']],
        'task_dep': ['compile_ui', 'licenses', 'get_version']
    }

def task_pyinstaller():
    """Generate QMControl.exe"""
    return {
        'actions': [['pipenv','run', 'pyinstaller', 'qmcontrol.spec', '-y']],
        'task_dep': ['clean_version','compile_ui', 'licenses', 'get_version'],
    }

def task_build_installer():
    """Builds the installer"""
    def gen_cmd():
    
        global QMC_VERSION
        iscc_path = (Path('/') / 'Program Files (x86)' / 'Inno Setup 6' / 'ISCC.exe')
        rv =  [iscc_path, '/DVersion=%s'%QMC_VERSION, Path(__file__).parent / 'InnoScript.iss'] 
        return rv
        
    return {
        'actions': [CmdAction(gen_cmd)],
        'task_dep': ['pyinstaller'],
    }
    

