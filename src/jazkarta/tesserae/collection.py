import random
from plone.app.standardtiles.existingcontent import CatalogSource
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import Unauthorized
from operator import itemgetter
from zope.component import getMultiAdapter
from zope.schema.vocabulary import SimpleVocabulary
from zope import schema
from zope.interface import Interface
from zope.interface import alsoProvides

from txbizlaw.customviews.tiles.resources import IResourceListingTileLayer

from .summary import ContentSummaryTile
from .summary import IContentSummaryTile
from . import _


def availableListingViewsVocabulary():
    listing_views = {
        'article_summary_view': u'Article Summary Layout',
        'committee_feeds_view': u'Committee Feeds Layout',
        'resource_badge_view': u'Badge Layout',
        'resource_listing_view': u'Listing Layout',
        # 'resource_masonry_view': u'Masonry Layout',
        'news_items_view': 'News Items Layout',
        'listing_view': 'Summary Layout',
        'tile_view': 'Tile Tile Layout'
    }
    voc = []
    for key, label in sorted(listing_views.items(), key=itemgetter(1)):
        voc.append(SimpleVocabulary.createTerm(key, key, label))
    return SimpleVocabulary(voc)


class ICollectionSummaryTile(IContentSummaryTile):

    content_uid = schema.Choice(
        title=_(u"Select an existing collection"),
        required=True,
        source=CatalogSource(
            object_provides='plone.app.contenttypes.behaviors.collection.ISyndicatableCollection'
        ),
    )

    show_title = schema.Bool(
        title=_(u"Show collection title"),
        default=True,
    )

    limit = schema.Int(
        title=_(u"Number of items to display"),
        default=3,
        min=1,
    )

    show_description = schema.Bool(
        title=_(u"Show description of result items"),
        default=True,
    )

    show_date = schema.Bool(
        title=_(u"Show publication date of result items"),
        description=_(u"Events will always include start date"),
        default=True,
    )

    display_mode = schema.Choice(
        title=_(u'Display mode'),
        vocabulary=availableListingViewsVocabulary(),
        description=_(u'Select the type of tile to display the results in.'),
        default='listing_view',
        required=True
    )


class CollectionSummaryTile(ContentSummaryTile):
    """Existing content tile
    """

    template = ViewPageTemplateFile('templates/collection.pt')
    summary_template = ViewPageTemplateFile('templates/summary.pt')
    show_description = False
    results = ()
    macro = None
    title = None
    has_special = False
    default_display_modes = ['tile_view', 'listing_view']

    def update(self):
        super(CollectionSummaryTile, self).update()
        self.macro = self.summary_template.macros['summary']
        self.show_title = self.data.get('show_title', False)
        limit = self.data.get('limit', 3)
        self.results = []
        for b in self.content.results(limit=limit):
            try:
                obj = b.getObject()
                self.results.append(obj)
            except Unauthorized:
                continue

    @property
    def allow_render(self):
        return self.display_mode not in self.default_display_modes

    def get_results(self):
        results = []
        self.has_special = False
        for item in self.results:
            title = item.title
            is_case_note = False
            results.append({
                'title': item.title,
                'url': item.absolute_url(),
                'description': item.description,
                'authors': getattr(item, 'authors', ''),
                'full_title': item.title
            })
        results.sort(key = lambda v: len(v.get('full_title', '')))
        return results

    def contents(self):
        if self.display_mode == 'resource_masonry_view':
            return self.get_results()
        return self.results
        
    def random(self):
        return random.randint(1,101)
            
    def render(self):
        options = dict(original_context=self.context)
        alsoProvides(self.request, IResourceListingTileLayer)
        return getMultiAdapter((self, self.request), name=self.display_mode, context=self.context)(**options)
