
from .identity_base import IdentityBase

class PassthruIdentity(IdentityBase):
    def __init__(self, config: dict):
        super().__init__(config)

    def get_user_info(self, identity: str) -> dict:
        return {"identity": identity}