from radical.entk import Pipeline, Stage, Task, AppManager, ResourceManager
import os

# ------------------------------------------------------------------------------
# Set default verbosity

if os.environ.get('RADICAL_ENTK_VERBOSE') == None:
    os.environ['RADICAL_ENTK_VERBOSE'] = 'INFO'

def generate_pipeline():

    # Create a Pipeline object
    p = Pipeline()
 
    # Create a Stage object 
    s1 = Stage()

    # Create a Task object which creates a file named 'output.txt' of size 1 MB
    t1 = Task()    
    t1.executable = ['/bin/bash']   
    t1.arguments = ['-l', '-c', 'base64 /dev/urandom | head -c 1000000 > output.txt'] 

    # Add the Task to the Stage
    s1.add_tasks(t1)

    # Add Stage to the Pipeline
    p.add_stages(s1)


    # Create another Stage object to hold character count tasks
    s2 = Stage()

    # Create a Task object
    t2 = Task()
    t2.executable = ['/bin/bash']    
    t2.arguments = ['-l', '-c', 'grep -o . output.txt | sort | uniq -c > ccount.txt']  
    # Copy data from the task in the first stage to the current task's location
    t2.copy_input_data = ['$Pipline_%s_Stage_%s_Task_%s/output.txt'%(p.uid, s1.uid, t1.uid)]

    # Add the Task to the Stage
    s2.add_tasks(t2)

    # Add Stage to the Pipeline
    p.add_stages(s2)


    # Create another Stage object to hold checksum tasks
    s3 = Stage()

    # Create a Task object
    t3 = Task()
    t3.executable = ['/bin/bash']    
    t3.arguments = ['-l','-c','sha1sum ccount.txt > chksum.txt']  
    # Copy data from the task in the first stage to the current task's location
    t3.copy_input_data = ['$Pipline_%s_Stage_%s_Task_%s/ccount.txt'%(p.uid, s2.uid, t2.uid)]
    # Download the output of the current task to the current location
    t3.download_output_data = ['chksum.txt > chksum_%s.txt'%cnt]

    # Add the Task to the Stage
    s3.add_tasks(t3)

    # Add Stage to the Pipeline
    p.add_stages(s3)


    return p


if __name__ == '__main__':

    pipelines = []
    
    for cnt in range(10):
        pipelines.append(generate_pipeline())


    # Create a dictionary describe four mandatory keys:
    # resource, walltime, cores and project
    # resource is 'local.localhost' to execute locally
    res_dict = {

            'resource': 'local.localhost',
            'walltime': 10,
            'cores': 2,
            'project': '',
    }

    # Create Resource Manager object with the above resource description
    rman = ResourceManager(res_dict)

    # Create Application Manager
    appman = AppManager()

    # Assign resource manager to the Application Manager
    appman.resource_manager = rman

    # Assign the workflow as a set of Pipelines to the Application Manager
    appman.assign_workflow(set(pipelines))

    # Run the Application Manager
    appman.run()
