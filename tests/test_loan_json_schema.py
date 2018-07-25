# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for loan JSON schema."""

from json import loads

import pytest
from jsonschema.exceptions import ValidationError
from pkg_resources import resource_string

from invenio_circulation.api import STATES, Loan

schema_in_bytes = resource_string(
    'invenio_circulation.schemas', 'loans/loan-v1.0.0.json'
)


def test_state_enum():
    """."""
    schema = loads(schema_in_bytes.decode('utf8'))
    state_dict = schema.get('properties').get('state')
    assert 'enum' in state_dict
    assert state_dict.get('enum') == STATES


def test_loan_params(db, loan_schema):
    """."""
    loan = Loan.create({})

    loan.update(loan_schema)
    with pytest.raises(ValidationError):
        loan.validate()


def test_state_checkout(db, params, loan_schema):
    """."""
    loan = Loan.create({})

    loan.checkout(**params)

    loan.update(loan_schema)
    with pytest.raises(ValidationError):
        loan.validate()


def test_state_checkout_with_loan_pid(db, params, loan_schema):
    """."""
    data = {}
    data.update({'loan_pid': 'loan_pid'})
    data.update(loan_schema)
    loan = Loan.create(data)
    loan.checkout(**params)
    loan.validate()
