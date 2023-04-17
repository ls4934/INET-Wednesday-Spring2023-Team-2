from django.db import models
from login.models import Custom_User
from django.utils import timezone
from multiselectfield import MultiSelectField

from datetime import datetime, timedelta
from pytz import timezone

from django.conf import settings
from django.utils.timezone import make_aware

from django.utils.timezone import get_current_timezone

# naive_datetime = datetime.now()
# settings.TIME_ZONE
# aware_datetime = make_aware(naive_datetime)
# aware_datetime.tzinfo


def resut_reveal_time_function():
    return datetime.now() + timedelta(hours=0)


# Create your models here.


class Post_Model(models.Model):
    question_text = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        Custom_User, related_name="posts_created", on_delete=models.CASCADE
    )
    viewed_by = models.ManyToManyField(
        Custom_User, related_name="posts_viewed", blank=True
    )

    # view_time = models.DateTimeField(auto_now_add=True, blank=True)

    category_list = [
        ("sports", "Sports"),
        ("fantasy", "Fantasy"),
        ("entertainment", "Entertainment"),
        ("misc", "Misc"),
    ]
    category = MultiSelectField(
        max_length=100, choices=category_list, max_choices=3, default="misc"
    )

    # created_time = models.DateTimeField(auto_now_add=True, blank=True)
    created_time = models.DateTimeField(
        default=datetime.now, editable=False, blank=True
    )
    result_reveal_time = models.DateTimeField(default=resut_reveal_time_function)
    reported_by = models.ManyToManyField(
        Custom_User, related_name="reported_post_user", blank=True
    )
    reported_count = models.IntegerField(default=0)

    def __str__(self):
        return str(self.id) + " => " + self.question_text


class Options_Model(models.Model):
    question = models.ForeignKey(Post_Model, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    chosen_by = models.ManyToManyField(
        Custom_User, related_name="user_option", blank=True
    )

    color_list = [
        ("AED9E0", "AED9E0"),
        ("8CB369", "8CB369"),
        ("D7A5E4", "D7A5E4"),
        ("5D6DD3", "5D6DD3"),
    ]
    color = models.CharField(max_length=6, choices=color_list, default="AED9E0")

    def __str__(self):
        return self.question.__str__() + " : " + self.choice_text


class Comments_Model(models.Model):
    question = models.ForeignKey(Post_Model, on_delete=models.CASCADE)
    commented_by = models.ForeignKey(
        Custom_User,
        related_name="comments_created",
        on_delete=models.CASCADE,
        default=1,
    )
    comment_text = models.CharField(max_length=500)
    commented_time = models.DateTimeField(default=datetime.now, blank=True)
    reported_by = models.ManyToManyField(
        Custom_User, related_name="reported_comment_user", blank=True
    )
    reported_count = models.IntegerField(default=0)
    upvoted_by = models.ManyToManyField(
        Custom_User, related_name="upvoted_comment_user", blank=True
    )
    downvoted_by = models.ManyToManyField(
        Custom_User, related_name="downvoted_comment_user", blank=True
    )
    vote_count = models.IntegerField(default=0)
    option_voted = models.ForeignKey(
        Options_Model,
        on_delete=models.CASCADE,
        related_name="comment_option_voted",
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            self.question.__str__()
            + " => "
            + self.commented_by.__str__()
            + " : "
            + self.comment_text
        )


class UserPostViewTime(models.Model):
    user = models.ForeignKey(
        Custom_User, related_name="posts_view_time", on_delete=models.CASCADE
    )

    post = models.ForeignKey(Post_Model, on_delete=models.CASCADE)

    view_time = models.DateTimeField(default=datetime.now, blank=True)


class Noti_Model(models.Model):
    recipient = models.ForeignKey(
        Custom_User, on_delete=models.CASCADE, related_name="notifications"
    )
    sender = models.ForeignKey(
        Custom_User, on_delete=models.CASCADE, related_name="sent_notifications"
    )
    post_at = models.ForeignKey(
        Post_Model, on_delete=models.CASCADE, related_name="post_notifications_at"
    )
    noti_type_options = [
        ("Invalid", "Invalid"),
        ("At", "At"),
        ("Comment", "Comment"),
    ]

    noti_type = models.CharField(
        max_length=20, choices=noti_type_options, default="Invalid"
    )
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return (
            "recipient:"
            + self.recipient.__str__()
            + "<= sender: "
            + self.sender.__str__()
            + "//postid: "
            + self.post_at.id.__str__()
            + "//type: "
            + self.noti_type.__str__()
        )
