from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from common.file_field import file_size_validator, upload_path
from common.html_processor import strip_tags

from .base import ProjectBaseModel


class IssueManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .exclude(archived_at__isnull=False)
            .exclude(project__archived_at__isnull=False)
            .exclude(is_draft=True)
        )


class Issue(ProjectBaseModel):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="parent_issue",
    )
    state = models.ForeignKey(
        "project.State",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="state_issue",
    )
    estimate_point = models.IntegerField(
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, verbose_name="Issue Name")
    description = models.JSONField(blank=True, default=dict)
    description_html = models.TextField(blank=True, default="<p></p>")
    description_stripped = models.TextField(blank=True, null=True)
    priority = models.CharField(
        max_length=30,
        choices=(
            ("urgent", "Urgent"),
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
            ("none", "None"),
        ),
        verbose_name="Issue Priority",
        default="none",
    )
    start_date = models.DateField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="assignee",
        through="IssueAssignee",
        through_fields=("issue", "assignee"),
    )
    sort_order = models.FloatField(default=65535)
    labels = models.ManyToManyField(
        "project.Label", blank=True, related_name="labels", through="IssueLabel"
    )
    completed_at = models.DateTimeField(null=True)
    archived_at = models.DateField(null=True)
    is_draft = models.BooleanField(default=False)
    sequence_id = models.IntegerField(default=1, verbose_name="Issue Sequence ID")

    objects = models.Manager()
    issue_objects = IssueManager()

    class Meta:
        verbose_name = "Issue"
        verbose_name_plural = "Issues"
        db_table = "issue"
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if self.state is None:
            """
            If the state is not set, then we will set the default state
            If default state is not set, then we will set the first state
            """
            try:
                from project.models.state import State

                default_state = State.objects.filter(
                    ~models.Q(name="Triage"),
                    project=self.project,
                    default=True,
                ).first()
                if default_state is None:
                    random_state = State.objects.filter(
                        ~models.Q(name="Triage"), project=self.project
                    ).first()
                    self.state = random_state
                else:
                    self.state = default_state
            except ImportError:
                pass
        else:
            """
            If the state is set, then we will check if the issue is completed or not
            If the issue is completed, then we will set the completed_at field
            Else we will set the completed_at field to None
            """
            try:
                from project.models.state import State

                if self.state.group == "completed":
                    self.completed_at = timezone.now()
                else:
                    self.completed_at = None
            except ImportError:
                pass
        if self._state.adding:
            last_id = IssueSequence.objects.filter(project=self.project).aggregate(
                largest=models.Max("sequence")
            )["largest"]
            if last_id:
                self.sequence_id = last_id + 1
            else:
                self.sequence_id = 1
            largest_sort_order = Issue.objects.filter(
                project=self.project, state=self.state
            ).aggregate(largest=models.Max("sort_order"))["largest"]
            if largest_sort_order is not None:
                self.sort_order = largest_sort_order + 10000
        self.description_stripped = (
            None
            if (self.description_html == "" or self.description_html is None)
            else strip_tags(self.description_html)
        )
        super(Issue, self).save(*args, **kwargs)


class IssueSequence(ProjectBaseModel):
    issue = models.ForeignKey(
        Issue,
        on_delete=models.SET_NULL,
        related_name="issue_sequence",
        null=True,
    )
    sequence = models.PositiveBigIntegerField(default=1)
    deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Issue Sequence"
        verbose_name_plural = "Issue Sequences"
        db_table = "issue_sequence"
        ordering = ("-created_at",)


