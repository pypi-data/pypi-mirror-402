from pydantic import BaseModel
from typing import Optional
import base64
import algosdk


# https://developer.algorand.org/docs/rest-apis/indexer/#tealvalue
class TealValue(BaseModel):
    type: int
    bytes: Optional[str]
    uint: Optional[int]

    @property
    def decoded_bytes(self):
        if self.bytes is not None:
            return base64.b64decode(self.bytes)

        return None

    @property
    def decoded_key_string(self):
        try:
            utf_string = self.decoded_bytes.decode("utf-8")

            if utf_string:
                return utf_string
        except:
            pass

        try:
            address = algosdk.encoding.encode_address(self.decoded_bytes)
            if address:
                return address
        except:
            pass

        return None


# https://developer.algorand.org/docs/rest-apis/indexer/#tealkeyvalue
class TealKeyValue(BaseModel):
    key: str
    value: TealValue

    @property
    def decoded_key(self):
        return base64.b64decode(self.key)

    @property
    def decoded_key_string(self):
        return self.decoded_key.decode("utf-8")

    @staticmethod
    def init_from_dict(state: dict):
        try:
            return TealKeyValue(key=state['key'],
                                value=TealValue(**state['value']))
        except:
            raise NotImplementedError(f"Invalid EvalDeltaKeyValue: {state}")
