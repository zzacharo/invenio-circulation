# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation views."""

from copy import deepcopy

from flask import Blueprint, current_app, jsonify, request, url_for
from invenio_db import db
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_records_rest.views import pass_record
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from werkzeug.exceptions import BadRequest

from invenio_circulation.permissions import need_permissions
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search import LoansSearch

from .api import Loan
from .errors import InvalidCirculationPermission, ItemNotAvailable, \
    LoanActionError, MultipleLoansOnItemError, NoValidTransitionAvailable

HTTP_CODES = {
    'method_not_allowed': 405,
    'accepted': 202,
}


def create_error_handlers(blueprint):
    """Create error handlers on blueprint."""
    blueprint.errorhandler(LoanActionError)(create_api_errorhandler(
        status=HTTP_CODES['method_not_allowed'], message='Invalid loan action'
    ))
    records_rest_error_handlers(blueprint)


def extract_transitions_from_app(app):
    """."""
    transitions_config = app.config.get('CIRCULATION_LOAN_TRANSITIONS', {})
    distinct_actions = set()
    for src_state, transitions in transitions_config.items():
        for t in transitions:
            distinct_actions.add(t.get('trigger', 'next'))
    return distinct_actions


def build_url_action_for_pid(pid, action):
    """."""
    return url_for(
        'invenio_circulation.{0}_actions'.format(pid.pid_type),
        pid_value=pid.pid_value,
        action=action,
        _external=True
    )


def build_blueprint_with_loan_actions(app):
    """."""
    blueprint = Blueprint(
        'invenio_circulation',
        __name__,
        url_prefix='',
    )

    create_error_handlers(blueprint)

    endpoints = app.config.get('CIRCULATION_REST_ENDPOINTS', [])
    pid_type = 'loanid'
    options = endpoints.get(pid_type, {})
    if options:
        options = deepcopy(options)
        serializers = {}
        if 'record_serializers' in options:
            rec_serializers = options.get('record_serializers')
            serializers = {mime: obj_or_import_string(func)
                           for mime, func in rec_serializers.items()}

        loan_actions = LoanActionResource.as_view(
            LoanActionResource.view_name.format(pid_type),
            serializers=serializers,
            ctx=dict(
                links_factory=app.config.get('CIRCULATION_LOAN_LINKS_FACTORY')
            ),
        )

        distinct_actions = extract_transitions_from_app(app)
        url = '{0}/<any({1}):action>'.format(
            options['item_route'],
            ','.join(distinct_actions),
        )

        blueprint.add_url_rule(
            url,
            view_func=loan_actions,
            methods=['POST'],
        )

    return blueprint


class LoanActionResource(ContentNegotiatedMethodView):
    """Loan action resource."""

    view_name = '{0}_actions'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(LoanActionResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @need_permissions('loan-read-access')
    @pass_record
    def post(self, pid, record, action, **kwargs):
        """Handle loan action."""
        params = request.get_json()
        try:
            # perform action on the current loan
            record = current_circulation.circulation.trigger(
                record, **dict(params, trigger=action)
            )
            db.session.commit()
        except (
            ItemNotAvailable,
            InvalidCirculationPermission,
            NoValidTransitionAvailable
        ) as ex:
            current_app.logger.exception(ex.msg)
            raise LoanActionError(ex)

        return self.make_response(
            pid, record, HTTP_CODES['accepted'],
            links_factory=self.links_factory
        )


def build_blueprint_with_items_loan(app):
    """Item circulation state blueprint."""
    blueprint = Blueprint(
        'invenio_circulation_item',
        __name__,
        url_prefix='',
    )

    create_error_handlers(blueprint)

    rec_serializers = {
        "application/json": (
            "invenio_records_rest.serializers" ":json_v1_response"
        )
    }
    serializers = {
        mime: obj_or_import_string(func)
        for mime, func in rec_serializers.items()
    }

    from invenio_circulation.links import loan_links_factory
    loan_request = ItemLoanResource.as_view(
        ItemLoanResource.view_name, serializers=serializers,
        ctx=dict(links_factory=loan_links_factory),
    )

    url = 'circulation/items/<pid_value>/loan'

    blueprint.add_url_rule(
        url, view_func=loan_request, methods=["GET"]
    )
    return blueprint


class ItemLoanResource(ContentNegotiatedMethodView):
    """Item circulation state resource."""

    view_name = 'loan_resource'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Resource view contructor."""
        super(ItemLoanResource, self).__init__(serializers, *args, **kwargs)
        for key, value in ctx.items():
            setattr(self, key, value)

    @need_permissions('loan-read-access')
    def get(self, *args, **kwargs):
        """Handle GET request for item state."""
        item_pid = kwargs.get('pid_value', None)
        if not item_pid:
            raise BadRequest()
        loans = list(LoansSearch.search_loans_by_pid(
            item_pid=item_pid,
            filter_states=['ITEM_ON_LOAN',
                           'ITEM_AT_DESK',
                           'ITEM_IN_TRANSIT_FOR_PICKUP',
                           'ITEM_IN_TRANSIT_TO_HOUSE']))
        if loans:
            if len(loans) > 1:
                raise MultipleLoansOnItemError(
                    "Multiple active loans on item {0}".format(item_pid))
            loan = Loan.get_record_by_pid(loans[0].loanid)

            from invenio_circulation.pid.fetchers import loan_pid_fetcher
            loan_pid = loan_pid_fetcher(loan.id, loan)
            return self.make_response(
                loan_pid, loan, 200,
                links_factory=self.links_factory
            )
        return jsonify({})
