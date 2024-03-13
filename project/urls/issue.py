from django.urls import path

from project.views import (
    BulkCreateIssueLabelsEndpoint,
    BulkDeleteIssuesEndpoint,
    CommentReactionViewSet,
    IssueActivityEndpoint,
    IssueArchiveViewSet,
    IssueAttachmentEndpoint,
    IssueCommentViewSet,
    IssueDraftViewSet,
    IssueLinkViewSet,
    IssueListEndpoint,
    IssueReactionViewSet,
    IssueRelationViewSet,
    IssueSubscriberViewSet,
    IssueUserDisplayPropertyEndpoint,
    IssueViewSet,
    LabelViewSet,
    SubIssuesEndpoint,
)

urlpatterns = [
    path(
        "<str:workspace_slug>/<int:project_id>/issues/list/",
        IssueListEndpoint.as_view(),
        name="project-issue",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/",
        IssueViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:pk>/",
        IssueViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-issue",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/labels/",
        LabelViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue-labels",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/labels/<int:pk>/",
        LabelViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-issue-labels",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/labels/create",
        BulkCreateIssueLabelsEndpoint.as_view(),
        name="project-bulk-labels",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/delete/",
        BulkDeleteIssuesEndpoint.as_view(),
        name="project-issues-bulk",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/sub/",
        SubIssuesEndpoint.as_view(),
        name="sub-issues",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/links/",
        IssueLinkViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue-links",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/links/<int:pk>/",
        IssueLinkViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-issue-links",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/attachments/",
        IssueAttachmentEndpoint.as_view(),
        name="project-issue-attachments",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/attachments/<int:pk>/",
        IssueAttachmentEndpoint.as_view(),
        name="project-issue-attachments",
    ),
    ## End Issues
    ## Issue Activity
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/history/",
        IssueActivityEndpoint.as_view(),
        name="project-issue-history",
    ),
    ## Issue Activity
    ## IssueComments
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/comments/",
        IssueCommentViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue-comment",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/comments/<int:pk>/",
        IssueCommentViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-issue-comment",
    ),
    ## End IssueComments
    # Issue Subscribers
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/subscribe/",
        IssueSubscriberViewSet.as_view(
            {
                "get": "subscription_status",
                "post": "subscribe",
                "delete": "unsubscribe",
            }
        ),
        name="project-issue-subscribers",
    ),
    ## End Issue Subscribers
    # Issue Reactions
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/reactions/",
        IssueReactionViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue-reactions",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/reactions/<str:reaction_code>/",
        IssueReactionViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="project-issue-reactions",
    ),
    ## End Issue Reactions
    # Comment Reactions
    path(
        "<str:workspace_slug>/<int:project_id>/comments/<int:comment_id>/reactions/",
        CommentReactionViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue-comment-reactions",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/comments/<int:comment_id>/reactions/<str:reaction_code>/",
        CommentReactionViewSet.as_view(
            {
                "delete": "destroy",
            }
        ),
        name="project-issue-comment-reactions",
    ),
    ## End Comment Reactions
    ## IssueProperty
    path(
        "<str:workspace_slug>/<int:project_id>/user-properties/",
        IssueUserDisplayPropertyEndpoint.as_view(),
        name="project-issue-display-properties",
    ),
    ## IssueProperty End
    ## Issue Archives
    path(
        "<str:workspace_slug>/<int:project_id>/archived-issues/",
        IssueArchiveViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="project-issue-archive",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:pk>/archive/",
        IssueArchiveViewSet.as_view(
            {
                "get": "retrieve",
                "post": "archive",
                "delete": "unarchive",
            }
        ),
        name="project-issue-archive-unarchive",
    ),
    ## End Issue Archives
    ## Issue Relation
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/relation/",
        IssueRelationViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="issue-relation",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issues/<int:issue_id>/relation/delete/",
        IssueRelationViewSet.as_view(
            {
                "post": "remove_relation",
            }
        ),
        name="issue-relation",
    ),
    ## End Issue Relation
    ## Issue Drafts
    path(
        "<str:workspace_slug>/<int:project_id>/issue/drafts/",
        IssueDraftViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-issue-draft",
    ),
    path(
        "<str:workspace_slug>/<int:project_id>/issue/drafts/<int:pk>/",
        IssueDraftViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-issue-draft",
    ),
]
