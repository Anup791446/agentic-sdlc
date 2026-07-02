import os
import sys
os.environ['MOCK_MODE'] = 'true'
sys.argv = ['main.py', 'Build a simple todo app with user login, task creation, update, delete, and persistence.', '--mock', '--yes']
import main
main.main()
