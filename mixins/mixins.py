from rest_framework.permissions import IsAuthenticated

class PermissionClassesByActionMixin(object):
    def get_permissions(self):
        try:
            return ([IsAuthenticated()]
                    + [permission() for permission in self.permission_classes_by_action[self.action]])
        except KeyError:
            return ([IsAuthenticated()]
                    + [permission() for permission in self.permission_classes])
