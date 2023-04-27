from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse

from .forms import LoginForm
from .forms import RegisterForm
from .forms import PasswordResetForm
from .forms import PasswordChangeForm, ProfilePicForm
from .forms import PasswordResetConfirmationForm
from .tokens import account_activation_token, password_reset_token
from .models import Custom_User
from chat.models import Connection_Model

# from chat.views import get_friends_info
from posts.models import Post_Model, Options_Model, Noti_Model


from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view


from django.contrib.auth.decorators import login_required


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


# Create your views here.

# put token generator in a single function and call it function


# to reset password after clickin on link in eamil
def password_reset_view(request, uid, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user_ = Custom_User.objects.get(pk=uid)
    except:
        user_ = None

    if user_ != None and password_reset_token.check_token(user_, token):
        password_reset_form = PasswordResetForm()
        if request.method == "POST":
            password_reset_form = PasswordResetForm(request.POST)

            if password_reset_form.is_valid():
                if (
                    make_password(password_reset_form.cleaned_data["password1"])
                    == user_.password
                ):
                    messages.error(
                        request, "New Password cannot be the same as old one!"
                    )
                    contents = {"form": password_reset_form}
                    return render(request, "pages/password_reset.html", contents)

                user_.set_password(password_reset_form.cleaned_data["password1"])
                user_.save()

                messages.success(request, f"Password Reset! Login to proceed")
                return redirect(reverse("account:login_page"))
            else:
                for err in list(password_reset_form.errors.values()):
                    messages.error(request, err)
                password_reset_form = PasswordResetForm(request.POST)

        contents = {"form": password_reset_form}
        return render(request, "pages/password_reset.html", contents)

    messages.error(request, f"Invalid Link!!")
    return redirect(reverse("account:login_page"))


# fucntion to send eamil for account verf and reset password
def email_token(request, user_, email_subject, text_, token_, reverse_link):
    uid = (urlsafe_base64_encode(force_bytes(user_.pk)),)
    token = token_.make_token(user_)
    password_reset_link = request.build_absolute_uri(
        reverse(reverse_link, kwargs={"uid": uid[0], "token": token})
    )

    email_msg = f"Hello {user_.username},\n\nPlease click the following link to {text_}:\n{password_reset_link}"

    try:
        send_mail(
            subject=email_subject,
            message=email_msg,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_.email],
        )
    except:
        return 0

    return 1


# to send password link in mail
def password_reset_confirmation_view(request):
    password_reset_form = PasswordResetConfirmationForm()
    if request.method == "POST":
        username_email = request.POST["username_or_email"]
        try:
            user_ = Custom_User.objects.get(username=username_email)
        except:
            try:
                user_ = Custom_User.objects.get(email=username_email)
            except:
                messages.error(request, f"Username or Email doesn't exist!")
                contents = {"form": password_reset_form}
                return render(
                    request, "pages/password_reset_confirmation.html", contents
                )

        # send token mail
        email_subject = "Password Reset"
        text_ = "reset your password"
        token_ = password_reset_token
        reverse_link = "account:passwordreset_page"

        if email_token(request, user_, email_subject, text_, token_, reverse_link):
            messages.success(
                request, "Password Reset Link sent via email. Reset Password to Login"
            )
            # return maybe redirect to home? or login?

        else:
            messages.error(request, "Error sending email!")
            password_reset_form = PasswordResetConfirmationForm(request.POST)

    contents = {"form": password_reset_form}
    return render(request, "pages/password_reset_confirmation.html", contents)


