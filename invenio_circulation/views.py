from flask import Blueprint
from .api import Loan

blueprint = Blueprint(
    'circulation_loan',
    __name__,
)


def build_endpoints_from_trasitions(app):
    transitions = app.config.get('CIRCULATION_LOAN_TRANSITIONS', [])
    for transition in transitions:
        blueprint.add_url_rule('{action}'.format(
            action=transition['trigger']
            ),
            transition['trigger'],
            getattr(Loan, 'save') # it's not working here cause transition is in self
        )
