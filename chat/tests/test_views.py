from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from chat.models import Group_Connection
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.files.uploadedfile import SimpleUploadedFile
import json

from login.models import Custom_User
from chat.views import (
    get_chat_history,
    get_num_new_messages,
    latest_message_formatting,
)
from chat.models import (
    Connection_Model,
    Chat_Message,
    Chat_History,
)


class TestChatViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Custom_User.objects.create_user(
            username="test", email="test@testemail.com", password="test1234"
        )
        self.chat_url = reverse("connections:chat_page")
        self.login_url = reverse("account:login_page")
        # user will be friends with user1 and not friends with user2
        self.user1 = Custom_User.objects.create_user(
            username="friend1", email="friend1@testemail.com", password="test1234"
        )
        self.connection = Connection_Model.objects.create(
            from_user=self.user1, to_user=self.user, connection_status="Accepted"
        )

        self.user2 = Custom_User.objects.create_user(
            username="nfriend", email="nfriend@testemail.com", password="test1234"
        )

    def test_friend_connection(self):
        self.client.login(username="test", password="test1234")
        self.assertTrue(
            Connection_Model.connection_exists(Connection_Model, self.user1, self.user)
        )
        self.assertTrue(
            Connection_Model.connection_exists(Connection_Model, self.user, self.user1)
        )
        self.assertFalse(
            Connection_Model.connection_exists(Connection_Model, self.user, self.user2)
        )

    ##TODO: fix
    # def test_chat_page_friendslist(self):
    #     self.client.login(username="test", password="test1234")
    #     response = self.client.get(self.chat_url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "pages/chat.html")

    #     friends = response.context["friends"]
    #     friend_objects = [friend.get_friend(self.user) for friend in friends]

    #     self.assertIn(self.user1, friend_objects)
    #     self.assertNotIn(self.user2, friend_objects)

    def test_chat_page_chathistory_view_valid(self):
        self.client.login(username="test", password="test1234")
        response = self.client.get(
            reverse("connections:get_chat_history_box", args=[self.connection.id]),
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/chat_box.html")
        self.assertContains(response, self.user1.username)

        messages = get_chat_history(self.connection.id)
        for message in messages:
            self.assertContains(response, message.message)

    def test_chat_page_chathistory_view_invalid(self):
        self.client.login(username="test", password="test1234")
        response = self.client.get(
            reverse("connections:get_chat_history_box", args=[99999])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thou Shall not Enter!!")

    def test_get_num_new_messages(self):
        self.client.login(username="test", password="test1234")

        chat_history = Chat_History.objects.create(connection=self.connection)

        self.chat_message1 = Chat_Message.objects.create(
            user=self.user, message="Hello"
        )
        self.chat_message2 = Chat_Message.objects.create(user=self.user1, message="Hi")
        chat_history.history.add(self.chat_message1)
        chat_history.history.add(self.chat_message2)

        factory = RequestFactory()
        request = factory.get("/")
        request.user = self.user
        num_new_messages = get_num_new_messages(request)
        self.assertEqual(num_new_messages, 1)

    def test_latest_message_formatting(self):
        # Test message less than 20 characters
        message = "Hello world"
        formatted_message = latest_message_formatting(message)
        self.assertEqual(formatted_message, message)

        # Test message more than 20 characters
        message = "This is a long message that needs to be formatted"
        expected_message = "This is a long messa..."
        formatted_message = latest_message_formatting(message)
        self.assertEqual(formatted_message, expected_message)

    def test_search_friends(self):
        user1 = Custom_User.objects.create(
            username="user1", email="user1@test.com", password="testpassword"
        )
        user2 = Custom_User.objects.create(
            username="user2", email="user2@test.com", password="testpassword"
        )
        user3 = Custom_User.objects.create(
            username="user3", email="user3@test.com", password="testpassword"
        )
        group1 = Group_Connection.objects.create(
            group_created_by=user1, group_name="Group 1"
        )
        group1.members.add(user2)
        group1.members.add(user3)
        connect2 = Connection_Model.objects.create(
            from_user=user2, to_user=user1, connection_status="Accepted"
        )
        group1_connection = Connection_Model.objects.create(
            group=group1, connection_status="Accepted"
        )
        self.client.force_login(user1)
        url = reverse("connections:search_friends")
        response = self.client.get(url + "?search=user2")
        expected_response = JsonResponse(
            {
                "search_results": [
                    {
                        "id": user2.id,
                        "username": user2.username,
                        "connection_id": connect2.id,
                        "type": "user",
                    }
                ]
            }
        )
        self.assertEqual(response.content.decode(), expected_response.content.decode())
