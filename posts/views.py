from datetime import timedelta, datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.template import loader
from django.views import View
from django.db.models import Q, Sum
from django.utils.safestring import mark_safe
from .forms import PollForm
import re
from django.views.generic import TemplateView
from login.models import Custom_User

from django.utils import timezone

# import datetime

from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view

from django.contrib.auth.decorators import login_required


import random
import json

from .models import (
    Post_Model,
    Options_Model,
    Comments_Model,
    UserPostViewTime,
    Noti_Model,
)
from .forms import CommentsForm
from login.models import Custom_User


# use rest-framework.APIView
# restrict api urls from being accessed
# need to do ajax implementation for other urls (notification, profile, chat)
# comment revealed after result voting
# make an api return func to give polls and once next or home ot polls is clicked, ajax calls this func to get the next poll

# Create your views here.

# current_pid = None


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


def get_random_pid(current_pid=None, category=None):
    if category:
        # pids = Post_Model.objects.filter(category=category)
        # pids = Post_Model.objects.filter(category__iexact=category).filter(
        #     ~Q(id=current_pid)
        # )
        pids = Post_Model.objects.filter(category__contains=category).filter(
            ~Q(id=current_pid)
        )
        # pids = Post_Model.objects.filter(~Q(id=current_pid))
    else:
        # pids = Post_Model.objects.all()
        pids = Post_Model.objects.filter(~Q(id=current_pid))

    # print(f"Category: {category}")  # Debugging line
    # print(f"PIDs: {pids}")          # Debugging line

    ##to check if user has alread seen/ interaacted with the post
    # if request.user.is_authenticated:
    #     user_posts_viewed = request.user.posts_viewed.all()
    #     pids = pids.difference(user_posts_viewed)

    try:
        pid = random.choice(list(pids))
        pid = pid.pk

        return (pid, True)

    except:
        return (None, False)


# home page - will generate random post id that user hasn't interacted with to display for user - will change to empty later in urls
# generate id and redirect/reverse with that parameter
def home_view(request):
    pid, truth = get_random_pid()

    if truth:
        return redirect(
            reverse(
                "posts:post_generation_page", kwargs={"category": "all", "pid": pid}
            )
        )
    else:
        return render(request, "pages/poll_empty.html")


def only_id_post_view(request, pid):
    return redirect(
        reverse("posts:post_generation_page", kwargs={"category": "all", "pid": pid})
    )


# def posts_view(request, pid, call="noapi"):
# post_ = Post_Model.objects.get(pk=pid)
# options_ = post_.options_model_set.all()

# ##to directly show results if user has already voted!
# ## Remove later as user should not even see posts that has already been interacted with
# # if post_.viewed_by.filter(username=request.user.username).exists():
# #     #display results
# #     return results_view(request, pid)

# if request.method == "POST":
#     try:
#         selected_choice = post_.options_model_set.get(pk=request.POST["option"])
#     except (KeyError, Options_Model.DoesNotExist):
#         print("error")
#         messages.error(request, "Select an option to submit!")

#         template = loader.get_template("pages/poll_disp.html")
#         post_ = Post_Model.objects.get(pk=pid)
#         options_ = post_.options_model_set.all()
#         contents = {"post": post_, "options": options_, "display_result": False}
#         return HttpResponse(template.render(contents, request))

#         # else:
#         #     template = loader.get_template("pages/poll_disp.html")
#         #     post_ = Post_Model.objects.get(pk=pid)
#         #     options_ = post_.options_model_set.all()
#         #     contents = {"post": post_, "options": options_, "display_result": False}
#         #     return HttpResponse(template.render(contents, request))
#         #     # contents = {"post": post_, "options": options_, "display_result": False}
#         #     # return render(request, "pages/posts_home.html", contents)

#     selected_choice.votes += 1
#     selected_choice.chosen_by.add(request.user)
#     selected_choice.save()

#     post_.viewed_by.add(request.user)
#     post_.save()

#     # display results
#     return results_view(request, pid)

# contents = {"post": post_, "options": options_, "display_result": False}
# return render(request, "pages/posts_home.html", contents)

