from rest_framework.permissions import IsAuthenticated

class PermissionClassesByActionMixin(object):
    def get_permissions(self):
        try:
            return ([IsAuthenticated()]
                    + [permission() for permission in self.permission_classes_by_action[self.action]])
        except (KeyError, AttributeError):
            # Catch the following:
            # KeyError: if permission_classes_by_action is missing this action;
            # AttributeError: if permission_classes_by_action itself is missing
            return ([IsAuthenticated()]
                    + [permission() for permission in self.permission_classes])
