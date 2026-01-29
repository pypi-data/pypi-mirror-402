"""dxfields serializers and deserializers"""

import json
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest
from plone.restapi.interfaces import ISerializeToJson, IDeserializeFromJson
from plone.restapi.serializer.dxcontent import SerializeToJson
from plone.restapi.deserializer.dxcontent import DeserializeFromJson
from plone.restapi.serializer.utils import uid_to_url
from plone.restapi.deserializer.utils import path2uid
from plone.app.uuid.utils import uuidToCatalogBrain
from eea.dexterity.indicators.interfaces import IIndicator

# Fields that store references as UUIDs but should be serialized as URLs
COPIED_FIELDS = ("copied_from", "copied_to")


@implementer(ISerializeToJson)
@adapter(IIndicator, IBrowserRequest)
class IndicatorSerializer(SerializeToJson):
    """Custom serializer for Indicator to convert UUID to URLs for
    copied_from/copied_to"""

    def __call__(self, version=None, include_items=True):
        result = super().__call__(version=version, include_items=include_items)

        # Convert UUIDs to URLs for copied fields
        for field in COPIED_FIELDS:
            if field in result and result[field]:
                uid = result[field]
                brain = uuidToCatalogBrain(uid)
                if brain:
                    result[field] = brain.getURL()
                else:
                    result[field] = uid_to_url("resolveuid/{}".format(uid))

        return result


@implementer(IDeserializeFromJson)
@adapter(IIndicator, IBrowserRequest)
class IndicatorDeserializer(DeserializeFromJson):
    """Custom deserializer for Indicator to convert URLs back to UUIDs for
    copied_from/copied_to"""

    def __call__(self, validate_all=False, create=False):
        # Get the data before processing
        data = self.request.get("BODY", {})
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (ValueError, TypeError):
                data = {}

        # Convert URLs back to UUIDs for copied fields
        for field in COPIED_FIELDS:
            if field in data and data[field]:
                data[field] = path2uid(context=self.context, link=data[field])

        # Update the request body with the modified data
        self.request["BODY"] = json.dumps(data)

        # Continue with normal deserialization
        return super().__call__(validate_all=validate_all, create=create)
