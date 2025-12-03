# queue/serializers.py
from rest_framework import serializers
from core.models import Token           # <-- core.Token is where your Token model lives
# If your Token model is in another app (e.g. token_queue.models) change import accordingly:
# from token_queue.models import Token

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        # include fields you want exposed; '__all__' is simplest for now
        fields = "__all__"
        # make some fields read-only if appropriate
        read_only_fields = ("number", "created_at", "updated_at")
