# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for loan mandatory constraints."""

import pytest
from helpers import SwappedConfig

from invenio_circulation.errors import TransitionConstraintsViolation
from invenio_circulation.proxies import current_circulation


def test_should_fail_when_missing_required_params(loan_created):
    """Test that transition fails when there required params are missing."""
    with pytest.raises(TransitionConstraintsViolation):
        current_circulation.circulation.trigger(
            loan_created, **dict(patron_pid='pid', trigger='checkout')
        )


def test_should_fail_when_item_not_exist(loan_created, params):
    """Test that transition fails when loan item do not exists."""
    with pytest.raises(TransitionConstraintsViolation):
        with SwappedConfig('CIRCULATION_ITEM_EXISTS', lambda x: False):
            current_circulation.circulation.trigger(
                loan_created, **dict(params, trigger='checkout')
            )


def test_should_fail_when_item_is_changed(loan_created, db, params):
    """Test that constraints fail if item for an existing loan is changed."""
    loan = current_circulation.circulation.trigger(
        loan_created, **dict(params, trigger='request')
    )
    db.session.commit()

    params['item_pid'] = 'different_item_pid'
    with pytest.raises(TransitionConstraintsViolation):
        current_circulation.circulation.trigger(loan, **dict(params))


def test_should_fail_when_patron_not_exist(loan_created, params):
    """Test that transition fails when loan patron do not exists."""
    with pytest.raises(TransitionConstraintsViolation):
        with SwappedConfig('CIRCULATION_PATRON_EXISTS', lambda x: False):
            current_circulation.circulation.trigger(
                loan_created, **dict(params, trigger='checkout')
            )


def test_should_fail_when_patron_is_changed(loan_created, db, params):
    """Test that constraints fail if patron for an existing loan is changed."""
    loan = current_circulation.circulation.trigger(
        loan_created, **dict(params, trigger='request')
    )
    db.session.commit()

    params['patron_pid'] = 'different_patron_pid'
    with pytest.raises(TransitionConstraintsViolation):
        current_circulation.circulation.trigger(loan, **dict(params))


def test_persist_loan_parameters(loan_created, db, params):
    """Test that input params are correctly persisted."""
    loan = current_circulation.circulation.trigger(
        loan_created, **dict(params, trigger='checkout')
    )
    db.session.commit()

    params['state'] = 'ITEM_ON_LOAN'
    params['start_date'] = loan['start_date']
    params['end_date'] = loan['end_date']
    params['trigger'] = loan['trigger']
    assert loan == params
