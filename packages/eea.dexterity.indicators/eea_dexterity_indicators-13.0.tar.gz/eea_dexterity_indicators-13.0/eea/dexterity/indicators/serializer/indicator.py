"""Indicator serializer"""

from eea.dexterity.indicators.interfaces import IIndicator
from plone import api
from plone.restapi.interfaces import IObjectPrimaryFieldTarget
from zope.interface import implementer, Interface
from zope.component import adapter


@adapter(IIndicator, Interface)
@implementer(IObjectPrimaryFieldTarget)
class IndicatorObjectPrimaryFieldTarget:
    """Indicator primary field target"""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        state = api.content.get_state(self.context)
        if state not in ("marked_for_deletion", "archived"):
            return None
        url = self.context.absolute_url()
        old_version = url.split("-")[-1]
        try:
            int(old_version)
        except ValueError:
            return None

        return url.rstrip(old_version).rstrip("-")
