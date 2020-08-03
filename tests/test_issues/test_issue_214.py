from radical.entk import Pipeline, Stage, Task, AppManager
import os


# ------------------------------------------------------------------------------
# Set default verbosity

if not os.environ.get('RADICAL_ENTK_VERBOSE'):
    os.environ['RADICAL_ENTK_VERBOSE'] = 'INFO'

hostname = os.environ.get('RMQ_HOSTNAME','localhost')
port = int(os.environ.get('RMQ_PORT',5672))
username = os.environ.get('RMQ_USERNAME', 'guest')
password = os.environ.get('RMQ_PASSWORD', 'guest')
sleep = os.environ.get('TEST_214_SLEEP_DURATION',300)


def generate_pipeline():

    # Create a Pipeline object
    p = Pipeline()

    # Create a Stage object
    s1 = Stage()

    # Create a Task object which creates a file named 'output.txt' of size 1 MB
    t1 = Task()
    t1.executable = '/bin/sleep'
    t1.arguments = [sleep]

    # Add the Task to the Stage
    s1.add_tasks(t1)

    # Add Stage to the Pipeline
    p.add_stages(s1)

    return p


def test_issue_214():

    # Create a dictionary describe four mandatory keys:
    # resource, walltime, cpus and project
    # resource is 'local.localhost' to execute locally
    res_dict = {

            'resource': 'local.localhost',
            'walltime': (int(sleep) // 60) + 5,
            'cpus': 1
    }


    # Create Application Manager
    appman = AppManager(hostname=hostname, port=port, username=username,
            password=password)

    # Assign resource manager to the Application Manager
    appman.resource_desc = res_dict

    p = generate_pipeline()

    # Assign the workflow as a set of Pipelines to the Application Manager
    appman.workflow = [p]

    # Run the Application Manager
    appman.run()
