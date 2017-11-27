from plone.app.standardtiles.existingcontent import uuidToObject
from plone.app.standardtiles.existingcontent import CatalogSource
from plone.memoize.view import memoize
from plone.tiles import Tile
from plone.supermodel import model
from plone.uuid.interfaces import IUUID
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import Unauthorized
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from .config import IMAGE_NAMES
from . import _


class IContentSummaryTile(model.Schema):

    content_uid = schema.Choice(
        title=_(u"Select an existing content item"),
        required=True,
        source=CatalogSource(),
    )

    show_description = schema.Bool(
        title=_(u"Show content description"),
        default=False,
    )

    show_date = schema.Bool(
        title=_(u"Show publication date"),
        description=_(u"Include the publication date in the "
                      u"summary (events will always include the start date)"),
        default=False,
    )

    display_mode = schema.Choice(
        title=_(u'Display mode'),
        vocabulary=SimpleVocabulary(
            [
                SimpleTerm(value=u'listing_view', title=_(u'Listing View')),
                SimpleTerm(value=u'tile_view', title=_(u'Tile View'))
            ]
        ),
        description=_(u'Select the type of tile to display the results in.'),
        default='listing_view',
        required=True
    )


class ContentSummaryTile(Tile):
    """Existing content tile
    """

    template = ViewPageTemplateFile('templates/summary.pt')
    show_description = False

    def __call__(self):
        self.update()
        return self.template()

    def update(self):
        self.show_description = self.data.get('show_description', False)
        self.show_date = self.data.get('show_date', False)
        self.display_mode = self.data.get('display_mode', 'listing_view')

    @property
    @memoize
    def content(self):
        uuid = self.data.get('content_uid')
        if uuid != IUUID(self.context, None):
            try:
                item = uuidToObject(uuid)
            except Unauthorized:
                item = None
                if not self.request.get('PUBLISHED'):
                    raise  # Should raise while still traversing
            if item is not None:
                return item
        return None

    def image_url(self, obj=None, scale_name="preview"):
        content = obj or self.content
        if content is None:
            return

        images_view = content.unrestrictedTraverse('@@images')

        for field_name in IMAGE_NAMES:
            try:
                scale = images_view.scale(fieldname=field_name,
                                          scale=scale_name)
            except AttributeError:
                continue
            if scale is not None:
                return scale.url