# To authenticate user and email and is_activate = True
def activate_view(request, uid, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user_ = Custom_User.objects.get(pk=uid)
    except:
        user_ = None

    if user_ != None and account_activation_token.check_token(user_, token):
        user_.is_active = True
        user_.save()
        messages.success(request, f"Email Verified! Login to proceed")
        return redirect(reverse("account:login_page"))

    messages.error(request, f"Invalid Link!!")
    return redirect(reverse("account:login_page"))


# log out a logged in user
def logout_view(request):
    logout(request)
    return redirect(reverse("posts:home_page"))


# comprises of both login_view and register_view
def access_view(request):
    login_form = LoginForm()
    register_form = RegisterForm()

    # print(request.POST.get('next'))
    # print("kk:", request.GET.get('next'))

    access_info_d = {"Sign In": login_view, "Sign Up": register_view}

    if request.method == "POST":
        return access_info_d[request.POST["access_info"]](
            request, login_form, register_form
        )

    contents = {"login_form": login_form, "register_form": register_form, "class_": ""}
    return render(request, "pages/login.html", contents)


# log in a user
def login_view(request, login_form, register_form):
    login_form = AuthenticationForm(request, data=request.POST)
    if login_form.is_valid():
        username = login_form.cleaned_data["username"]
        password = login_form.cleaned_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            print("here:", reverse("posts:home_page"))
            # print(request.POST.get("next"))
            # try:
            #     redirect_url = request.GET.get('next')
            #     return redirect(request.build_absolute_uri(redirect_url))
            # except:
            return redirect(reverse("posts:home_page"))
    else:
        messages.error(request, f"Username or password is wrong.")

    contents = {"login_form": login_form, "register_form": register_form, "class_": ""}
    return render(request, "pages/login.html", contents)


# register a user
def register_view(request, login_form, register_form):
    register_form = RegisterForm(request.POST)
    if register_form.is_valid():
        user_ = register_form.save(commit=False)
        user_.is_active = False
        user_.save()

        # send email token
        email_subject = "Verification"
        text_ = "activate your account"
        token_ = account_activation_token
        reverse_link = "account:activate_page"

        if email_token(request, user_, email_subject, text_, token_, reverse_link):
            messages.success(request, "Registration successful, verify email to login.")
            return redirect(reverse("account:login_page"))
        else:
            messages.error(request, "Email verification failed!")
    else:
        for err in list(register_form.errors.values()):
            messages.error(request, err)

    contents = {
        "login_form": login_form,
        "register_form": register_form,
        "class_": "right-panel-active",
    }
    return render(request, "pages/login.html", contents)


def profile_picture_change(request, contents):
    profile_picture_change_form = ProfilePicForm(request.POST, request.FILES)

    if not request.FILES.get("profile_picture"):
        messages.error(request, "No Image Chosen!")
        return render(request, "pages/profile.html", contents)

    if profile_picture_change_form.is_valid():
        request.user.profile_picture = request.FILES.get("profile_picture")
        request.user.save()

        messages.success(request, "Profile Picture Changed Successfully!")

        contents["profile"] = request.user

    else:
        for err in list(profile_picture_change_form.errors.values()):
            messages.error(request, err)

    return render(request, "pages/profile.html", contents)


def password_change(request, contents):
    password_change_form = PasswordChangeForm(request.POST)

    if password_change_form.is_valid():
        old_password = password_change_form.cleaned_data["old_password"]

        if authenticate(request, username=request.user.username, password=old_password):
            if old_password == password_change_form.cleaned_data["password1"]:
                messages.error(request, "New Password cannot be the same as old one!")
                contents["class_"] = "right-panel-active"
                return render(request, "pages/profile.html", contents)

            request.user.set_password(password_change_form.cleaned_data["password1"])
            request.user.save()
            messages.success(request, "Password Changed Successfully!")
            login(request, request.user)
            # contents = {"password_change_form": password_change_form, "class_": ""}
            # contents['username'] = request.user.username
            # contents['email'] = request.user.email
            # contents['edit_access'] = True
            return render(request, "pages/profile.html", contents)
        else:
            messages.error(request, f"Current Password is wrong")
            contents["class_"] = "right-panel-active"
    else:
        for err in list(password_change_form.errors.values()):
            messages.error(request, err)
        contents["class_"] = "right-panel-active"

    return render(request, "pages/profile.html", contents)


def profile_page_contents(request, username_):
    password_change_form = PasswordChangeForm()
    profile_picture_change_form = ProfilePicForm()
    contents = {
        "password_change_form": password_change_form,
        "profile_picture_change_form": profile_picture_change_form,
        "class_": "",
    }

    if request.user.username == username_:
        # my_user_details = Custom_User.objects.get(username = request.user.username)
        # contents['username'] = request.user.username
        # contents['email'] = request.user.email
        contents["profile"] = request.user
        contents["edit_access"] = True
    else:
        requested_user_details = Custom_User.objects.get(username=username_)
        # contents['username'] = requested_user_details.username
        # contents['email'] = requested_user_details.email
        contents["profile"] = requested_user_details
        contents["edit_access"] = False

    profile = Custom_User.objects.get(username=username_)

    # Check if the request already exists
    request_exists = (
        Connection_Model.objects.filter(
            from_user=request.user, to_user=profile, connection_status="Pending"
        ).exists()
        or Connection_Model.objects.filter(
            from_user=profile, to_user=request.user, connection_status="Pending"
        ).exists()
    )

    coming_request_exists = Connection_Model.objects.filter(
        from_user=profile, to_user=request.user, connection_status="Pending"
    ).exists()

    contents["coming_request_exists"] = coming_request_exists

    if coming_request_exists:
        coming_request = Connection_Model.objects.get(
            from_user=profile, to_user=request.user, connection_status="Pending"
        )

        print(coming_request)

        contents["coming_request"] = coming_request

    block_connection_exists = (
        Connection_Model.objects.filter(
            from_user=profile, to_user=request.user, connection_status="Blocked"
        ).exists()
        or Connection_Model.objects.filter(
            from_user=request.user, to_user=profile, connection_status="Blocked"
        ).exists()
    )

    contents["block_connection_exists"] = block_connection_exists
    contents["view_access"] = True

    if block_connection_exists:
        block_connection = (
            Connection_Model.objects.filter(
                from_user=profile, to_user=request.user, connection_status="Blocked"
            ).first()
            or Connection_Model.objects.filter(
                from_user=request.user, to_user=profile, connection_status="Blocked"
            ).first()
        )

        ##admin can view blocked user profiles
        if block_connection.blocked_by == request.user or request.user.is_superuser:
            contents["view_access"] = True
        else:
            # TODO:fix later
            contents["view_access"] = False

    # Get friends list
    # user_ = Custom_User.objects.get(username=username_)
    # friends = get_user_friends_list(user_).order_by("-connection_answer_time")
    # friends_list = [friend.get_friend(user_) for friend in friends]
    friend_exists = (
        Connection_Model.objects.filter(
            from_user=request.user, to_user=profile, connection_status="Accepted"
        ).exists()
        or Connection_Model.objects.filter(
            from_user=request.user, to_user=profile, connection_status="Blocked"
        ).exists()
        ##declined can request again
        # or Connection_Model.objects.filter(
        #     from_user=request.user, to_user=profile, connection_status="Declined"
        # ).exists()
        or Connection_Model.objects.filter(
            from_user=profile, to_user=request.user, connection_status="Accepted"
        ).exists()
        or Connection_Model.objects.filter(
            from_user=profile, to_user=request.user, connection_status="Blocked"
        ).exists()
        ##declined can request again
        # or Connection_Model.objects.filter(
        #     from_user=profile, to_user=request.user, connection_status="Declined"
        # ).exists()
    )

    contents["request_exists"] = request_exists
    contents["friend_exists"] = friend_exists

    # context = {
    #     # 'profile': profile,
    #     'request_exists': request_exists,
    #     'friends_list': friends_list
    # }

    return contents


@login_required
def profile_view(request, username_):
    contents = profile_page_contents(request, username_)

    print(request.user.profile_picture.url)
    if request.user.username == username_ and request.method == "POST":
        func_map = {
            "profile_pic": profile_picture_change,
            "pass_change": password_change,
        }
        return func_map[request.POST["account_info"]](request, contents)

    contents["tab_to_click"] = "nav-profile-tab"

    return render(request, "pages/profile.html", contents)


## Change all classes to smthng like this and pass a parameter and render post_home.html and check in html to render the right page
class UserHistory(APIView):
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, username_):
        if is_ajax(request):
            print("ajax request")

            user_ = Custom_User.objects.get(username=username_)

            content = user_.posts_view_time.all().order_by("-view_time")

            history_results = [
                {
                    "id": post.id,
                    "question_text": post.question_text,
                    "category": post.category,
                    "options": [
                        {"choice_text": option.choice_text}
                        for option in Options_Model.objects.filter(question=post)
                    ],
                }
                for con in content
                for post in [con.post]
            ]

            return Response(
                {"posts": history_results}, template_name="pages/profile_history.html"
            )

        else:
            contents = profile_page_contents(request, username_)

            contents["tab_to_click"] = "nav-history-tab"
            return Response(contents, template_name="pages/profile.html")


