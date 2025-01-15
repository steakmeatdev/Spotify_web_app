from django.shortcuts import render
from rest_framework import generics, status
from .models import Room
from .serializers import RoomSerializer, CreateRoomSerializer
from rest_framework.views import APIView
from rest_framework.response import Response


# Set up a generic view with generics.ListAPIView to display all the Room objects
class RoomView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class GetRoom(APIView):
    serializer_class = RoomSerializer
    lookup_url_kwarg = "code"

    def get(self, request, format=None):
        code = request.GET.get(self.lookup_url_kwarg)

        if code != None:
            room = Room.objects.filter(code = code)
            if len(room) > 0:
                data = RoomSerializer(room[0]).data

                data["is_host"] = self.request.session.session_key == room[0].host
                # Returning the room instance
                return Response(data, status=status.HTTP_200_OK)
            
            return Response({"Room Not Found":"Invalid Room Code"})
        return({"Bad request":"Code parameter not found"})

class CreateRoomView(APIView):
    serializer_class = CreateRoomSerializer

    def post(self, request):
        # Check active session
        if not self.request.session.session_key:
            self.request.session.create()

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            guest_can_pause = serializer.validated_data.get("guest_can_pause")
            votes_to_skip = serializer.validated_data.get("votes_to_skip")
            host = self.request.session.session_key

            queryset = Room.objects.filter(host=host)
            if queryset.exists():
                room = queryset[0]
                room.guest_can_pause = guest_can_pause
                room.votes_to_skip = votes_to_skip
                room.save(update_fields=["guest_can_pause", "votes_to_skip"])
                self.request.session["room_code"] = room.code
                return Response(RoomSerializer(room).data)
            else:
                room = Room(host=host, guest_can_pause=guest_can_pause, votes_to_skip=votes_to_skip)
                room.save()
                self.request.session["room_code"] = room.code
                return Response(RoomSerializer(room).data)
            
            return Response(CreateRoomSerializer(room).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class JoinRoom(APIView):
    # Joining with code currently at the URL
    lookup_url_kwarg = "code"

    def post(self, request, format=None):
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        
        code = request.data.get(self.lookup_url_kwarg)

        if code != None:
            room_result = Room.objects.filter(code = code)
            if len(room_result) > 0:
                room = room_result[0]

                # Storing the user session information in this object
                self.request.session["room_code"] = code

                return Response({"message":"Room joined"}, status=status.HTTP_200_OK)
            
            return Response({"Bad request":"Invalid Room Code"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"Bad request":"post data"}, status=status.HTTP_400_BAD_REQUEST)
