"""
AIdol repository factories

Uses BaseRepositoryFactory for BaseCrudRouter compatibility.
"""

from aioia_core.factories import BaseRepositoryFactory

from aidol.repositories.aidol import AIdolRepository
from aidol.repositories.companion import CompanionRepository


class AIdolRepositoryFactory(BaseRepositoryFactory[AIdolRepository]):
    """Factory for creating AIdol repositories."""

    def __init__(self):
        super().__init__(repository_class=AIdolRepository)


class CompanionRepositoryFactory(BaseRepositoryFactory[CompanionRepository]):
    """Factory for creating Companion repositories."""

    def __init__(self):
        super().__init__(repository_class=CompanionRepository)
