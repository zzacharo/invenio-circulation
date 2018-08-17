# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for the circulation of bibliographic items."""

from invenio_records_rest.utils import allow_all

from .api import Loan
from .links import loan_links_factory
from .search import LoansSearch
from .transitions.transitions import CreatedToItemOnLoan, CreatedToPending, \
    ItemAtDeskToItemOnLoan, ItemInTransitHouseToItemReturned, \
    ItemOnLoanToItemInTransitHouse, ItemOnLoanToItemOnLoan, \
    ItemOnLoanToItemReturned, PendingToItemAtDesk, \
    PendingToItemInTransitPickup
from .utils import get_default_extension_duration, \
    get_default_extension_max_count, get_default_loan_duration, \
    is_item_available, is_loan_duration_valid, item_exists, \
    item_location_retriever, patron_exists

_CIRCULATION_LOAN_PID_TYPE = 'loan_pid'
"""."""

_CIRCULATION_LOAN_MINTER = 'loan_pid'
"""."""

_CIRCULATION_LOAN_FETCHER = 'loan_pid'
"""."""

_Loan_PID = 'pid(loan_pid,record_class="invenio_circulation.api:Loan")'
"""."""

_CIRCULATION_LOAN_LINKS_FACTORY = loan_links_factory
"""."""

CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT = None
"""Function that returns a list of item pids given a document pid."""

CIRCULATION_DOCUMENT_RETRIEVER_FROM_ITEM = None
"""Function that returns the document pid of a given item pid."""

CIRCULATION_PERMISSION_FACTORY = allow_all
"""."""

CIRCULATION_STATES_ITEM_AVAILABLE = ['ITEM_RETURNED']
"""."""

CIRCULATION_LOAN_TRANSITIONS = {
    'CREATED': [
        dict(dest='PENDING', trigger='request', transition=CreatedToPending),
        dict(dest='ITEM_ON_LOAN', trigger='checkout',
             transition=CreatedToItemOnLoan)
    ],
    'PENDING': [
        dict(dest='ITEM_AT_DESK', transition=PendingToItemAtDesk),
        dict(dest='ITEM_IN_TRANSIT_FOR_PICKUP',
             transition=PendingToItemInTransitPickup),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_AT_DESK': [
        dict(dest='ITEM_ON_LOAN', transition=ItemAtDeskToItemOnLoan),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_IN_TRANSIT_FOR_PICKUP': [
        dict(dest='ITEM_AT_DESK'),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_ON_LOAN': [
        dict(dest='ITEM_RETURNED', transition=ItemOnLoanToItemReturned),
        dict(dest='ITEM_IN_TRANSIT_TO_HOUSE',
             transition=ItemOnLoanToItemInTransitHouse),
        dict(dest='ITEM_ON_LOAN', transition=ItemOnLoanToItemOnLoan,
             trigger='extend'),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_IN_TRANSIT_TO_HOUSE': [
        dict(dest='ITEM_RETURNED',
             transition=ItemInTransitHouseToItemReturned),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_RETURNED': [],
    'CANCELLED': [],
}
"""."""

CIRCULATION_LOAN_INITIAL_STATE = 'CREATED'
"""."""

CIRCULATION_PATRON_EXISTS = patron_exists
"""."""

CIRCULATION_ITEM_EXISTS = item_exists
"""."""

CIRCULATION_ITEM_LOCATION_RETRIEVER = item_location_retriever
"""."""

CIRCULATION_POLICIES = dict(
    checkout=dict(
        duration_default=get_default_loan_duration,
        duration_validate=is_loan_duration_valid,
        item_available=is_item_available
    ),
    extension=dict(
        from_end_date=True,
        duration_default=get_default_extension_duration,
        max_count=get_default_extension_max_count
    ),
)
"""."""

CIRCULATION_REST_ENDPOINTS = dict(
    loan_pid=dict(
        pid_type=_CIRCULATION_LOAN_PID_TYPE,
        pid_minter=_CIRCULATION_LOAN_MINTER,
        pid_fetcher=_CIRCULATION_LOAN_FETCHER,
        search_class=LoansSearch,
        search_type=None,
        record_class=Loan,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/circulation/loan/',
        item_route='/circulation/loan/<{0}:pid_value>'.format(_Loan_PID),
        default_media_type='application/json',
        links_factory_imp=_CIRCULATION_LOAN_LINKS_FACTORY,
        max_result_window=10000,
        error_handlers=dict(),
    ),
)
"""."""