# template = loader.get_template("pages/poll_disp.html")
# post_ = Post_Model.objects.get(pk=pid)
# options_ = post_.options_model_set.all()
# contents = {"post": post_, "options": options_, "display_result": False}
# return HttpResponse(template.render(contents, request))


##need a json response here as post method automatically returns whatever is in this function and renders it!
def results_view(request, pid, change_url, category):
    post_ = Post_Model.objects.get(pk=pid)
    options_ = post_.options_model_set.all().order_by("id")
    user_option = request.user.user_option.get(question=post_)

    # user_choice = post_.options_model_set.get(chosen_by=request.user)
    # user_color_ = user_choice.color
    contents = {
        "post": post_,
        "options": options_,
        "pid": pid,
        "user_option": user_option,
        "show_poll_results": False,
        "change_url": change_url,
        "category": category,
    }
    template = loader.get_template("pages/poll_result.html")

    # use this to get user's choice and color code the username in comments to match the choice!
    # user_choice = post_.options_model_set.get(chosen_by=request.user)
    # user_color = user_choice.color
    # print(user_choice, user_color)

    # print(post_.result_reveal_time - timedelta(hours=5), datetime.now())

    # print(timezone.localtime(post_.result_reveal_time).replace(tzinfo=None), post_.result_reveal_time.replace(tzinfo=None), datetime.now())
    if (
        timezone.localtime(post_.result_reveal_time).replace(tzinfo=None)
        < datetime.now()
    ):
        contents["show_poll_results"] = True

    return HttpResponse(template.render(contents, request))

    # return render(request, "pages/posts_home.html", contents)


def show_analytics(request):
    pid = request.GET.get("pid")
    post_ = Post_Model.objects.get(pk=pid)
    options_ = Options_Model.objects.filter(question=post_)

    total_votes = sum(option.votes for option in options_)
    percentage_list = [option.votes / total_votes * 100 for option in options_]

    option_percentage_list = zip(options_, percentage_list)

    contents = {
        "post": post_,
        "option_percentage_list": option_percentage_list,
    }

    template = loader.get_template("pages/poll_analytics.html")

    return HttpResponse(template.render(contents, request))


##api view
## once next button is clicked, it goes to test1func and u call post view from here with random pid and call="api"
# def test1_view(request):
# return JsonResponse({'hello': 'world'})
# print(request, request.GET['hello'])
# template = loader.get_template("pages/poll_disp.html")
# post_ = Post_Model.objects.all()
# post_ = Post_Model.objects.get(pk=1)
# options_ = post_.options_model_set.all()
# contents = {"post": post_, "options": options_, "display_result": False}
# return HttpResponse(template.render(contents, request))


# shows whether you have voted or not
# if voted, then results. if not, poll
def show_curr_post_api_view(request, category, current_pid):
    if is_ajax(request):
        pid = current_pid
        post_view_class = PostsView()
        if request.method == "GET":
            return post_view_class.get(
                request=request, category=category, pid=pid, call="api"
            )
        return post_view_class.post(
            request=request, category=category, pid=pid, call="api"
        )
    else:
        return HttpResponse("Thou Shall not Enter!!")


# put ajax in poll_disp.html


