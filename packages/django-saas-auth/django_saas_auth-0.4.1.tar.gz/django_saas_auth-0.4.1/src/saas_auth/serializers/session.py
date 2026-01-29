from rest_framework import serializers

from saas_auth.models import Session


class SessionSerializer(serializers.ModelSerializer):
    current_session = serializers.SerializerMethodField()

    class Meta:
        model = Session
        exclude = ('user', 'session_key')

    def get_current_session(self, obj):
        request = self.context['request']
        return request.session.session_key == obj.session_key
