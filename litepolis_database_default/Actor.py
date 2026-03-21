import os
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
from .MathResult import MathResultManager

# Import models to register them with SQLModel
from .Users import User
from .Conversations import Conversation
from .Comments import Comment
from .Vote import Vote
from .Participant import Participant
from .Zinvite import Zinvite
from .Einvite import Einvite
from .PasswordReset import PasswordResetToken
from .MathResult import MathResult

from .utils_StarRocks import create_db_and_tables

# Only auto-create tables if not explicitly disabled
# This allows importing the module without triggering table creation
# (useful when extending with additional models)
if os.environ.get("LITEPOLIS_AUTO_CREATE_TABLES", "true").lower() != "false":
    create_db_and_tables()

class DatabaseActor(
    UserManager, 
    ConversationManager, 
    CommentManager, 
    VoteManager,
    ParticipantManager,
    ZinviteManager,
    EinviteManager,
    PasswordResetTokenManager,
    MathResultManager
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
