
import os
import json
import pika

from unittest import TestCase
from random import shuffle

from hypothesis import given, settings, strategies as st
import threading as mt

from radical.entk.appman.wfprocessor import WFprocessor
from radical.entk                    import AppManager as Amgr
from radical.entk                    import Pipeline, Stage, Task, states

import radical.utils as ru
try:
    import mock
except ImportError:
    from unittest import mock

# Hypothesis settings
settings.register_profile("travis", max_examples=100, deadline=None)
settings.load_profile("travis")


# ------------------------------------------------------------------------------
#
class TestBase(TestCase):

    @mock.patch('radical.utils.generate_id', return_value='wfp.0000')
    @mock.patch('os.getcwd', return_value='test_folder')
    @mock.patch('radical.utils.Logger')
    @mock.patch('radical.utils.Profiler')
    @mock.patch('radical.utils.Reporter')
    def test_wfp_initialization(self, mocked_generate_id, mocked_getcwd,
                                mocked_Logger, mocked_Profiler, mocked_Reporter):

        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=False)

        self.assertIsNone(wfp._wfp_process)
        self.assertIsNone(wfp._enqueue_thread)
        self.assertIsNone(wfp._dequeue_thread)
        self.assertEqual(wfp._rmq_ping_interval, 10)
        self.assertEqual(wfp._path, 'test_folder/test_sid')
        self.assertEqual(wfp._workflow, 'workflow')
        

        self.assertEqual(wfp._sid, 'test_sid')
        self.assertEqual(wfp._pending_queue, 'pending_queue')
        self.assertEqual(wfp._completed_queue, 'completed_queue')
        self.assertFalse(wfp._resubmit_failed)
        self.assertEqual(wfp._rmq_conn_params, 'test_rmq_params')
        self.assertEqual(wfp._uid, 'wfp.0000')
        
        os.environ['RMQ_PING_INTERVAL'] = '20'
        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=True)
        
        self.assertIsNone(wfp._wfp_process)
        self.assertIsNone(wfp._enqueue_thread)
        self.assertIsNone(wfp._dequeue_thread)
        self.assertEqual(wfp._rmq_ping_interval, 20)
        self.assertEqual(wfp._path, 'test_folder/test_sid')
        self.assertEqual(wfp._workflow, 'workflow')
        self.assertEqual(wfp._sid, 'test_sid')
        self.assertEqual(wfp._pending_queue, 'pending_queue')
        self.assertEqual(wfp._completed_queue, 'completed_queue')
        self.assertTrue(wfp._resubmit_failed)
        self.assertEqual(wfp._rmq_conn_params, 'test_rmq_params')
        self.assertEqual(wfp._uid, 'wfp.0000')
    
    
    # ------------------------------------------------------------------------------
    #
    @mock.patch.object(WFprocessor, '__init__', return_value=None)
    @mock.patch('radical.utils.Logger')
    def test_wfp_workflow_incomplete(self, mocked_init, mocked_Logger):

        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=False)

        pipe = mock.Mock()
        pipe.lock = mt.Lock()
        pipe.completed = False
        wfp._workflow = set([pipe])
        self.assertTrue(wfp.workflow_incomplete())

        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=False)

        pipe = mock.Mock()
        pipe.lock = mt.Lock()
        pipe.completed = True
        wfp._workflow = set([pipe])
        self.assertFalse(wfp.workflow_incomplete())

        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=False)
        with self.assertRaises(Exception):
            wfp.workflow_incomplete()
    
    # ------------------------------------------------------------------------------
    #
    @mock.patch.object(WFprocessor, '__init__', return_value=None)
    def test_check_processor(self, mocked_init):

        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=False)

        wfp._enqueue_thread = None
        wfp._dequeue_thread = None

        self.assertFalse(wfp.check_processor())

        wfp._enqueue_thread = mock.Mock()
        wfp._enqueue_thread.is_alive = mock.MagicMock(side_effect=[False, False,
                                                                   True, True])
        wfp._dequeue_thread = mock.Mock()
        wfp._dequeue_thread.is_alive = mock.MagicMock(side_effect=[False, True,
                                                                   False, True])
        
        self.assertFalse(wfp.check_processor())
        self.assertFalse(wfp.check_processor())
        self.assertFalse(wfp.check_processor())
        self.assertTrue(wfp.check_processor())


    # ------------------------------------------------------------------------------
    #
    @mock.patch.object(WFprocessor, '__init__', return_value=None)
    @mock.patch('radical.utils.Logger')
    @mock.patch('radical.utils.Profiler')
    @mock.patch('time.sleep', return_value=None)
    @mock.patch.object(WFprocessor, '_create_workload',
                       side_effect=[['task','stages'],[]])
    @mock.patch.object(WFprocessor, '_execute_workload', retur_value=True)
    def test_enqueue(self, mocked_init, mocked_Logger, mocked_Profiler,
                     mocked_sleep, mocked_create_workload, mocked_execute_workload):
        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=False)
        wfp._logger = mocked_Logger
        wfp._prof = mocked_Profiler
        wfp._uid = 'wfp.0000'
        wfp._enqueue_thread_terminate = mock.Mock()
        wfp._enqueue_thread_terminate.is_set = mock.MagicMock(side_effect=[False, True])

        wfp._enqueue()

        with self.assertRaises(Exception):
            wfp._enqueue()

    # ------------------------------------------------------------------------------
    #
    @mock.patch.object(WFprocessor, '__init__', return_value=None)
    @mock.patch('radical.utils.Logger')
    @mock.patch('radical.utils.Reporter')
    def test_advance(self, mocked_init, mocked_Logger, mocked_Reporter):
        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=False)

        global_profs = []
        def _log(log_entry, uid, state, msg):
            nonlocal global_profs
            global_profs.append([log_entry, uid, state, msg])

        wfp._logger = mocked_Logger
        wfp._report = mocked_Reporter
        wfp._prof = mock.Mock()
        wfp._prof.prof = mock.MagicMock(side_effect=_log)
        wfp._uid = 'wfp.0000'
        obj = mock.Mock()
        obj.parent_stage = {'uid': 'test_stage'}
        obj.parent_pipeline = {'uid': 'test_pipe'}
        obj.uid = 'test_object'
        obj.state = 'test_state'
        wfp._advance(obj, 'Task', None)
        self.assertEqual(global_profs[0],['advance', 'test_object', None, 'test_stage'])
        global_profs = []
        wfp._advance(obj, 'Stage', 'new_state')
        self.assertEqual(global_profs[0],['advance','test_object', 'new_state', 'test_pipe'])
        global_profs = []
        wfp._advance(obj, 'Pipe', 'new_state')
        self.assertEqual(global_profs[0],['advance','test_object', 'new_state', None])


    # ------------------------------------------------------------------------------
    #
    @mock.patch.object(WFprocessor, '__init__', return_value=None)
    @mock.patch.object(WFprocessor, '_advance', return_value=None)
    @mock.patch('radical.utils.Logger')
    @mock.patch('radical.utils.Reporter')
    def test_create_workload(self, mocked_init, mocked_advance, mocked_Logger,
                             mocked_Reporter):
        wfp = WFprocessor(sid='test_sid', workflow='workflow',
                          pending_queue='pending_queue',
                          completed_queue='completed_queue',
                          rmq_conn_params='test_rmq_params',
                          resubmit_failed=False)
        
        wfp._resubmit_failed = False
        pipe = mock.Mock()
        pipe.lock = mt.Lock()
        pipe.state = states.INITIAL
        pipe.completed = False
        pipe.current_stage = 1
        
        stage = mock.Mock()
        stage.uid = 'stage.0000'
        stage.state = states.SCHEDULING

        task = mock.Mock()
        task.uid = 'task.0000'
        task.state = states.INITIAL

        stage.tasks = [task]
        pipe.stages = [stage]
        wfp._workflow = set([pipe])

        workload, scheduled_stages = wfp._create_workload()

        self.assertEqual(workload, [task])
        self.assertEqual(scheduled_stages, [stage])