class UserPostsCreated(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    # permission_classes = [permissions.IsAdminUser]

    def get(self, request, username_):
        if is_ajax(request):
            # print("ajax request")
            user_ = Custom_User.objects.get(username=username_)
            content = user_.posts_created.all().order_by(
                "-created_time"
            )  # .order_by('-view_time') order by relation field here

            created_results = []

            for post in content:
                options = []

                for option in Options_Model.objects.filter(question=post):
                    options.append(
                        {
                            "choice_text": option.choice_text,
                        }
                    )

                created_results.append(
                    {
                        "id": post.id,
                        "question_text": post.question_text,
                        "category": post.category,
                        "options": options,
                    }
                )

            return Response(
                {"posts": created_results},
                template_name="pages/profile_posts_created.html",
            )

        else:
            ## render entire profile page with active nav id
            # print("url request")
            contents = profile_page_contents(request, username_)

            contents["tab_to_click"] = "nav-postscreated-tab"
            return Response(contents, template_name="pages/profile.html")


class CurrentProfileURL(APIView):
    renderer_classes = [JSONRenderer]
    # permission_classes = [permissions.IsAdminUser]

    def get(self, request, page, username):
        url_page_map = {
            "history": "account:profile_history_page",
            "posts_created": "account:profile_postscreated_page",
            "profile": "account:profile_page",
            "friends": "account:profile_friends_page",
            "friend_requests": "account:friend_requests",
        }
        current_url = request.build_absolute_uri(
            reverse(url_page_map[page], kwargs={"username_": username})
        )
        content = {"current_url": current_url}
        # print(content)
        return Response(content)


class UserFriends(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    # permission_classes = [permissions.IsAdminUser]

    def get(self, request, username_):
        if is_ajax(request):
            user_ = Custom_User.objects.get(username=username_)
            friends = get_user_friends_list(user_).order_by("-connection_answer_time")
            # print(get_user_friends_list(user_), friends)
            friends_data = []
            friends_set = set()

            # friends = [friend.get_friend(user_) for friend in friends]

            for connection in friends:
                friend = connection.get_friend(user_)
                connection_status = connection.connection_status
                blocked_by = connection.blocked_by
                # prevent showing duplicate friends in friends list

                # if friend not in friends_set:
                #     friends_set.add(friend)
                friends_data.append(
                    {
                        "friend": friend,
                        "connection_id": connection.id,
                        "connection_status": connection_status,
                        "blocked_by": blocked_by,
                    }
                )

            if request.user == user_:
                block_access = True
            else:
                block_access = False

            return Response(
                # {"friends": friends}, template_name="pages/profile_friends.html"
                {"friends_data": friends_data, "block_access": block_access},
                template_name="pages/profile_friends.html",
            )

        else:
            contents = profile_page_contents(request, username_)

            contents["tab_to_click"] = "nav-friends-tab"
            return Response(contents, template_name="pages/profile.html")


def get_user_friends_list(user):
    connections_sent = user.connection_requests_sent.filter(
        connection_status="Accepted"
    )
    connections_recieved = user.connection_requests_received.filter(
        connection_status="Accepted"
    )

    connections_sent_blocked = user.connection_requests_sent.filter(
        connection_status="Blocked"
    )

    connections_recieved_blocked = user.connection_requests_received.filter(
        connection_status="Blocked"
    )

    friends = (
        connections_sent
        | connections_recieved
        | connections_sent_blocked
        | connections_recieved_blocked
    )

    # returns all connection models that has from_user = user or to_user=user
    return friends


# def block_friend(request, uid):
#     if request.user.is_authenticated:
#         friend = Custom_User.objects.get(id=uid)
#         connection = Connection_Model.objects.filter(from_user=request.user, to_user=friend).first()
#         if connection:
#             connection.status = 'declined'
#             connection.save()
#             return JsonResponse({'status': 'success'}, status=200)
#         else:
#             return JsonResponse({'status': 'error', 'message': 'Friend not found.'}, status=404)
#     return JsonResponse({'status': 'error', 'message': 'User not authenticated.'}, status=401)


@login_required
def block_friend(request, connection_id):
    if is_ajax(request):
        try:
            # friend = Custom_User.objects.get(id=uid)
            connection = Connection_Model.objects.get(id=connection_id)
            if (
                connection.to_user == request.user
                or connection.from_user == request.user
            ) and connection.connection_status == "Accepted":
                connection.connection_status = "Blocked"
                connection.blocked_by = request.user
                connection.save()

                # also change the connection status of opposite connection if exists
                # (from_user=to_user, to_user=from_user)
                # if request.user == connection.to_user:
                #     opposite_request = Connection_Model.objects.get(
                #         from_user=request.user,
                #         to_user=connection.from_user,
                #          connection_status="Accepted",
                #     )
                #     if opposite_request:
                #         opposite_request.connection_status = "Blocked"
                #         opposite_request.save()

                # if request.user == connection.from_user:
                #     opposite_request = Connection_Model.objects.get(
                #         from_user=connection.to_user,
                #         to_user=request.user,
                #         connection_status="Accepted",
                #     )
                #     if opposite_request:
                #         opposite_request.connection_status = "Blocked"
                #         opposite_request.save()

                return JsonResponse(
                    {"status": "success", "message": "The user has been blocked"}
                )
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "You don't have permission to block this user.",
                    }
                )
        except Connection_Model.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Friend request not found."}
            )
    return JsonResponse({"status": "error", "message": "Not an AJAX request."})


