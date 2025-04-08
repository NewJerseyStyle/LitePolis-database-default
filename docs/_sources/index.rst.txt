.. LitePolis database default documentation master file, created by
   sphinx-quickstart on Mon Apr  7 22:04:35 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

LitePolis database default
========================================
This module is designed to be compatible with the original `polis`_ platform.

To integrate this module into your LitePolis middleware or FastAPI-based APIs, import the necessary components. Additionally, ensure that the system administrator configures the ``litepolis_database_default`` section within their ``~/litepolis/litepolis.config`` file.

.. _polis: https://pol.is

.. toctree::
   :maxdepth: 1
   :caption: Reference:

   apis


DatabaseActor
-----------

DatabaseActor class for LitePolis.

This class serves as the central point of interaction between the LitePolis system
and the database module. It aggregates operations from various manager classes,
such as UserManager, ConversationManager, CommentManager, VoteManager, and ReportManager,
providing a unified interface for database interactions.


Users Table
-----------

.. autosummary::
   :toctree: generated

.. automodule:: litepolis_database_default.Users
   :undoc-members:

.. code-block:: python

    from litepolis_database_default import DatabaseActor
    from datetime import datetime

    # Create a user
    user = DatabaseActor.create_user({
        "email": "test@example.com",
        "auth_token": "auth_token",
    })

    # Read a user by ID
    user = DatabaseActor.read_user(user_id=1)

    # Read a user by email
    user = DatabaseActor.read_user_by_email(email="test@example.com")

    # List users with pagination
    users = DatabaseActor.list_users(page=1, page_size=10)

    # Update a user
    user = DatabaseActor.update_user(user_id=1, data={"email": "new_email@example.com"})

    # Delete a user
    success = DatabaseActor.delete_user(user_id=1)

    # Search users by email
    users = DatabaseActor.search_users_by_email(query="example.com")

    # List users by admin status
    users = DatabaseActor.list_users_by_admin_status(is_admin=True)

    # List users created in a date range
    users = DatabaseActor.list_users_created_in_date_range(start_date=datetime(2023, 1, 1), end_date=datetime(2023, 12, 31))

    # Count users
    count = DatabaseActor.count_users()


Comments Table
--------------

.. automodule:: litepolis_database_default.Comments
   :show-inheritance:
   :undoc-members:

.. code-block:: python

    from litepolis_database_default import DatabaseActor
    from datetime import datetime

    # Create a comment
    comment = DatabaseActor.create_comment({
        "text": "This is a comment.",
        "user_id": 1,
        "conversation_id": 1
    })

    # Read a comment by ID
    comment = DatabaseActor.read_comment(comment_id=1)

    # List comments by conversation ID
    comments = DatabaseActor.list_comments_by_conversation_id(conversation_id=1, page=1, page_size=10, order_by="created", order_direction="asc")

    # Update a comment
    updated_comment = DatabaseActor.update_comment(comment_id=1, data={"text": "Updated comment text."})

    # Delete a comment
    success = DatabaseActor.delete_comment(comment_id=1)

    # Search comments
    comments = DatabaseActor.search_comments(query="search term")

    # List comments by user ID
    comments = DatabaseActor.list_comments_by_user_id(user_id=1, page=1, page_size=10)

    # List comments created in a date range
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 31)
    comments = DatabaseActor.list_comments_created_in_date_range(start_date=start, end_date=end)

    # Count comments in a conversation
    count = DatabaseActor.count_comments_in_conversation(conversation_id=1)

    # Get a comment with its replies
    comment = DatabaseActor.get_comment_with_replies(comment_id=1)


Conversations Table
-------------------

.. automodule:: litepolis_database_default.Conversations
   :show-inheritance:
   :undoc-members:

