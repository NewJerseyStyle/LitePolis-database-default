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
from .PasswordReset import PasswordResetTokenManager

# Import models to register them with SQLModel
from .Users import User
from .Conversations import Conversation
from .Comments import Comment
from .Vote import Vote
from .Participant import Participant
from .Zinvite import Zinvite
from .Einvite import Einvite
from .PasswordReset import PasswordResetToken

from .utils_StarRocks import create_db_and_tables
create_db_and_tables()

class DatabaseActor(
    UserManager, 
    ConversationManager, 
    CommentManager, 
    VoteManager,
    ParticipantManager,
    ZinviteManager,
    EinviteManager,
    PasswordResetTokenManager
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