@login_required
def unblock_friend(request, connection_id):
    if is_ajax(request):
        try:
            # friend = Custom_User.objects.get(id=uid)
            connection = Connection_Model.objects.get(id=connection_id)
            if (
                connection.to_user == request.user
                or connection.from_user == request.user
            ) and connection.connection_status == "Blocked":
                connection.connection_status = "Accepted"
                connection.blocked_by = None
                connection.save()

                # also change the connection status of opposite connection if exists
                # (from_user=to_user, to_user=from_user)
                # if request.user == connection.to_user:
                #     opposite_request = Connection_Model.objects.get(
                #         from_user=request.user,
                #         to_user=connection.from_user,
                #         connection_status="Blocked",
                #     )
                #     if opposite_request:
                #         opposite_request.connection_status = "Accepted"
                #         opposite_request.save()

                # if request.user == connection.from_user:
                #     opposite_request = Connection_Model.objects.get(
                #         from_user=connection.to_user,
                #         to_user=request.user,
                #         connection_status="Blocked",
                #     )
                #     if opposite_request:
                #         opposite_request.connection_status = "Accepted"
                #         opposite_request.save()

                return JsonResponse(
                    {"status": "success", "message": "The user has been unblocked"}
                )
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "You don't have permission to unblock this user.",
                    }
                )
        except Connection_Model.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Friend request not found."}
            )
    return JsonResponse({"status": "error", "message": "Not an AJAX request."})


