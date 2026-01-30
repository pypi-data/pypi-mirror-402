from pydantic import BaseModel

class Urn(BaseModel):
    """Superclass for URN types.

    All URNs are required to have a type identifier.

    Attributes:
        urn_type (str): Required identifier for URN type.

    """    
    urn_type: str
