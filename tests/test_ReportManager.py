from litepolis_database_default.Report import ReportManager, Report
from litepolis_database_default.Comments import CommentManager
from litepolis_database_default.Actor import DatabaseActor
import pytest
from typing import Optional

def test_create_report():
    # Create test user
    reporter = DatabaseActor.create_user({
        "email": "reporter1@example.com",
        "auth_token": "reporter-token"
    })
    
    # Create test comment
    comment = CommentManager.create_comment({
        "text": "Test comment",
        "user_id": reporter.id,
        "conversation_id": 1
    })
    
    # Create report
    report = ReportManager.create_report({
        "reporter_id": reporter.id,
        "target_comment_id": comment.id,
        "reason": "Test reason"
    })
    
    assert report.id is not None
    assert report.reporter_id == reporter.id
    assert report.target_comment_id == comment.id
    assert report.reason == "Test reason"
    assert report.status == "pending"

    # Clean up
    assert DatabaseActor.delete_user(reporter.id)
    assert CommentManager.delete_comment(comment.id)
    assert ReportManager.delete_report(report.id)

def test_get_report():
    # Create test user
    reporter = DatabaseActor.create_user({
        "email": "reporter2@example.com",
        "auth_token": "reporter-token"
    })
    
    # Create test comment
    comment = CommentManager.create_comment({
        "text": "Test comment",
        "user_id": reporter.id,
        "conversation_id": 1
    })
    
    # Create report
    report = ReportManager.create_report({
        "reporter_id": reporter.id,
        "target_comment_id": comment.id,
        "reason": "Test reason"
    })
    
    # Retrieve report
    retrieved_report = ReportManager.read_report(report.id)
    assert retrieved_report.id == report.id
    assert retrieved_report.reporter_id == reporter.id

    # Clean up
    assert DatabaseActor.delete_user(reporter.id)
    assert CommentManager.delete_comment(comment.id)
    assert ReportManager.delete_report(report.id)


def test_update_report_status():
    # Create test user
    reporter = DatabaseActor.create_user({
        "email": "reporter3@example.com",
        "auth_token": "reporter-token"
    })
    
    # Create test comment
    comment = CommentManager.create_comment({
        "text": "Test comment",
        "user_id": reporter.id,
        "conversation_id": 1
    })
    
    # Create report
    report = ReportManager.create_report({
        "reporter_id": reporter.id,
        "target_comment_id": comment.id,
        "reason": "Test reason"
    })
    
    # Update status
    new_status = "resolved"
    ReportManager.update_report(report.id, {"status": new_status})
    
    # Verify update
    retrieved_report = ReportManager.read_report(report.id)
    assert retrieved_report.status == new_status

    # Clean up
    assert DatabaseActor.delete_user(reporter.id)
    assert CommentManager.delete_comment(comment.id)
    assert ReportManager.delete_report(report.id)

def test_delete_report():
    # Create test user
    reporter = DatabaseActor.create_user({
        "email": "reporter4@example.com",
        "auth_token": "reporter-token"
    })
    
    # Create test comment
    comment = CommentManager.create_comment({
        "text": "Test comment",
        "user_id": reporter.id,
        "conversation_id": 1
    })
    
    # Create report
    report = ReportManager.create_report({
        "reporter_id": reporter.id,
        "target_comment_id": comment.id,
        "reason": "Test reason"
    })
    
    # Delete report
    ReportManager.delete_report(report.id)
    
    # Verify deletion
    retrieved_report = ReportManager.read_report(report.id)
    assert retrieved_report is None

    # Clean up
    assert DatabaseActor.delete_user(reporter.id)
    assert CommentManager.delete_comment(comment.id)
