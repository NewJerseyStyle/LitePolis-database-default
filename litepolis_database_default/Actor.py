from typing import Dict, Any, List
from sqlmodel import SQLModel

from .Conversations import ConversationManager
from .Comments import CommentManager
from .Users import UserManager
from .Vote import VoteManager
from .Participant import ParticipantManager
from .Zinvite import ZinviteManager
from .Einvite import EinviteManager
from .MigrationRecord import MigrationRecordManager

from .utils_StarRocks import create_db_and_tables
create_db_and_tables()

class DatabaseActor(
    UserManager, 
    ConversationManager, 
    CommentManager, 
    VoteManager,
    ParticipantManager,
    ZinviteManager,
    EinviteManager
):
    """
    DatabaseActor class for LitePolis.

    This class serves as the central point of interaction between the LitePolis system
    and the database module. It aggregates operations from various manager classes,
    such as UserManager, ConversationManager, CommentManager, VoteManager,
    ParticipantManager, ZinviteManager, EinviteManager,
    providing a unified interface for database interactions.
    """
    pass
