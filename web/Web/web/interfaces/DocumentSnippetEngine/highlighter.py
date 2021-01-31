from whoosh import analysis, highlight
from whoosh.analysis.tokenizers import SpaceSeparatedTokenizer
from whoosh.analysis.filters import StopFilter
from whoosh.analysis.filters import LowercaseFilter


def generate_highlight(text, query):
    sst = SpaceSeparatedTokenizer() | StopFilter(lang="es") | LowercaseFilter()
    terms = frozenset([token.text for token in sst(query)])
    sa = analysis.StandardAnalyzer()
    cf = highlight.ContextFragmenter(maxchars=50, surround=20)
    hf = highlight.HtmlFormatter(tagname="b", termclass="t")
    return highlight.highlight(text, terms, sa, cf, hf)