class PostsView(View):
    def get(self, request, category, pid, call="noapi", change_url=True):
        try:
            post_ = Post_Model.objects.get(pk=pid, category__contains=category)
        except Post_Model.DoesNotExist:
            try:
                post_ = Post_Model.objects.get(pk=pid)
                category = "all"
            except Post_Model.DoesNotExist:
                if call == "api":
                    return render(request, "pages/poll_end.html")
                contents = {
                    "pid": "0",
                    "category": category,
                }
                return render(request, "pages/posts_home.html", contents)
        options_ = post_.options_model_set.all().order_by("id")

        if call == "noapi":
            contents = {
                "post": post_,
                "options": options_,
                "pid": pid,
                "category": category,
            }
            print(pid, call)
            return render(request, "pages/posts_home.html", contents)

        if post_.viewed_by.filter(username=request.user.username).exists():
            # display results
            return results_view(request, pid, change_url, category)

        template = loader.get_template("pages/poll_disp.html")
        contents = {
            "post": post_,
            "options": options_,
            "pid": pid,
            "change_url": change_url,
            "category": category,
        }
        return HttpResponse(template.render(contents, request))

    def post(self, request, category, pid, call="noapi"):
        if is_ajax(request):
            post_ = Post_Model.objects.get(pk=pid)
            try:
                selected_choice = post_.options_model_set.get(pk=request.POST["option"])
            except (KeyError, Options_Model.DoesNotExist):
                print("error")
                messages.error(request, "Select an option to submit!")
                return JsonResponse({"voting": "Wrong request"})

            if request.user.is_authenticated:
                selected_choice.votes += 1
                selected_choice.chosen_by.add(request.user)
                post_.viewed_by.add(request.user)
                post_.save()
                selected_choice.save()

            if (
                request.user.is_authenticated
                and not request.user.posts_view_time.filter(post=post_).exists()
            ):
                # print(request.user.posts_view_time.all())
                user_post_view_time_model = UserPostViewTime.objects.create(
                    user=request.user, post=post_
                )
                # user_post_view_time_model.post.add(post_)
                # user_post_view_time_model.save()

                # user_post_view_time_model.save()

            # request.user.posts_view_time.post = post_
            # request.user.posts_view_time.save()

            return JsonResponse({"voting": "success"})
        return JsonResponse({"voting": "Wrong request"})


class SearchPostsView(TemplateView):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("search", "")

        if query:
            post_results = Post_Model.objects.filter(
                Q(question_text__icontains=query)
                | Q(options_model__choice_text__icontains=query)
            ).distinct()

            user_results = Custom_User.objects.filter(
                Q(username__icontains=query)
            ).distinct()
        else:
            post_results = Post_Model.objects.none()
            user_results = Custom_User.objects.none()

        search_results = []
        for post in post_results:
            options = []
            # create an array for options based on the Options_Model.question=post
            for option in Options_Model.objects.filter(question=post):
                options.append(
                    {
                        "choice_text": option.choice_text,
                    }
                )

            search_results.append(
                {
                    "id": post.id,
                    "question_text": post.question_text,
                    "category": post.category,
                    "options": options,
                }
            )

        for user in user_results:
            search_results.append(
                {
                    "id": user.id,
                    "username": user.username,
                }
            )

        return JsonResponse({"search_results": search_results})


# def posts_view(request, pid, call="noapi"):
#     post_ = Post_Model.objects.get(pk=pid)
#     options_ = post_.options_model_set.all()

#     ##to directly show results if user has already voted!
#     ## Remove later as user should not even see posts that has already been interacted with
#     # if post_.viewed_by.filter(username=request.user.username).exists():
#     #     #display results
#     #     return results_view(request, pid)

#     if request.method == "POST" and is_ajax(request):
#         try:
#             selected_choice = post_.options_model_set.get(pk=request.POST["option"])
#         except (KeyError, Options_Model.DoesNotExist):
#             print("error")
#             messages.error(request, "Select an option to submit!")
#             return

#             # template = loader.get_template("pages/poll_disp.html")
#             # post_ = Post_Model.objects.get(pk=pid)
#             # options_ = post_.options_model_set.all()
#             # contents = {"post": post_, "options": options_, 'pid': pid}
#             # # return HttpResponse(template.render(contents, request))
#             # return JsonResponse({'voting': 'Failed!'})


#         selected_choice.votes += 1
#         selected_choice.chosen_by.add(request.user)
#         selected_choice.save()

#         post_.viewed_by.add(request.user)
#         post_.save()

#         # display results
#         # return results_api_view(request, pid, call="api")
#         return JsonResponse({'voting': 'success'})

#     elif request.method == 'POST':
#         return JsonResponse({'voting': 'success'})

#     if call == "noapi":
#         print("Hello")
#         contents = {"post": post_, "options": options_, 'pid': pid}
#         return render(request, "pages/post_home.html", contents)

#     template = loader.get_template("pages/poll_disp.html")
#     contents = {"post": post_, "options": options_, 'pid': pid}
#     return HttpResponse(template.render(contents, request))


