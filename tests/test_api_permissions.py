# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.


"""Test API permissions"""
import json

from flask import url_for
from invenio_accounts.models import User
from invenio_accounts.testutils import login_user_via_session


def test_default_permission_factory(base_app, db, json_headers,
                                    indexed_loans):
    """Test default permission factory."""
    multiple_loans_pid = "item_multiple_pending_on_loan_7"

    with base_app.test_client() as client:
        url = url_for('invenio_circulation_item.loan_resource',
                      pid_value=multiple_loans_pid)
        res = client.get(url, headers=json_headers)
        assert res.status_code == 200


def test_loan_access_anonymous(base_app, db, json_headers,
                               indexed_loans, users):
    """Test access for anonymous user to items loan endpoint."""
    multiple_loans_pid = "item_multiple_pending_on_loan_7"

    with base_app.test_client() as client:
        url = url_for('invenio_circulation_item.loan_resource',
                      pid_value=multiple_loans_pid)
        res = client.get(url, headers=json_headers)
        assert res.status_code == 401


def test_logged_user_no_access(base_app, db, json_headers,
                               indexed_loans, users):
    """Test access for user with no right to see the loan."""
    user = users['user']
    multiple_loans_pid = "item_multiple_pending_on_loan_7"

    with base_app.test_client() as client:
        login_user_via_session(client, email=User.query.get(user.id).email)
        url = url_for('invenio_circulation_item.loan_resource',
                      pid_value=multiple_loans_pid)
        res = client.get(url, headers=json_headers)
        assert res.status_code == 403


def test_logged_user_access_granted(base_app, db, json_headers,
                                    indexed_loans, users):
    """Test access for user with a right to see the loan."""
    user = users['manager']
    multiple_loans_pid = "item_multiple_pending_on_loan_7"

    with base_app.test_client() as client:
        login_user_via_session(client, email=User.query.get(user.id).email)
        url = url_for('invenio_circulation_item.loan_resource',
                      pid_value=multiple_loans_pid)
        res = client.get(url, headers=json_headers)
        res_json = json.loads(res.data.decode('utf-8'))
        assert res_json['metadata']['item_pid'] == multiple_loans_pid
        assert res.status_code == 200
