#activate virtual environment
activate_this = '/path/to/www/user_study/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

#put the user study app in the path
import sys
sys.path.insert(0,'/path/to/www/user_study')

from app import app as application
