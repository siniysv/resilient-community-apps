# -*- coding: utf-8 -*-

"""Action Module task logger, implemented via circuits"""

from __future__ import print_function
import logging
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent

LOG = logging.getLogger(__name__)

CONFIG_DATA_SECTION = "task_tracker"


class TaskTrackerComponent(ResilientComponent):
    """Example Circuits script to implement a data-table based task tracker"""

    def __init__(self, opts):
        super(TaskTrackerComponent, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})
        LOG.debug(self.options)

        # The queue name can be specified in the config file,
        # or default to 'tasktrackerqueue'
        self.channel = "actions." + self.options.get("queue", "tasktrackerqueue")

    @handler("task_tracker")
    def _task_tracker_function(self, event, *args, **kwargs):
        """
        Function to add a row in the data table containing task information
        whenever task status changes from open to close or vice-versa
        """

        # Get information from action
        LOG.info('Getting information from action...')
        information = kwargs['message']
        task_name = information['task']['name']
        task_init_date = information['task']['init_date']
        task_closed_date = information['task']['closed_date']
        task_id = information['task']['id']
        if task_closed_date is None:
            task_closed_date = task_init_date
        task_status = information['task']['status']
        task_inc_id = information['task']['inc_id']
        # Create task note
        LOG.info('Creating task note...')
        task_note = "Task Opened"
        if task_status == "C":
            task_note = "Task Closed"
        # Create time duration
        LOG.info('Calculating duration...')
        task_closetime = "task not closed"
        if task_closed_date is not None:
            secs = (int(task_closed_date)-int(task_init_date))/1000
            minutes = int(secs/60)
            secs = secs % 60
            hours = int(minutes/60)
            minutes = minutes % 60
            days = int(hours/24)
            hours = hours % 24
            task_closetime = "{}d {}h {}m {}s".format(days, hours, minutes, secs)
        # Note: Data fields will be organized as follows:

        # task_name | task_note |  init_date | closed_date | task_closetime | task_id
        #    (text) |   (text)  | (datetime) |  (datetime) |     (text)     |  (text)
        # ===========================================================================
        # Do stuff  |   Opened  |    5/26    |     5/27    |  1d 2h 14m 23s |  22414

        # task_name: Name of task, text field
        # task_note: Whether the task was opened or closed, text field
        # init_date: Task init date, datetimepicker field
        # closed_date: Task closed date, datetimepicker field
        # task_closetime: Time taken to close task in days/hours/min/sec, text field
        # task_id: The task ID, text field

        # Posting to a data table is done via dictionary with the fields
        # mentioned above

        # Get the table ID
        LOG.info('Organizing data...')
        table_uri = '/types/'+self.options['table_api_name']
        mytable = self.rest_client().get(table_uri)
        mytable_id = mytable['id']
        # Get table column ID's
        column_ids = {}
        for column in mytable['fields']:
            column_ids[column] = mytable['fields'][column]['id']
        # Create values dictionary
        values = {self.options['column_one']: task_name,
                  self.options['column_two']: task_note,
                  self.options['column_three']: task_init_date,
                  self.options['column_four']: task_closed_date,
                  self.options['column_five']: str(task_closetime),
                  self.options['column_six']: str(task_id)}
        table_uri = "/incidents/{}/table_data/{}/row_data".format(task_inc_id, mytable_id)
        # Create row to add
        LOG.info('Creating row...')
        row = {}
        row['cells'] = {}
        for key in column_ids:
            row['cells'][int(column_ids[key])] = {'value': values[key]}

        # Post Row
        LOG.info('Posting row...')
        self.rest_client().post(table_uri, row)
        LOG.info('Row posted! :D')

        status = "Finished posting task time to close! :D"
        yield status