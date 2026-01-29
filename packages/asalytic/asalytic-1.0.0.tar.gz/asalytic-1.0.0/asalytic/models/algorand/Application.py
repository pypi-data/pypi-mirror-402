from pydantic import BaseModel
from typing import Optional, Dict, List

from asalytic.models.algorand.ApplicationParams import ApplicationParams
from asalytic.models.algorand.StateSchema import StateSchema


# https://developer.algorand.org/docs/rest-apis/indexer/#application
class Application(BaseModel):
    created_at_round: Optional[int]
    deleted: Optional[bool]
    deleted_at_round: Optional[int]
    id: int
    params: ApplicationParams

    @property
    def app_state(self):
        app_state = {}

        for state in self.params.global_state:

            if state.value.type == 1:
                app_state[state.key] = state.value.decoded_key_string
            else:
                app_state[state.key] = state.value.uint

        return app_state

    def valid_keys(self, required_keys: List[str]) -> bool:

        state_keys = set([state.key for state in self.params.global_state])

        for key in required_keys:
            if key in state_keys:
                continue

            return False

        return True

    def valid_key_values(self, required_key_values: dict) -> bool:

        for k, v in required_key_values.items():
            try:
                is_valid = self.app_state[k] == v
                if not is_valid:
                    return False
            except:
                return False

        return True

    def valid_global_schema(self, required_schema: StateSchema) -> bool:
        if self.params.global_state_schema:
            return self.params.global_state_schema.num_byte_slice == required_schema.num_byte_slice \
                   and self.params.global_state_schema.num_uint == required_schema.num_uint

        return False

    @staticmethod
    def init_from_application(application: dict):
        try:
            return Application(
                created_at_round=application.get('created-at-round', None),
                deleted=application.get('deleted', None),
                deleted_at_round=application.get('deleted-at-round', None),
                id=application['id'],
                params=ApplicationParams.init_from_application_params(params=application['params'])
            )
        except:
            raise NotImplementedError(f"Invalid application response: {application}")
