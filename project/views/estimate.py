from rest_framework import status
from rest_framework.response import Response

from common.permissions import ProjectEntityPermission
from common.views import BaseAPIView, BaseViewSet
from project.models import Estimate, EstimatePoint, Project
from project.serializers import (
    EstimatePointSerializer,
    EstimateReadSerializer,
    EstimateSerializer,
)


class ProjectEstimatePointEndpoint(BaseAPIView):
    permission_classes = [
        ProjectEntityPermission,
    ]

    def get(self, request, workspace_slug, project_id):
        project = Project.objects.get(workspace__slug=workspace_slug, pk=project_id)
        if project.estimate_id is not None:
            estimate_points = EstimatePoint.objects.filter(
                estimate_id=project.estimate_id,
                project_id=project_id,
                workspace__slug=workspace_slug,
            )
            serializer = EstimatePointSerializer(estimate_points, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)


class BulkEstimatePointEndpoint(BaseViewSet):
    permission_classes = [
        ProjectEntityPermission,
    ]
    model = Estimate
    serializer_class = EstimateSerializer

    def list(self, request, workspace_slug, project_id):
        estimates = (
            Estimate.objects.filter(
                workspace__slug=workspace_slug, project_id=project_id
            )
            .prefetch_related("points")
            .select_related("workspace", "project")
        )
        serializer = EstimateReadSerializer(estimates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, workspace_slug, project_id):
        if not request.data.get("estimate", False):
            return Response(
                {"error": "Estimate is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estimate_points = request.data.get("estimate_points", [])

        serializer = EstimatePointSerializer(
            data=request.data.get("estimate_points"), many=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        estimate_serializer = EstimateSerializer(data=request.data.get("estimate"))
        if not estimate_serializer.is_valid():
            return Response(
                estimate_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        estimate = estimate_serializer.save(
            project_id=project_id,
            created_by=self.request.user,
            updated_by=self.request.user,
        )
        project = Project.objects.get(workspace__slug=workspace_slug, pk=project_id)
        if project.estimate is None:
            project.estimate = estimate
            project.save()
        estimate_points = EstimatePoint.objects.bulk_create(
            [
                EstimatePoint(
                    estimate=estimate,
                    key=estimate_point.get("key", 0),
                    value=estimate_point.get("value", ""),
                    description=estimate_point.get("description", ""),
                    project_id=project_id,
                    workspace_id=estimate.workspace_id,
                    created_by=request.user,
                    updated_by=request.user,
                )
                for estimate_point in estimate_points
            ],
            batch_size=10,
            ignore_conflicts=True,
        )

        estimate_point_serializer = EstimatePointSerializer(estimate_points, many=True)

        return Response(
            {
                "estimate": estimate_serializer.data,
                "estimate_points": estimate_point_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, workspace_slug, project_id, estimate_id):
        estimate = Estimate.objects.get(
            pk=estimate_id, workspace__slug=workspace_slug, project_id=project_id
        )
        serializer = EstimateReadSerializer(estimate)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def partial_update(self, request, workspace_slug, project_id, estimate_id):
        if not request.data.get("estimate", False):
            return Response(
                {"error": "Estimate is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not len(request.data.get("estimate_points", [])):
            return Response(
                {"error": "Estimate points are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estimate = Estimate.objects.get(pk=estimate_id)

        estimate_serializer = EstimateSerializer(
            estimate, data=request.data.get("estimate"), partial=True
        )
        if not estimate_serializer.is_valid():
            return Response(
                estimate_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        estimate = estimate_serializer.save(
            updated_by=self.request.user,
        )

        estimate_points_data = request.data.get("estimate_points", [])

        estimate_points = EstimatePoint.objects.filter(
            pk__in=[
                estimate_point.get("id") for estimate_point in estimate_points_data
            ],
            workspace__slug=workspace_slug,
            project_id=project_id,
            estimate_id=estimate_id,
        )

        updated_estimate_points = []
        for estimate_point in estimate_points:
            # Find the data for that estimate point
            estimate_point_data = [
                point
                for point in estimate_points_data
                if point.get("id") == str(estimate_point.id)
            ]
            if len(estimate_point_data):
                estimate_point.value = estimate_point_data[0].get(
                    "value", estimate_point.value
                )
                updated_estimate_points.append(estimate_point)

        EstimatePoint.objects.bulk_update(
            updated_estimate_points,
            ["value"],
            batch_size=10,
        )

        estimate_point_serializer = EstimatePointSerializer(estimate_points, many=True)
        return Response(
            {
                "estimate": estimate_serializer.data,
                "estimate_points": estimate_point_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, workspace_slug, project_id, estimate_id):
        estimate = Estimate.objects.get(
            pk=estimate_id, workspace__slug=workspace_slug, project_id=project_id
        )
        estimate.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
