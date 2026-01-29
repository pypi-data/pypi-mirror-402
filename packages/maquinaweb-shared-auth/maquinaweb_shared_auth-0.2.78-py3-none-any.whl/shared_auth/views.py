from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shared_auth.mixins import LoggedOrganizationPermMixin, RequirePermissionMixin
from shared_auth.utils import get_member_model, get_user_model

from .middleware import get_member
from .serializers import OrganizationSerializer, UserSerializer


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para organizações do usuário + action `me` para retornar
    a organização atual via header.
    """

    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        organizations = self.request.user.organizations
        return organizations

    @action(detail=False, methods=["get"])
    def me(self, request):
        org = request.user.get_org(request.organization_id)
        if not org:
            return Response(
                {"detail": "Organization not specified or not found."}, status=400
            )

        if not get_member(request.user.id, org.pk):
            return Response(
                {"detail": "Você não pertence a essa organização."}, status=403
            )
        serializer = self.get_serializer(org)
        return Response(serializer.data)


class UserViewSet(
    RequirePermissionMixin, LoggedOrganizationPermMixin, viewsets.ReadOnlyModelViewSet
):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        members = (
            get_member_model()
            .objects.filter(organization_id=self.request.organization_id)
            .values_list("user_id", flat=True)
        )
        return get_user_model().objects.filter(id__in=members)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="list")
    def list_all(self, request):
        users = self.get_queryset()
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
