from pydantic import BaseModel
from typing import Optional, List

from asalytic.models.algorand.TealKeyValue import TealKeyValue
from asalytic.models.algorand.StateSchema import StateSchema


# https://developer.algorand.org/docs/rest-apis/indexer/#applicationparams
class ApplicationParams(BaseModel):
    approval_program: str
    clear_state_program: str
    creator: Optional[str]
    extra_program_pages: Optional[int]
    global_state: List[TealKeyValue]
    global_state_schema: Optional[StateSchema]
    local_state_schema: Optional[StateSchema]

    @staticmethod
    def init_from_application_params(params: dict):
        app_state: List[TealKeyValue] = []

        try:
            app_state = [
                TealKeyValue.init_from_dict(state=state)
                for state in params['global-state']
            ]
        except:
            pass

        global_schema = None
        local_schema = None

        try:
            global_schema = StateSchema.init_from_schema(params['global-state-schema'])
        except:
            pass

        try:
            local_schema = StateSchema.init_from_schema(params['local-state-schema'])
        except:
            pass

        try:
            return ApplicationParams(
                approval_program=params['approval-program'],
                clear_state_program=params['clear-state-program'],
                creator=params.get('creator', None),
                extra_program_pages=params.get('extra-program-pages', None),
                global_state=app_state,
                global_state_schema=global_schema,
                local_state_schema=local_schema
            )
        except:
            return NotImplementedError(f"Invalid application params: {params}")
