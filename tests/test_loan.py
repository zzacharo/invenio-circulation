# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for loan states."""
from copy import deepcopy

import pytest

from invenio_circulation.api import Loan
from invenio_circulation.proxies import current_circulation


def test_loan_checkout_checkin(app, db, params):
    """Test loan checkout and checkin."""
    loan = Loan.create({})
    assert loan['state'] == 'CREATED'

    new_params = deepcopy(params)
    trigger_name = app.config['CIRCULATION_TRANSITIONS_TRIGGER_NAME']
    new_params[trigger_name] = 'checkout'
    loan = current_circulation.machine.to_next(loan, **new_params)
    db.session.commit()
    assert loan['state'] == 'ITEM_ON_LOAN'

    # set same location
    app.config['CIRCULATION_ITEM_LOCATION_RETRIEVER'] = \
        lambda x: params['transaction_location_pid']

    new_params = deepcopy(params)
    loan = current_circulation.machine.to_next(loan, **new_params)
    db.session.commit()
    assert loan['state'] == 'ITEM_RETURNED'


def test_loan_request(app, db, params):
    """Test loan request."""
    loan = Loan.create({})
    assert loan['state'] == 'CREATED'

    new_params = deepcopy(params)
    new_params['pickup_location_pid'] = 'pickup_location_pid'
    trigger_name = app.config['CIRCULATION_TRANSITIONS_TRIGGER_NAME']
    new_params[trigger_name] = 'request'
    loan = current_circulation.machine.to_next(loan, **new_params)
    db.session.commit()
    assert loan['state'] == 'PENDING'


@pytest.mark.skip(reason="Add duration policy in checkout")
def test_storing_loan_parameters(loan_created, app, db, params):
    """."""
    new_params = deepcopy(params)
    trigger_name = app.config['CIRCULATION_TRANSITIONS_TRIGGER_NAME']
    new_params[trigger_name] = 'checkout'
    loan = current_circulation.machine.to_next(loan_created, **new_params)
    db.session.commit()

    params['state'] = 'ITEM_ON_LOAN'
    params['start_date'] = loan['start_date']
    params['end_date'] = loan['end_date']
    assert loan == params


def test_validate_item_in_transit_for_pickup(loan_created, app, db, params):
    """."""
    new_params = deepcopy(params)
    trigger_name = app.config['CIRCULATION_TRANSITIONS_TRIGGER_NAME']
    new_params[trigger_name] = 'request'
    new_params['pickup_location_pid'] = 'pickup_location_pid'
    loan = current_circulation.machine.to_next(loan_created, **new_params)
    db.session.commit()
    assert loan['state'] == 'PENDING'

    app.config[
        'CIRCULATION_ITEM_LOCATION_RETRIEVER'
    ] = lambda x: 'external_location_pid'
    new_params = deepcopy(params)
    loan = current_circulation.machine.to_next(loan_created, **new_params)
    assert loan['state'] == 'ITEM_IN_TRANSIT_FOR_PICKUP'


def test_validate_item_at_desk(loan_created, app, db, params):
    """."""
    new_params = deepcopy(params)
    trigger_name = app.config['CIRCULATION_TRANSITIONS_TRIGGER_NAME']
    new_params[trigger_name] = 'request'
    new_params['pickup_location_pid'] = 'pickup_location_pid'
    loan = current_circulation.machine.to_next(loan_created, **new_params)
    db.session.commit()
    assert loan['state'] == 'PENDING'

    app.config[
        'CIRCULATION_ITEM_LOCATION_RETRIEVER'
    ] = lambda x: 'pickup_location_pid'
    new_params = deepcopy(params)
    loan = current_circulation.machine.to_next(loan_created, **new_params)
    db.session.commit()
    assert loan['state'] == 'ITEM_AT_DESK'


@pytest.mark.skip(reason="Add duration policy in checkout")
def test_conditional_checkout(loan, app, db, params):
    """Test checkout with some conditions."""
    loan.checkout(**params)
    assert loan.state == 'ITEM_ON_LOAN'
    assert loan['start_date'] == params.get('transaction_date')

    loan = Loan.create({})
    loan.checkout(
        **dict(start_date='2020-01-01', end_date='2020-02-01', **params)
    )
    assert loan.state == 'ITEM_ON_LOAN'
    assert loan['start_date'] == '2020-01-01'
    assert loan['end_date'] == '2020-02-01'

    loan = Loan.create({})
    with pytest.raises(ValueError):
        loan.checkout(**dict(start_date='2020-01-xx', **params))
    with pytest.raises(ValueError):
        loan.checkout(**dict(end_date='2020-01-xx', **params))


@pytest.mark.skip(reason="Add duration policy in checking")
def test_conditional_checkin(loan, app, db, params):
    """Test checkin with some conditions."""
    loan.checkout(**params)
    loan.checkin(**params)
    assert loan.state == 'ITEM_RETURNED'

    loan = Loan.create({})
    loan.checkout(**params)
    loan.checkin(**dict(end_date='2020-02-01', **params))
    assert loan.state == 'ITEM_RETURNED'
    assert loan['end_date'] == '2020-02-01'

    loan = Loan.create({})
    loan.checkout(**params)
    with pytest.raises(ValueError):
        loan.checkin(**dict(end_date='2020-01-xx', **params))


@pytest.mark.skip(reason="Fix me")
def test_conditional_request(loan, app, db, params):
    """Test request with some conditions."""
    loan.request(
        **dict(
            pickup_location_pid='my_pickup_location_pid',
            request_expire_date='2020-02-01',
            **params
        )
    )
    assert loan.state == 'PENDING'
    loan['request_expire_date'] == '2020-02-01'
    loan['pickup_location_pid'] == 'my_pickup_location_pid'

    loan = Loan.create({})
    app.config[
        'CIRCULATION_ITEM_LOCATION_RETRIEVER'
    ] = lambda x: 'custom_pickup_location_pid'
    loan.request(**params)
    assert loan.state == 'PENDING'
    loan['pickup_location_pid'] == 'custom_pickup_location_pid'


def test_indexed_loans(indexed_loans):
    """Test mappings, index creation and loans indexing."""
    assert indexed_loans