class IssueBlocker(ProjectBaseModel):
    block = models.ForeignKey(
        Issue, related_name="blocker_issues", on_delete=models.CASCADE
    )
    blocked_by = models.ForeignKey(
        Issue, related_name="blocked_issues", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Issue Blocker"
        verbose_name_plural = "Issue Blockers"
        db_table = "issue_blocker"
        ordering = ("-created_at",)


class IssueRelation(ProjectBaseModel):
    issue = models.ForeignKey(
        Issue, related_name="issue_relation", on_delete=models.CASCADE
    )
    related_issue = models.ForeignKey(
        Issue, related_name="issue_related", on_delete=models.CASCADE
    )
    relation_type = models.CharField(
        max_length=20,
        choices=(
            ("duplicate", "Duplicate"),
            ("relates_to", "Relates To"),
            ("blocked_by", "Blocked By"),
        ),
        verbose_name="Issue Relation Type",
        default="blocked_by",
    )

    class Meta:
        unique_together = ["issue", "related_issue"]
        verbose_name = "Issue Relation"
        verbose_name_plural = "Issue Relations"
        db_table = "issue_relation"
        ordering = ("-created_at",)


class IssueMention(ProjectBaseModel):
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="issue_mention"
    )
    mention = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_mention",
    )

    class Meta:
        unique_together = ["issue", "mention"]
        verbose_name = "Issue Mention"
        verbose_name_plural = "Issue Mentions"
        db_table = "issue_mention"
        ordering = ("-created_at",)


class IssueAssignee(ProjectBaseModel):
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="issue_assignee"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_assignee",
    )

    class Meta:
        unique_together = ["issue", "assignee"]
        verbose_name = "Issue Assignee"
        verbose_name_plural = "Issue Assignees"
        db_table = "issue_assignee"
        ordering = ("-created_at",)


class IssueLink(ProjectBaseModel):
    title = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField()
    issue = models.ForeignKey(
        "project.Issue", on_delete=models.CASCADE, related_name="issue_link"
    )
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Issue Link"
        verbose_name_plural = "Issue Links"
        db_table = "issue_link"
        ordering = ("-created_at",)


class IssueAttachment(ProjectBaseModel):
    meta_data = models.JSONField(default=dict)
    file = models.FileField(
        upload_to=upload_path,
        validators=[
            file_size_validator,
        ],
    )
    issue = models.ForeignKey(
        "project.Issue", on_delete=models.CASCADE, related_name="issue_attachment"
    )

    class Meta:
        verbose_name = "Issue Attachment"
        verbose_name_plural = "Issue Attachments"
        db_table = "issue_attachment"
        ordering = ("-created_at",)


class IssueActivity(ProjectBaseModel):
    issue = models.ForeignKey(
        Issue,
        on_delete=models.SET_NULL,
        null=True,
        related_name="issue_activity",
    )
    verb = models.CharField(max_length=255, verbose_name="Action", default="created")
    field = models.CharField(
        max_length=255, verbose_name="Field Name", blank=True, null=True
    )
    old_value = models.TextField(verbose_name="Old Value", blank=True, null=True)
    new_value = models.TextField(verbose_name="New Value", blank=True, null=True)
    comment = models.TextField(verbose_name="Comment", blank=True)
    attachments = ArrayField(
        models.FileField(
            upload_to=upload_path,
            validators=[file_size_validator],
        ),
        size=10,
        blank=True,
        default=list,
    )
    issue_comment = models.ForeignKey(
        "project.IssueComment",
        on_delete=models.SET_NULL,
        related_name="issue_comment",
        null=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="issue_activities",
    )
    old_identifier = models.BigIntegerField(null=True)
    new_identifier = models.BigIntegerField(null=True)
    epoch = models.FloatField(null=True)

    class Meta:
        verbose_name = "Issue Activity"
        verbose_name_plural = "Issue Activities"
        db_table = "issue_activity"
        ordering = ("-created_at",)


