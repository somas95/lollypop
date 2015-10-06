# Copyright (c) 2014-2015 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gio

from gettext import gettext as _
from locale import getdefaultlocale
from random import shuffle
import re
import wikipedia


class Wikipedia:
    """
        Wikipedia helper
    """

    def __init__(self):
        """
            Init wikipedia
        """
        language = getdefaultlocale()[0][0:2]
        wikipedia.set_lang(language)
        # Translators: Put here words added by wikipedia in band search
        # Ex: Muse_(band), Peaches(musician)
        self._search_str = _("musician;band")

    def search(self, pattern):
        """
            Search in wikipedia
            @param pattern as string
        """
        search = wikipedia.search(pattern)
        return search

    def get_page(self, page):
        """
            Get wikipedia page
            @param page as str
            @return (url as str, image url as str, content as str)
        """
        if not Gio.NetworkMonitor.get_default().get_network_available():
            return (None, None, None)
        try:
            words = page.split(' ')
            page = wikipedia.page(page)
            if page is None:
                return (None, None, None)
            content = page.content
            content = re.sub(r'%s ==' % _('Modify'), ' ==', content)
            url = page.url
            img = None
            shuffle(page.images)
            for image in page.images:
                if image.lower().endswith('.jpg'):
                    # Search specific string in urls
                    for word in words:
                        if word in image:
                            return (url, image, content)
                    img = image
            return (url, img, content)
        except:
            return (None, None, None)

#######################
# PRIVATE             #
#######################