@login_required
def send_friend_request(request, uid):
    if is_ajax(request):
        try:
            from_user = request.user
            to_user = Custom_User.objects.get(id=uid)

            if not Connection_Model.connection_exists(
                Connection_Model, from_user, to_user
            ):
                friend_request = Connection_Model.objects.create(
                    from_user=from_user, to_user=to_user
                )
                return JsonResponse(
                    {"status": f"Friend request sent to {to_user.username}!"}
                )

            else:
                friend_request = (
                    Connection_Model.objects.filter(
                        from_user=from_user, to_user=to_user
                    ).first()
                    or Connection_Model.objects.filter(
                        from_user=to_user, to_user=from_user
                    ).first()
                )

                if friend_request.connection_status == "Declined":
                    friend_request.connection_status = "Pending"
                    friend_request.save()
                    return JsonResponse(
                        {"status": f"Friend request sent to {to_user.username}!"}
                    )
                else:
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "You have already sent a friend request to {to_user.username}.",
                        }
                    )
        except Connection_Model.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Friend request not found."}
            )
    return JsonResponse({"status": "error", "message": "Not an AJAX request."})


# @login_required
# def accept_friend_request_profilepage(request, uid):
#     if is_ajax(request):
#         try:
#             friend_request = Connection_Model.objects.get(id=uid)
#             if friend_request.to_user == request.user:
#                 friend_request.connection_status = "Accepted"
#                 friend_request.save()