class IssueComment(ProjectBaseModel):
    comment_stripped = models.TextField(verbose_name="Comment", blank=True)
    comment_json = models.JSONField(blank=True, default=dict)
    comment_html = models.TextField(blank=True, default="<p></p>")
    attachments = ArrayField(
        models.FileField(
            upload_to=upload_path,
            validators=[file_size_validator],
        ),
        size=10,
        default=list,
        blank=True,
    )
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="issue_comments"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
    )

    def save(self, *args, **kwargs):
        self.comment_stripped = (
            strip_tags(self.comment_html) if self.comment_html != "" else ""
        )
        return super(IssueComment, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Issue Comment"
        verbose_name_plural = "Issue Comments"
        db_table = "issue_comment"
        ordering = ("-created_at",)


class IssueProperty(ProjectBaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_property_user",
    )
    filters = models.JSONField(default=dict)
    display_filters = models.JSONField(default=dict)
    display_properties = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Issue Property"
        verbose_name_plural = "Issue Properties"
        db_table = "issue_property"
        ordering = ("-created_at",)
        unique_together = ["user", "project"]


class Label(ProjectBaseModel):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="parent_label",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.FloatField(default=65535)
    color = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if self._state.adding:
            last_id = Label.objects.filter(project=self.project).aggregate(
                largest=models.Max("sort_order")
            )["largest"]
            if last_id is not None:
                self.sort_order = last_id + 10000
        super(Label, self).save(*args, **kwargs)

    class Meta:
        unique_together = ["name", "project"]
        verbose_name = "Label"
        verbose_name_plural = "Labels"
        db_table = "label"
        ordering = ("-created_at",)


class IssueLabel(ProjectBaseModel):
    issue = models.ForeignKey(
        "project.Issue", on_delete=models.CASCADE, related_name="label_issue"
    )
    label = models.ForeignKey(
        "project.Label", on_delete=models.CASCADE, related_name="label_issue"
    )

    class Meta:
        verbose_name = "Issue Label"
        verbose_name_plural = "Issue Labels"
        db_table = "issue_label"
        ordering = ("-created_at",)


class IssueSubscriber(ProjectBaseModel):
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="issue_subscribers"
    )
    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_subscribers",
    )

    class Meta:
        unique_together = ["issue", "subscriber"]
        verbose_name = "Issue Subscriber"
        verbose_name_plural = "Issue Subscribers"
        db_table = "issue_subscriber"
        ordering = ("-created_at",)


class IssueReaction(ProjectBaseModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_reactions",
    )
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="issue_reactions"
    )
    reaction = models.CharField(max_length=20)

    class Meta:
        unique_together = ["issue", "actor", "reaction"]
        verbose_name = "Issue Reaction"
        verbose_name_plural = "Issue Reactions"
        db_table = "issue_reaction"
        ordering = ("-created_at",)


class CommentReaction(ProjectBaseModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_reactions",
    )
    comment = models.ForeignKey(
        IssueComment,
        on_delete=models.CASCADE,
        related_name="comment_reactions",
    )
    reaction = models.CharField(max_length=20)

    class Meta:
        unique_together = ["comment", "actor", "reaction"]
        verbose_name = "Comment Reaction"
        verbose_name_plural = "Comment Reactions"
        db_table = "comment_reaction"
        ordering = ("-created_at",)


class IssueVote(ProjectBaseModel):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="votes")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    vote = models.IntegerField(
        choices=(
            (-1, "DOWNVOTE"),
            (1, "UPVOTE"),
        ),
        default=1,
    )

    class Meta:
        unique_together = [
            "issue",
            "actor",
        ]
        verbose_name = "Issue Vote"
        verbose_name_plural = "Issue Votes"
        db_table = "issue_vote"
        ordering = ("-created_at",)


class IssueGitPR(ProjectBaseModel):
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="issue_github_pr"
    )
    pr_id = models.IntegerField()
    pr_url = models.URLField()

    class Meta:
        verbose_name = "Issue Github PR"
        unique_together = ["issue", "pr_id"]
        verbose_name_plural = "Issue Github PRs"
        db_table = "issue_github_pr"
        ordering = ("-created_at",)


class IssueGitCommit(ProjectBaseModel):
    issue = models.ForeignKey(
        Issue, on_delete=models.CASCADE, related_name="issue_github_commit"
    )
    commit_id = models.CharField(max_length=255)
    commit_url = models.URLField()

    class Meta:
        verbose_name = "Issue Github Commit"
        unique_together = ["issue", "commit_id"]
        verbose_name_plural = "Issue Github Commits"
        db_table = "issue_github_commit"
        ordering = ("-created_at",)


@receiver(post_save, sender=Issue)
def create_issue_sequence(sender, instance, created, **kwargs):
    if created:
        IssueSequence.objects.create(
            issue=instance,
            sequence=instance.sequence_id,
            project=instance.project,
        )