def no_more_posts(request, category):
    template = loader.get_template("pages/poll_end.html")
    contents = {
        "post": None,
        "pid": "0",
        "change_url": True,
        "category": category,
    }
    return HttpResponse(template.render(contents, request))


def show_next_post_api_view(request, current_pid, category):
    if is_ajax(request):
        category_ = category
        if category == "all":
            category_ = None
        pid, truth = get_random_pid(current_pid=current_pid, category=category_)

        if truth:
            post_view_class = PostsView()
            if request.method == "GET":
                return post_view_class.get(
                    request=request, pid=pid, call="api", category=category
                )
            return post_view_class.post(
                request=request, pid=pid, call="api", category=category
            )

        else:
            ## need to implement an empty template to say you have reached the end! and pass a httpresponse/ template_response here
            # return HttpResponse("No more posts to display in the selected category")
            return no_more_posts(request, category)

    else:
        return HttpResponse("Thou Shall not Enter!!")


def show_categorybased_post_api_view(request, current_pid, category):
    if is_ajax(request):
        category_ = category
        if category == "all":
            category_ = None
        pid, truth = get_random_pid(current_pid=current_pid, category=category_)

        # print(pid)

        if truth:
            post_view_class = PostsView()
            if request.method == "GET":
                return post_view_class.get(
                    request=request, pid=pid, call="api", category=category
                )
            return post_view_class.post(
                request=request, pid=pid, call="api", category=category
            )

        else:
            ## need to implement an empty template to say you have reached the end! and pass a httpresponse/ template_response here
            # return HttpResponse("No more posts to display in the selected category")
            return no_more_posts(request, category)
    else:
        return HttpResponse("Thou Shall not Enter!!")


# def get_current_url_api_view(request):
#     if request.method == 'GET':
#         pid = current_pid
#         current_url = request.build_absolute_uri(reverse("posts:post_generation_page", kwargs={"pid": pid}))
#         return JsonResponse({'current_url': current_url})


class CurrentPostURL(APIView):
    # renderer_classes = [TemplateHTMLRenderer]
    # template_name = 'profile_list.html'

    renderer_classes = [JSONRenderer]
    # permission_classes = [permissions.IsAdminUser]

    def get(self, request, category, current_pid):
        if is_ajax(request):
            pid = current_pid
            current_url = request.build_absolute_uri(
                reverse(
                    "posts:post_generation_page",
                    kwargs={"category": category, "pid": pid},
                )
            )
            print("test", current_url)
            content = {"current_url": current_url}
            return Response(content)
        else:
            return HttpResponse("Thou Shall not Enter!!")


##to show comments
class CommentsView(View):
    def post(self, request, current_pid):
        if is_ajax(request):
            pid = current_pid
            post_ = Post_Model.objects.get(pk=pid)
            comments_form = CommentsForm(request.POST)
            if comments_form.is_valid():
                comments_ = comments_form.save(commit=False)
                comments_.question = post_
                comments_.commented_by = request.user
                comments_.option_voted = Options_Model.objects.filter(
                    question=post_, chosen_by=request.user
                ).first()
                comment_text = comments_form.cleaned_data["comment_text"]

                # Comment notification
                noti_post = Noti_Model.objects.filter(
                    recipient=post_.created_by,
                    sender=request.user,
                    post_at=post_,
                    noti_type="Comment",
                    is_read=False,
                ).first()

                if not noti_post:
                    noti_post = Noti_Model.objects.create(
                        recipient=post_.created_by,
                        sender=request.user,
                        content_text=comment_text,
                        post_at=post_,
                        noti_type="Comment",
                    )

                def check_mention_user_exist(match):
                    username = match.group(1)
                    try:
                        Custom_User.objects.get(username=username)
                        target = Custom_User.objects.get(username=username)

                        # Mention notification
                        noti_at = Noti_Model.objects.filter(
                            recipient=target,
                            sender=request.user,
                            post_at=post_,
                            noti_type="At",
                            is_read=False,
                        ).first()

                        if not noti_at:
                            noti_at = Noti_Model.objects.create(
                                recipient=target,
                                sender=request.user,
                                content_text=comment_text,
                                post_at=post_,
                                noti_type="At",
                            )

                        return f'<a href="{reverse("account:profile_page", args=[username])}"><strong>@{username}</strong></a>'
                    except Custom_User.DoesNotExist:
                        return f"@{username}"

                comment_text = re.sub(r"@(\w+)", check_mention_user_exist, comment_text)
                comment_text = comment_text.replace("\r\n", "<br>")
                comments_.comment_text = comment_text
                comments_.save()
                return JsonResponse({"commment": "success"})
        else:
            return HttpResponse("Thou Shall not Enter!!")

            # comment_text = request.POST["comment_text"].cleaned_data()

    ## Maybe sort and feed here
    def get(self, request, current_pid):
        if is_ajax(request):
            pid = current_pid
            # print('whyyyy:', pid)
            post_ = Post_Model.objects.get(pk=pid)
            comments_ = post_.comments_model_set.all().order_by("-commented_time")

            template = loader.get_template("pages/comments.html")
            contents = {
                "pid": pid,
                "comments": comments_,
                "show_comments_text": False,
            }
            if post_.viewed_by.filter(username=request.user.username).exists():
                contents["show_comments_text"] = True
            contents["post"] = post_
            return HttpResponse(template.render(contents, request))
        else:
            return HttpResponse("Thou Shall not Enter!!")


