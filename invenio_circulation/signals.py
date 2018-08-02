# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Signals for Invenio-Circulation."""

from blinker import Namespace

_signals = Namespace()

loan_state_changed = _signals.signal('loan-state-changed')
"""Loan state changed signal.

Its is broadcasted when a loan transitions to a different state.
"""
