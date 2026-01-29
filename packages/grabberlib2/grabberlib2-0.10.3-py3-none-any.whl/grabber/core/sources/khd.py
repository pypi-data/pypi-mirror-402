import pathlib
from typing import Any

from boltons.setutils import IndexedSet
from bs4 import Tag
from telegraph import Telegraph
from tqdm import tqdm

from grabber.core.sources.helpers.core import get_page_title, handle_final_destination
from grabber.core.utils import (
    build_unique_img_urls,
    get_tags,
    headers_mapping,
    query_mapping,
    run_downloader,
    send_post_to_telegram,
)


async def get_images_from_pagination(url: str, headers: dict[str, str] | None = None) -> list[str]:
    page_nav_query = "div.page-link-box li a.page-numbers"
    tags, _ = await get_tags(url, headers=headers, query=page_nav_query)
    return [a.attrs["href"] for a in tags if tags]



async def get_sources_for_4khd(
    sources: list[str],
    entity: str,
    telegraph_client: Telegraph | None = None,
    final_dest: str | pathlib.Path = "",
    save_to_telegraph: bool | None = False,
    **kwargs: Any,
) -> None:
    tqdm_sources_iterable = tqdm(
        sources,
        total=len(sources),
        desc="Retrieving URLs...",
    )
    query, src_attr = query_mapping[entity]
    headers = headers_mapping.get(entity, None)
    page_title = ""
    title_folder_mapping: dict[str, tuple[IndexedSet, Any]] = {}
    posts_sent_counter = 0
    titles = IndexedSet()
    ordered_unique_img_urls = None
    all_sources: list[str] = []
    original_folder_path = final_dest
    channel = kwargs.get("channel", "")

    for source_url in tqdm_sources_iterable:
        final_dest = pathlib.Path(str(original_folder_path)) if final_dest else ""
        all_sources.append(source_url)

        folder_name = ""
        urls = [
            source_url,
            *await get_images_from_pagination(url=source_url, headers=headers),
        ]
        image_tags: list[Tag] = []

        for index, url in enumerate(urls):
            tags, soup = await get_tags(
                url,
                headers=headers,
                query=query,
            )
            image_tags.extend(tags or [])
            page_title = get_page_title(soup=soup, strings_to_remove=["- 4KHD", "- Page"])
            titles.add(page_title)

            if index == 0:
                folder_name = get_page_title(soup=soup, strings_to_remove=["- 4KHD", "- Page"])
                page_title = folder_name.strip().rstrip()
                titles.add(page_title)

        ordered_unique_img_urls = await build_unique_img_urls(image_tags, src_attr)
        tqdm_sources_iterable.set_description(f"Finished retrieving images for {page_title}")

        folder_dest, title_folder_mapping = handle_final_destination(
            page_title=page_title,
            entity=entity,
            ordered_unique_img_urls=ordered_unique_img_urls,
            title_folder_mapping=title_folder_mapping,
            final_dest=final_dest,
        )

        # if final_dest:
        #     final_dest = pathlib.Path(final_dest) / unidecode(f"{page_title} - {entity}")
        #     if not final_dest.exists():
        #         final_dest.mkdir(parents=True, exist_ok=True)
        #
        #     folder_name = f"{page_title}"
        #     title_folder_mapping[page_title] = (ordered_unique_img_urls, final_dest)

        if save_to_telegraph:
            _ = await send_post_to_telegram(
                ordered_unique_img_urls=ordered_unique_img_urls,
                page_title=page_title,
                telegraph_client=telegraph_client,
                posts_sent_counter=posts_sent_counter,
                tqdm_sources_iterable=tqdm_sources_iterable,
                all_sources=all_sources,
                source_url=source_url,
                entity=entity,
                channel=channel,
            )
        page_title = ""

    if folder_dest and ordered_unique_img_urls:
        await run_downloader(
            final_dest=folder_dest,
            page_title=page_title,
            unique_img_urls=ordered_unique_img_urls,
            titles=titles,
            title_folder_mapping=title_folder_mapping,
            headers=headers,
        )
