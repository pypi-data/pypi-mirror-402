from rest_framework.mixins import ListModelMixin
from saas_base.drf.views import TenantEndpoint

from ..models import Reaction
from ..serializers import ReactionSerializer


class ReactionListEndpoint(ListModelMixin, TenantEndpoint):
    serializer_class = ReactionSerializer
    queryset = Reaction.objects.select_related('thread').all()
    required_permission = 'content.comment.view'

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