def report_comment(request, comment_id):
    if is_ajax(request):
        try:
            comment = Comments_Model.objects.get(id=comment_id)
            if request.user not in comment.reported_by.all():
                comment.reported_by.add(request.user)
                comment.reported_count += 1
                comment.save()
                return JsonResponse(
                    {"report": "success", "message": "Comment has been reported"}
                )
            else:
                comment.reported_by.remove(request.user)
                comment.reported_count -= 1
                comment.save()
                return JsonResponse(
                    {"report": "unreported", "message": "Report has been canceled"}
                )
        except Comments_Model.DoesNotExist:
            return JsonResponse({"report": "error"})
    return JsonResponse({"report": "not ajax"})


def report_post(request, post_id):
    if is_ajax(request):
        try:
            post = Post_Model.objects.get(id=post_id)
            print(post)
            if request.user not in post.reported_by.all():
                post.reported_by.add(request.user)
                post.reported_count += 1
                post.save()
                return JsonResponse(
                    {"report": "success", "message": "Poll has been reported"}
                )
            else:
                post.reported_by.remove(request.user)
                post.reported_count -= 1
                post.save()
                return JsonResponse(
                    {"report": "cancel", "message": "Report has been canceled"}
                )
        except Comments_Model.DoesNotExist:
            return JsonResponse({"report": "error"})
    return HttpResponse("Thou Shall not Enter!!")


def delete_comment(request, comment_id):
    if is_ajax(request):
        comment = Comments_Model.objects.get(id=comment_id)

        if comment.commented_by == request.user:
            comment.delete()
            return JsonResponse(
                {"delete": "success", "message": "Comment has been deleted"}
            )
        else:
            return JsonResponse({"delete": "fail", "message": "Something went wrong"})
    return HttpResponse("Thou Shall not Enter!!")


def upvote_comment(request, comment_id):
    if is_ajax(request):
        try:
            comment = Comments_Model.objects.get(id=comment_id)
            if (
                request.user not in comment.upvoted_by.all()
                and request.user not in comment.downvoted_by.all()
            ):
                comment.upvoted_by.add(request.user)
                comment.vote_count += 1
                comment.save()
                return JsonResponse({"upvote": "success"})
            elif (
                request.user in comment.upvoted_by.all()
                and request.user not in comment.downvoted_by.all()
            ):
                comment.upvoted_by.remove(request.user)
                comment.vote_count -= 1
                comment.save()
                return JsonResponse({"upvote": "success"})
            elif (
                request.user not in comment.upvoted_by.all()
                and request.user in comment.downvoted_by.all()
            ):
                comment.upvoted_by.add(request.user)
                comment.vote_count += 2
                comment.downvoted_by.remove(request.user)
                comment.save()
                return JsonResponse({"upvote": "change vote success"})
            else:
                return JsonResponse({"upvote": "already upvoted"})

        except Comments_Model.DoesNotExist:
            return JsonResponse({"upvote": "error"})

    else:
        return HttpResponse("Thou Shall not Enter!!")


