# -*- coding: utf-8 -*-


class RequestResource(object):
    def __init__(
        self,
        type: str,
        namespace: str,
        group: str,
        resource: str | None,
    ):
        self.type = type
        if namespace is None or namespace == "":
            namespace = "public"
        self.namespace = namespace
        if group is None or group == "":
            group = "DEFAULT_GROUP"
        self.group = group
        self.resource = resource

    def get_type(self):
        return self.type

    def get_namespace(self):
        return self.namespace

    def get_group(self):
        return self.group

    def get_resource(self):
        return self.resource
