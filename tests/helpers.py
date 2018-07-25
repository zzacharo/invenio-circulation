# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helper methods for tests."""

import copy
import uuid

from invenio_db import db
from invenio_pidstore import current_pidstore

from invenio_circulation.api import Loan


def create_loan(data):
    """Create a test record."""
    with db.session.begin_nested():
        data = copy.deepcopy(data)
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['circ_loanid'](rec_uuid, data)
        record = Loan.create(data, id_=rec_uuid)
    return pid, record
