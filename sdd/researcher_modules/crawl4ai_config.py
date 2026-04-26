def build_crawl4ai_run_config(
    crawler_run_config_cls,
    has_markdown_filters: bool,
    pruning_content_filter_cls=None,
    default_markdown_generator_cls=None,
):
    kwargs = {
        "wait_until": "load",
        "word_count_threshold": 10,
        "excluded_tags": ["nav", "footer", "header", "aside", "form"],
        "remove_overlay_elements": True,
    }
    if (
        has_markdown_filters
        and pruning_content_filter_cls is not None
        and default_markdown_generator_cls is not None
    ):
        kwargs["markdown_generator"] = default_markdown_generator_cls(
            content_filter=pruning_content_filter_cls(
                threshold=0.45,
                threshold_type="dynamic",
                min_word_threshold=8,
            ),
            options={"ignore_links": True},
        )
    return crawler_run_config_cls(**kwargs)
