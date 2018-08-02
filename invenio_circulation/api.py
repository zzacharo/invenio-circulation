# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation API."""

from elasticsearch_dsl.query import Bool, Q
from flask import current_app
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record

from .search import LoansSearch


class Loan(Record):
    """Loan record class."""

    def __init__(self, data, model=None):
        """."""
        data.setdefault(
            'state',
            current_app.config['CIRCULATION_LOAN_INITIAL_STATE']
        )
        super(Loan, self).__init__(data, model)

    @classmethod
    def get_loans_for_pid(cls, item_pid=None, document_pid=None, filter_states=[],
        exclude_states=[]):
        """."""
        search = LoansSearch()

        if filter_states:
            search = search.query(
                Bool(filter=[Q('terms', state=filter_states)])
            )
        elif exclude_states:
            search = search.query(
                Bool(filter=[~Q('terms', state=exclude_states)])
            )

        if document_pid:
            search = search.filter('term', document_pid=document_pid).source(
                includes='loan_pid'
            )
        elif item_pid:
            search = search.filter('term', item_pid=item_pid).source(
                includes='loan_pid'
            )

        for result in search.scan():
            if result.loan_pid:
                yield cls.get_record_by_pid(result.loan_pid)

    @classmethod
    def get_record_by_pid(cls, pid, with_deleted=False):
        """Get ils record by pid value."""
        from .config import _CIRCULATION_LOAN_PID_TYPE
        resolver = Resolver(
            pid_type=_CIRCULATION_LOAN_PID_TYPE,
            object_type='rec',
            getter=cls.get_record,
        )
        persistent_identifier, record = resolver.resolve(str(pid))
        return record


def is_item_available(item_pid):
    """."""
    config = current_app.config
    cfg_item_available = config['CIRCULATION_POLICIES']['checkout'].get(
        'item_available'
    )
    if not cfg_item_available(item_pid):
        return False

    if any(True for loan in Loan.get_loans_for_pid(
            item_pid=item_pid,
            exclude_states=config.get('CIRCULATION_STATES_ITEM_AVAILABLE'),
        )
    ):
        return False
    return True


def get_pending_loans_by_item_pid(item_pid):
    """."""
    return Loan.get_loans_for_pid(item_pid=item_pid,
                                   filter_states=['PENDING'])


def get_pending_loans_by_doc_pid(document_pid):
    """."""
    return Loan.get_loans_for_pid(document_pid=document_pid,
                                   filter_states=['PENDING'])


def get_available_item_by_doc_pid(document_pid):
    """Returns an item pid available for this document."""
    for item_pid in get_items_by_doc_pid(document_pid):
        if is_item_available(item_pid):
            return item_pid
    return None

def get_items_by_doc_pid(document_pid):
    """Returns a list of item pids for this document."""
    return current_app.config['CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT'](
        document_pid
    )


def get_document_by_item_pid(item_pid):
    """Return the document pid of this item_pid."""
    return current_app.config['CIRCULATION_DOCUMENT_RETRIEVER_FROM_ITEM'](
        item_pid
    )
