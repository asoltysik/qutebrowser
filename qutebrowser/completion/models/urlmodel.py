# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014-2017 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Function to return the url completion model for the `open` command."""

from qutebrowser.completion.models import (completionmodel, listcategory,
                                           sqlcategory)
from qutebrowser.config import config
from qutebrowser.utils import qtutils, log, objreg


_URLCOL = 0
_TEXTCOL = 1


def _delete_url(completion):
    """Delete the selected item.

    Args:
        completion: The Completion object to use.
    """
    index = completion.currentIndex()
    qtutils.ensure_valid(index)
    category = index.parent()
    index = category.child(index.row(), _URLCOL)
    catname = category.data()
    qtutils.ensure_valid(category)

    if catname == 'Bookmarks':
        urlstr = index.data()
        log.completion.debug('Deleting bookmark {}'.format(urlstr))
        bookmark_manager = objreg.get('bookmark-manager')
        bookmark_manager.delete(urlstr)
    elif catname == 'Quickmarks':
        quickmark_manager = objreg.get('quickmark-manager')
        sibling = index.sibling(index.row(), _TEXTCOL)
        qtutils.ensure_valid(sibling)
        name = sibling.data()
        log.completion.debug('Deleting quickmark {}'.format(name))
        quickmark_manager.delete(name)


def url():
    """A model which combines bookmarks, quickmarks and web history URLs.

    Used for the `open` command.
    """
    model = completionmodel.CompletionModel(
        column_widths=(40, 50, 10),
        delete_cur_item=_delete_url)

    quickmarks = ((url, name) for (name, url)
                  in objreg.get('quickmark-manager').marks.items())
    bookmarks = objreg.get('bookmark-manager').marks.items()

    model.add_category(listcategory.ListCategory('Quickmarks', quickmarks,
                                                 columns_to_filter=[0, 1]))
    model.add_category(listcategory.ListCategory('Bookmarks', bookmarks,
                                                 columns_to_filter=[0, 1]))

    # replace 's to avoid breaking the query
    timefmt = config.get('completion', 'timestamp-format').replace("'", "`")
    select_time = "strftime('{}', last_atime, 'unixepoch')".format(timefmt)
    hist_cat = sqlcategory.SqlCategory(
        'CompletionHistory', sort_order='desc', sort_by='last_atime',
        filter_fields=['url', 'title'],
        select='url, title, {}'.format(select_time))
    model.add_category(hist_cat)
    return model
