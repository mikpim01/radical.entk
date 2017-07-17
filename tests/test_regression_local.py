from radical.entk import Pipeline, Stage, Task, AppManager, ResourceManager
import pytest
from radical.entk.exceptions import *
import os


def test_regression_local():

    def create_single_task():

        t1 = Task()
        t1.name = 'simulation'
        t1.executable = ['/bin/echo']
        t1.arguments = ['hello']
        t1.copy_input_data = []
        t1.copy_output_data = []

        return t1

    p1 = Pipeline()
    p1.name = 'p1'

    s = Stage()
    s.name = 's1'
    s.tasks = create_single_task()
    s.add_tasks(create_single_task())

    p1.add_stages(s)

    res_dict = {

            'resource': 'local.localhost',
            'walltime': 5,
            'cores': 1,
            'project': ''

    }

    os.environ['RADICAL_PILOT_DBURL'] = 'mongodb://entk:entk@ds129010.mlab.com:29010/test_entk'
    os.environ['RP_ENABLE_OLD_DEFINES'] = 'True'

    rman = ResourceManager(res_dict)

    appman = AppManager()
    appman.resource_manager = rman
    appman.assign_workflow(set([p1]))
    appman.run()

    pass