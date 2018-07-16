# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation API."""

from datetime import datetime

from transitions import Machine

from invenio_records.api import Record

from flask import current_app

STATES = ['CREATED', 'PENDING', 'ITEM_ON_LOAN', 'ITEM_RETURNED',
          'ITEM_IN_TRANSIT', 'ITEM_AT_DESK']

TRANSITIONS = [
    {'trigger': 'request', 'source': 'CREATED',
        'dest': 'PENDING', 'before': 'set_request_parameters'
    },
    {'trigger': 'validate_request', 'source': 'PENDING',
        'dest': 'ITEM_IN_TRANSIT', 'before': 'set_parameters',
        'unless': 'is_pickup_at_same_library'
    },
    {'trigger': 'validate_request', 'source': 'PENDING',
        'dest': 'ITEM_AT_DESK', 'before': 'set_parameters',
        'conditions': 'is_pickup_at_same_library'
    },
    {'trigger': 'checkout', 'source': 'CREATED',
        'dest': 'ITEM_ON_LOAN', 'before': 'set_parameters'
    },
    {'trigger': 'checkin', 'source': 'ITEM_ON_LOAN',
        'dest': 'ITEM_RETURNED', 'before': 'set_parameters'
    }
]


class Loan(Record):

    def __init__(self, data, model=None):
        """."""
        data.setdefault('state', STATES[0])
        super(Loan, self).__init__(data, model)
        Machine(model=self, states=STATES, send_event=True,
                transitions=TRANSITIONS,
                initial=self['state'],
                finalize_event='save')

    def set_request_parameters(self, event):
        self.set_parameters(event)
        self['pickup_location_pid'] = event.kwargs.get('pickup_location_pid')

    def set_parameters(self, event):
        params = event.kwargs
        self['transaction_user_pid'] = params.get('transaction_user_pid')
        self['patron_pid'] = params.get('patron_pid')
        self['item_pid'] = params.get('item_pid')
        self['transaction_location_pid'] = params.get('transaction_location_pid')
        self['transaction_date'] = params.get('transaction_date') or datetime.now().isoformat()

    def is_pickup_at_same_library(self, event):
        item_location_pid = current_app.config.get('CIRCULATION_ITEM_LOCATION_RETRIEVER')(self['item_pid'])
        print(self['pickup_location_pid'], item_location_pid)
        return self['pickup_location_pid'] == item_location_pid

    def save(self, event):
        if event.error:
            raise Exception(event.error)
        else:
            self['state'] = self.state
            self.commit()