def downvote_comment(request, comment_id):
    if is_ajax(request):
        try:
            comment = Comments_Model.objects.get(id=comment_id)
            if (
                request.user not in comment.downvoted_by.all()
                and request.user not in comment.upvoted_by.all()
            ):
                comment.downvoted_by.add(request.user)
                comment.vote_count -= 1
                comment.save()
                return JsonResponse({"downvote": "success"})
            elif (
                request.user in comment.downvoted_by.all()
                and request.user not in comment.upvoted_by.all()
            ):
                comment.downvoted_by.remove(request.user)
                comment.vote_count += 1
                comment.save()
                return JsonResponse({"downvote": "success"})
            elif (
                request.user not in comment.downvoted_by.all()
                and request.user in comment.upvoted_by.all()
            ):
                comment.downvoted_by.add(request.user)
                comment.vote_count -= 2
                comment.upvoted_by.remove(request.user)
                comment.save()
                return JsonResponse({"downvote": "change vote success"})
            else:
                return JsonResponse({"downvote": "already downvoted"})
        except Comments_Model.DoesNotExist:
            return JsonResponse({"downvote": "error"})

    else:
        return HttpResponse("Thou Shall not Enter!!")


def show_comments_text_api(request, current_pid):
    if is_ajax(request):
        if request.method == "GET":
            pid = current_pid
            post_ = Post_Model.objects.get(pk=pid)
            comments_form = CommentsForm()

            contents = {
                "pid": pid,
                "comments_form": comments_form,
                "show_comments_text": False,
            }
            if post_.viewed_by.filter(username=request.user.username).exists():
                contents["show_comments_text"] = True

            template = loader.get_template("pages/comments_text.html")
            return HttpResponse(template.render(contents, request))
    else:
        return HttpResponse("Thou Shall not Enter!!")


# @api_view(["GET"])
# def get_user_history(request):
#     if is_ajax(request):
#         return


# return JsonResponse({'current_url': current_url})


@login_required
def create_poll(request):
    # if request.user.is_authenticated:
    # print("create poll")
    categories = Post_Model.category_list
    if request.method == "POST":
        form = PollForm(request.POST)
        # print(request.POST)
        if form.is_valid():
            # print("form is valid")
            # print(form.cleaned_data)
            question_text = form.cleaned_data["prefix"]
            # print(question_text)
            if question_text == "own_ques":
                question_text = form.cleaned_data["question"]

            delay = int(form.cleaned_data["delay"])
            # print(delay)
            category = form.cleaned_data["category"]

            post = Post_Model.objects.create(
                question_text=question_text,
                created_by=request.user,
                category=category,
                created_time=datetime.now(),
                # created_time=timezone.now(),
            )

            color_list = ["AED9E0", "8CB369", "D7A5E4", "5D6DD3"]

            for i in range(1, 5):
                option_text = form.cleaned_data.get("choice{}".format(i))
                if option_text:
                    option = Options_Model.objects.create(
                        question=post, choice_text=option_text, color=color_list[i - 1]
                    )

            result_reveal_time = post.created_time + timedelta(hours=delay)
            print(
                post.created_time,
                datetime.now(),
                timezone.now(),
                result_reveal_time.replace(tzinfo=None),
            )
            post.result_reveal_time = result_reveal_time.replace(tzinfo=None)
            post.save()

            post_id = post.id
            messages.success(request, f"Post Created Successfully with ID => {post_id}")

            return redirect(reverse("posts:create_poll"))
        else:
            for err in list(form.errors.values()):
                messages.error(request, err)
            # print("form invalid")
            # print(form.errors)

    else:
        # print("GET request")
        form = PollForm()

    context = {"form": form, "categories": categories}
    return render(request, "pages/poll_create.html", context)


# return HttpResponse("Thou Shall not Enter!!")


def get_back_api_view(request, category, pid):
    if is_ajax(request):
        post_view_class = PostsView()
        return post_view_class.get(
            request=request, call="api", pid=pid, change_url=False, category=category
        )

    else:
        return HttpResponse("Thou Shall not Enter!!")
