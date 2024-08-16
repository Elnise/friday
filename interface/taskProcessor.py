import subprocess
import os.path
from logging import exception


def execute_task(task):
    task_data = task.split('|')
    action = task_data[0]
    item = task_data[1]
    try:
        params = task_data[2]
    except:
        params = []
    script_location = './taskScripts/'+item+'/'+action+'.sh'
    if not os.path.isfile(script_location):
        raise Exception('Missing action')
    call_data = ['sh', script_location] + params
    subprocess.call(call_data)