#                 return JsonResponse({"status": "success"})
#             else:
#                 return JsonResponse(
#                     {
#                         "status": "error",
#                         "message": "You don't have permission to accept this friend request.",
#                     }
#                 )
#         except Connection_Model.DoesNotExist:
#             return JsonResponse(
#                 {"status": "error", "message": "Friend request not found."}
#             )
#     return JsonResponse({"status": "error", "message": "Not an AJAX request."})


# @login_required
# def decline_friend_request_profilepage(request, uid):
#     if is_ajax(request):
#         try:
#             friend_request = Connection_Model.objects.get(id=uid)
#             if friend_request.to_user == request.user:
#                 friend_request.connection_status = "Declined"
#                 friend_request.save()

#                 return JsonResponse({"status": "success"})
#             else:
#                 return JsonResponse(
#                     {
#                         "status": "error",
#                         "message": "You don't have permission to decline this friend request.",
#                     }
#                 )
#         except Connection_Model.DoesNotExist:
#             return JsonResponse(
#                 {"status": "error", "message": "Friend request not found."}
#             )
#     return JsonResponse({"status": "error", "message": "Not an AJAX request."})


@login_required
def friend_requests(request, username_):
    user = Custom_User.objects.get(username=username_)
    pending_requests = Connection_Model.objects.filter(
        to_user=user, connection_status="Pending"
    )
    context = {"pending_requests": pending_requests}
    return render(request, "pages/friend_request.html", context)


@login_required
def accept_friend_request(request, uid):
    if is_ajax(request):
        try:
            friend_request = Connection_Model.objects.get(id=uid)
            if friend_request.to_user == request.user:
                friend_request.connection_status = "Accepted"
                friend_request.save()

                # also change the connection status of opposite connection if exists
                # (from_user=to_user, to_user=from_user)
                # sender = friend_request.from_user
                # opposite_request = Connection_Model.objects.get(
                #     from_user=request.user, to_user=sender, connection_status="Pending"
                # )
                # if opposite_request:
                #     opposite_request.connection_status = "Accepted"
                #     opposite_request.save()

                return JsonResponse({"status": "success"})
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "You don't have permission to accept this friend request.",
                    }
                )
        except Connection_Model.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Friend request not found."}
            )
    return JsonResponse({"status": "error", "message": "Not an AJAX request."})


@login_required
def decline_friend_request(request, uid):
    if is_ajax(request):
        try:
            friend_request = Connection_Model.objects.get(id=uid)
            if friend_request.to_user == request.user:
                friend_request.connection_status = "Declined"
                friend_request.save()
                # friend_request.delete()

                # also change the connection status of opposite connection if exists
                # (from_user=to_user, to_user=from_user)
                # sender = friend_request.from_user
                # opposite_request = Connection_Model.objects.get(
                #     from_user=request.user, to_user=sender, connection_status="Pending"
                # )
                # if opposite_request:
                #     opposite_request.connection_status = "Declined"
                #     opposite_request.save()

                return JsonResponse({"status": "success"})
            else:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "You don't have permission to decline this friend request.",
                    }
                )
        except Connection_Model.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Friend request not found."}
            )
    return JsonResponse({"status": "error", "message": "Not an AJAX request."})


@login_required
def notification_page(request):
    # Retrieve all notifications for the current user
    notifications = Noti_Model.objects.filter(recipient=request.user)

    notifications_results = []

    for notification in notifications:
        post = notification.post_at
        options = []

        for option in Options_Model.objects.filter(question=post):
            options.append(
                {
                    "choice_text": option.choice_text,
                }
            )

        notifications_results.append(
            {
                "post_id": post.id,
                "notification": notification,
                "question_text": post.question_text,
                "category": post.category,
                "options": options,
            }
        )

    # Mark all unread notifications as read
    for notification in notifications.filter(is_read=False):
        notification.is_read = True
        notification.save()

    context = {
        "notifications": notifications_results,
    }

    return render(request, "pages/notification_page.html", context)


# def backactivetab_view(request, username, tab):
#     # implement map for each tab to corresponding func
#     tab_map = {"history": UserHistory(), "postscreated": None}
#     return
