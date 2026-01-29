from . import scroll

scroll_classes = {
    "scrolling_text": scroll.ScrollingTextModel,
    "stub_scroll": scroll.StubScrollModel,
    "numbered_pager": scroll.NumberedPagerModel,
    "first_page": scroll.FirstPageModel,
    "prev_page": scroll.PrevPageModel,
    "current_page": scroll.CurrentPageModel,
    "next_page": scroll.NextPageModel,
    "last_page": scroll.LastPageModel,
}