.. code-block:: python

    from litepolis_database_default import DatabaseActor

    # Create a conversation
    conversation = DatabaseActor.create_conversation({
        "title": "New Conversation",
        "description": "A new conversation about a topic.",
    })

    # Read a conversation by ID
    conversation = DatabaseActor.read_conversation(conversation_id=1)

    # List conversations with pagination and ordering
    conversations = DatabaseActor.list_conversations(page=1, page_size=10, order_by="title", order_direction="asc")

    # Update a conversation
    updated_conversation = DatabaseActor.update_conversation(conversation_id=1, data={"title": "Updated Title"})

    # Delete a conversation
    success = DatabaseActor.delete_conversation(conversation_id=1)

    # Search conversations
    conversations = DatabaseActor.search_conversations(query="search term")

    # List conversations by archived status
    conversations = DatabaseActor.list_conversations_by_archived_status(is_archived=True)

    # List conversations created in a date range
    from datetime import datetime

    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 31)
    conversations = DatabaseActor.list_conversations_created_in_date_range(start_date=start, end_date=end)

    # Count conversations
    count = DatabaseActor.count_conversations()

    # Archive a conversation
    archived_conversation = DatabaseActor.archive_conversation(conversation_id=1)



Reports Table
-------------

.. automodule:: litepolis_database_default.Report
   :show-inheritance:
   :undoc-members:

.. code-block:: python

    from litepolis_database_default import DatabaseActor
    from litepolis_database_default.Report import ReportStatus

    # Create a report
    report = DatabaseActor.create_report({
        "reporter_id": 1,
        "target_comment_id": 2,
        "reason": "Inappropriate content",
        "status": "pending"
    })

    # Read a report by ID
    report = DatabaseActor.read_report(report_id=1)

    # List reports by status with pagination and ordering
    reports = DatabaseActor.list_reports_by_status(status=ReportStatus.pending, page=1, page_size=10, order_by="created", order_direction="desc")

    # Update a report
    updated_report = DatabaseActor.update_report(report_id=1, data={"status": "resolved"})

    # Delete a report
    success = DatabaseActor.delete_report(report_id=1)

    # Search reports by reason
    reports = DatabaseActor.search_reports_by_reason(query="inappropriate")

    # List reports by reporter ID with pagination
    reports = DatabaseActor.list_reports_by_reporter_id(reporter_id=1, page=1, page_size=10)

    # List reports created in a date range
    from datetime import datetime
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 31)

    reports = DatabaseActor.list_reports_created_in_date_range(start_date=start, end_date=end)

    # Count reports by status
    count = DatabaseActor.count_reports_by_status(status=ReportStatus.pending)

    # Resolve a report
    resolved_report = DatabaseActor.resolve_report(report_id=1, resolution_notes="Resolved after review.")

    # Escalate a report
    escalated_report = DatabaseActor.escalate_report(report_id=1, resolution_notes="Escalated for further review.")



Votes Table
-----------

.. automodule:: litepolis_database_default.Vote
   :show-inheritance:
   :undoc-members:

.. code-block:: py
    
    # Create a new vote
    from litepolis_database_default import DatabaseActor

    vote = DatabaseActor.create_vote({
        "value": 1,
        "user_id": 1,
        "comment_id": 1
    })

    # Read a vote by ID
    vote = DatabaseActor.read_vote(vote_id=1)

    # Get a vote by user and comment
    vote = DatabaseActor.get_vote_by_user_comment(user_id=1, comment_id=1)

    # List votes by comment ID with pagination and ordering
    votes = DatabaseActor.list_votes_by_comment_id(comment_id=1, page=1, page_size=10, order_by="created", order_direction="asc")

    # Update a vote
    updated_vote = DatabaseActor.update_vote(vote_id=1, data={"value": -1})

    # Delete a vote
    success = DatabaseActor.delete_vote(vote_id=1)

    # List votes by user ID with pagination
    votes = DatabaseActor.list_votes_by_user_id(user_id=1, page=1, page_size=10)

    # List votes created in a date range
    from litepolis_database_default import DatabaseActor
    from datetime import datetime

    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 31)
    votes = DatabaseActor.list_votes_created_in_date_range(start_date=start, end_date=end)

    # Count votes for a comment
    count = DatabaseActor.count_votes_for_comment(comment_id=1)

    # Get vote value distribution for a comment
    distribution = DatabaseActor.get_vote_value_distribution_for_comment(comment_id=1)
