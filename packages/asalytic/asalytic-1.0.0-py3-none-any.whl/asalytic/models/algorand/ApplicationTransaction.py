from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from asalytic.models.algorand.StateSchema import StateSchema


class OnCompletion(str, Enum):
    noop = 'noop'
    optin = 'optin'
    closeout = 'closeout'
    clear = 'clear'
    update = 'update'
    delete = 'delete'


# https://developer.algorand.org/docs/rest-apis/indexer/#transactionapplic
class ApplicationTransaction(BaseModel):
    accounts: List[str]
    application_args: List[str]
    application_id: int

    # Bytes
    approval_program: Optional[str]

    # Bytes
    clear_state_program: Optional[str]

    extra_program_state: Optional[int]

    foreign_apps: List[int]
    foreign_assets: List[int]

    global_state_schema: Optional[StateSchema]
    local_state_schema: Optional[StateSchema]

    on_completion: OnCompletion

    @staticmethod
    def init_from_application_transaction(app_txn: dict):
        global_schema = None
        local_schema = None

        try:
            global_schema = StateSchema.init_from_schema(app_txn['global-state-schema'])
        except:
            pass

        try:
            local_schema = StateSchema.init_from_schema(app_txn['local-state-schema'])
        except:
            pass

        try:
            return ApplicationTransaction(
                accounts=app_txn.get("accounts", []),
                application_args=app_txn.get("application-args", []),
                application_id=app_txn['application-id'],
                approval_program=app_txn.get('approval-program', None),
                clear_state_program=app_txn.get('clear-state-program', None),
                extra_program_state=app_txn.get('extra-program-pages', None),
                foreign_apps=app_txn.get('foreign-apps', []),
                foreign_assets=app_txn.get('foreign-assets', []),
                global_state_schema=global_schema,
                local_state_schema=local_schema,
                on_completion=OnCompletion(app_txn['on-completion'])
            )
        except:
            return None
