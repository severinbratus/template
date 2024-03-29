from __future__ import unicode_literals

from pybtex.style import FormattedEntry, FormattedBibliography
from pybtex.style.template import node, join
from pybtex.richtext import Symbol
from pybtex.plugin import Plugin, find_plugin


@node
def toplevel(children, data):
    return join(sep=Symbol('newblock')) [children].format_data(data)


class BaseStyle(Plugin):
    """
    The base class for pythonic formatting styles.
    """

    default_name_style = None
    default_label_style = None
    default_sorting_style = None

    def __init__(self, label_style=None, name_style=None, sorting_style=None, abbreviate_names=False, min_crossrefs=2, **kwargs):
        self.name_style = find_plugin('pybtex.style.names', name_style or self.default_name_style)()
        self.label_style = find_plugin('pybtex.style.labels', label_style or self.default_label_style)()
        self.sorting_style = find_plugin('pybtex.style.sorting', sorting_style or self.default_sorting_style)()
        self.format_name = self.name_style.format
        self.format_labels = self.label_style.format_labels
        self.sort = self.sorting_style.sort
        self.abbreviate_names = abbreviate_names
        self.min_crossrefs = min_crossrefs

    def format_entries(self, entries, bib_data=None):
        sorted_entries = self.sort(entries)
        labels = self.format_labels(sorted_entries)
        for label, entry in zip(labels, sorted_entries):
            yield self.format_entry(label, entry, bib_data=bib_data)

    def format_entry(self, label, entry, bib_data=None):
            context = {
                'entry': entry,
                'style': self,
                'bib_data': bib_data,
            }
            try:
                get_template = getattr(self, 'get_{}_template'.format(entry.type))
            except AttributeError:
                format_method = getattr(self, "format_" + entry.type)
                text = format_method(context)
            else:
                text = get_template(entry).format_data(context)
            return FormattedEntry(entry.key, text, label)

    def format_bibliography(self, bib_data, citations=None):
        """
        Format bibliography entries with the given keys and return a
        ``FormattedBibliography`` object.

        :param bib_data: A :py:class:`pybtex.database.BibliographyData` object.
        :param citations: A list of citation keys.
        """

        if citations is None:
            citations = list(bib_data.entries.keys())
        citations = bib_data.add_extra_citations(citations, self.min_crossrefs)
        entries = [bib_data.entries[key] for key in citations]
        formatted_entries = self.format_entries(entries)
        formatted_bibliography = FormattedBibliography(formatted_entries, style=self, preamble=bib_data.preamble)
        return formatted_bibliography
