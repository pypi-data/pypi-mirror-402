from ...endpoints import User
from ..base import AuthClaim
from ..granting.results import BaseGrantingResult
from collections.abc import Sequence
from dataclasses import dataclass

__all__ = ['GrantingClaimParams', 'GrantingClaim']

@dataclass(frozen=True)
class GrantingClaimParams:
    claim: AuthClaim
    admin: User
    user: User
    cloud_admins_domains: Sequence[str]

class GrantingClaim(AuthClaim):
    def grant_claim(self, params: GrantingClaimParams) -> BaseGrantingResult: ...
