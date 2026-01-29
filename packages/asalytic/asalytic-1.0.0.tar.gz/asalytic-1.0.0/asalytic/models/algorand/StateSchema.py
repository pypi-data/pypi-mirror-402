from pydantic import BaseModel


# https://developer.algorand.org/docs/rest-apis/indexer/#stateschema
class StateSchema(BaseModel):
    num_byte_slice: int
    num_uint: int

    # TODO: Read Pydantic this should be able by the default init.
    @staticmethod
    def init_from_schema(schema: dict):
        try:
            return StateSchema(
                num_byte_slice=schema['num-byte-slice'],
                num_uint=schema['num-uint']
            )
        except:
            raise NotImplementedError(f"Invalid StateSchema parsing: {schema}")
