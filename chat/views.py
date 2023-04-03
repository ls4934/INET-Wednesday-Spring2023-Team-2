from django.shortcuts import render
from django.http import HttpResponse
from .models import Chat_History, Connection_Model


# to check if request is form ajax
def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


# Create your views here.
def chat_view(request):
    return render(request, "pages/chat.html")



##todo: similiar function to get friends list for each user show up in profile page
def get_friends_info(request):
    connections_sent = request.user.connection_requests_sent.filter(connection_status='Accepted')
    connections_recieved = request.user.connection_requsts_received.filter(connection_status='Accepted')
    
    friends = connections_sent | connections_recieved

    # returns all connection models that has from_user = user or to_user=user
    return friends
    ## use this code to display user's friends list:
    # friends = get_friends_info(request)
    #  for i in friends:
    #      print(i.get_friend(request.user), i.id)




def get_chat_history(connection_id):
    chat_history = Chat_History.objects.get(
        connection=Connection_Model.objects.get(id=connection_id)
    )
    history_list = chat_history.history.order_by(
        "-timestamp"
    ).all()  # [:100] ##todo: return top 100msg everytime to reduce query time
    return history_list[::-1]


# delete later
def chat_view_test(request, connection_id):
    # if connection doesn't exists (i.e. users don't know each other) or
    # if connection is not in accepted status (i.e. users agreed to chat with each other) or
    # if request isnot from ajax (url request not accepted)

    if (
        Connection_Model.objects.filter(id=connection_id).exists()
        and Connection_Model.objects.get(id=connection_id).connection_status
        == "Accepted"
    ):  # and is_ajax(request):
        messages = get_chat_history(connection_id)        
        
        
        return render(
            request,
            "pages/chat_test.html",
            {"connection_id": connection_id, "messages": messages},
        )

    else:
        return HttpResponse("Thou Shall not Enter!!")
