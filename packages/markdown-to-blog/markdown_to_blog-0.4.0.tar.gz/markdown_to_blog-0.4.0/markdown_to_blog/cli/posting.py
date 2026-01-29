"""
포스팅 관리 관련 명령어
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Optional

import click
from loguru import logger
from markdown2 import Markdown
from googleapiclient import errors as google_api_errors

from ..libs.blogger import get_all_posts, update_post, delete_post, DEFAULT_MARKDOWN_EXTRAS
from . import mdb


@mdb.command("backup-posting", help="Downloads all posts from a blog and stores info in posting_info.json.")
@click.option("--blog-id", "blog_id_option", required=True, help="The ID of the blog to backup.")
@click.option("--target-dir", "target_dir_option", required=True, type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), help="Directory to save posts and posting_info.json.")
def run_backup_posting(blog_id_option: str, target_dir_option: str):
    """
    Downloads all 'live' posts from the specified blog ID, saves each post as an HTML file
    in the target directory, and creates a posting_info.json file with metadata (filename and hash)
    for each post.
    """
    try:
        target_dir = Path(target_dir_option)
        target_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting backup for blog ID: {blog_id_option} to directory: {target_dir}")
        posts = get_all_posts(blog_id_option)

        if not posts:
            click.echo(f"No posts found for blog ID {blog_id_option}. Nothing to backup.")
            return

        posts_info = {}
        saved_count = 0

        for post in posts:
            post_id = post.get("id")
            content = post.get("content")

            if not post_id or content is None:
                logger.warning(f"Post missing ID or content, skipping: {post.get('title', 'N/A')}")
                continue

            filename = f"post_{post_id}.html"
            file_path = target_dir / filename

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()
                posts_info[post_id] = {"filename": filename, "hash": hash_value}
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving post {post_id} to {file_path}: {e}")
                continue
        
        info_file_path = target_dir / "posting_info.json"
        with open(info_file_path, "w", encoding="utf-8") as f:
            json.dump(posts_info, f, indent=4, ensure_ascii=False)

        click.echo(f"Backup complete. {saved_count} posts saved to {target_dir}")
        logger.info(f"Posting information saved to {info_file_path}")

    except Exception as e:
        click.echo(f"Backup failed: {str(e)}", err=True)
        logger.error(f"Backup failed catastrophically: {str(e)}")
        sys.exit(1)


@mdb.command("sync-posting", help="Synchronizes posts from a blog with a local directory based on posting_info.json.")
@click.option("--blog-id", "blog_id_option", required=True, help="The ID of the blog to sync from.")
@click.option("--posting-info", "posting_info_path_option", required=True, type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True), help="Path to the posting_info.json file.")
@click.option("--target-dir", "target_dir_option", required=True, type=click.Path(file_okay=False, dir_okay=True, resolve_path=True), help="Directory to save and sync posts.")
def run_sync_posting(blog_id_option: str, posting_info_path_option: str, target_dir_option: str):
    """
    Synchronizes posts from a blog with a local directory.
    It uses a posting_info.json file to track local file hashes and update as necessary.
    """
    try:
        target_dir = Path(target_dir_option)
        posting_info_file = Path(posting_info_path_option)

        target_dir.mkdir(parents=True, exist_ok=True)

        local_posts_info = {}
        if posting_info_file.exists() and posting_info_file.stat().st_size > 0:
            try:
                with open(posting_info_file, "r", encoding="utf-8") as f:
                    local_posts_info = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {posting_info_file}. Starting with empty info.")
        else:
            logger.info(f"{posting_info_file} does not exist or is empty. Starting with empty info.")

        logger.info(f"Starting sync for blog ID: {blog_id_option} with local directory: {target_dir} using info file: {posting_info_file}")
        remote_posts = get_all_posts(blog_id_option)

        if not remote_posts:
            click.echo(f"No remote posts found for blog ID {blog_id_option}. Local state will be preserved if no info file, or posts_info.json will be emptied if it exists and remote is empty.")
            if local_posts_info:
                logger.info("Remote blog is empty. Clearing local posting_info.json.")
                with open(posting_info_file, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4, ensure_ascii=False)
            return

        new_posts_count = 0
        updated_posts_count = 0

        updated_local_posts_info = {}

        for remote_post in remote_posts:
            post_id = remote_post.get("id")
            content = remote_post.get("content")

            if not post_id or content is None:
                logger.warning(f"Remote post missing ID or content, skipping: {remote_post.get('title', 'N/A')}")
                continue

            remote_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            filename = f"post_{post_id}.html"
            
            local_entry = local_posts_info.get(post_id)

            if local_entry:
                if local_entry.get('hash') == remote_hash:
                    updated_local_posts_info[post_id] = local_entry.copy()
                    filename = local_entry.get('filename', filename)
                else:
                    filename = local_entry.get('filename', filename)
                    file_path = target_dir / filename
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    updated_local_posts_info[post_id] = {"filename": filename, "hash": remote_hash}
                    updated_posts_count += 1
                    logger.info(f"Updated post: {post_id} in file {filename}")
            else:
                file_path = target_dir / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                updated_local_posts_info[post_id] = {"filename": filename, "hash": remote_hash}
                new_posts_count += 1
                logger.info(f"Added new post: {post_id} to file {filename}")
        
        with open(posting_info_file, "w", encoding="utf-8") as f:
            json.dump(updated_local_posts_info, f, indent=4, ensure_ascii=False)

        processed_count = len(remote_posts)
        click.echo(f"Sync complete. Total remote posts processed: {processed_count}. New local files: {new_posts_count}. Updated local files: {updated_posts_count}.")
        logger.info(f"Posting information updated in {posting_info_file}")

    except Exception as e:
        click.echo(f"Sync failed: {str(e)}", err=True)
        logger.error(f"Sync failed catastrophically: {str(e)}")
        sys.exit(1)


@mdb.command("update-posting", help="Updates an existing blog post.")
@click.option("--blog-id", "blog_id_option", required=True, help="The ID of the blog.")
@click.option("--post-id", "post_id_option", required=True, help="The ID of the post to update.")
@click.option("--title", "title_option", required=True, help="The new title for the post.")
@click.argument("markdown_file_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option("--draft", "draft_option", is_flag=True, default=False, help="Update the post as a draft.")
@click.option("--label", "labels_option", multiple=True, help="Set labels for the post. Replaces existing if specified. Omit to keep current labels. To clear all labels, this option should not be used and a future --clear-labels flag might be implemented if needed.")
@click.option("--description", "description_option", default=None, help="Set the search meta description for the post.")
def run_update_posting(
    blog_id_option: str, 
    post_id_option: str, 
    title_option: str, 
    markdown_file_path: str, 
    draft_option: bool, 
    labels_option: tuple, 
    description_option: Optional[str]
):
    """
    Updates an existing blog post using content from a local Markdown file.
    """
    try:
        md_file_path = Path(markdown_file_path)
        with open(md_file_path, "r", encoding="utf-8") as f:
            raw_markdown_content = f.read()

        markdowner = Markdown(extras=DEFAULT_MARKDOWN_EXTRAS)
        html_content = markdowner.convert(raw_markdown_content)

        labels_to_pass = list(labels_option) if labels_option else None

        updated_post_data = update_post(
            blog_id=blog_id_option,
            post_id=post_id_option,
            title=title_option,
            html_content=html_content,
            is_draft=draft_option,
            labels=labels_to_pass,
            search_description=description_option,
        )
        
        click.echo(
            f"Post '{updated_post_data['title']}' (ID: {updated_post_data['id']}) updated successfully. "
            f"URL: {updated_post_data.get('url', 'N/A')}"
        )

    except google_api_errors.HttpError as e:
        if e.resp.status == 404:
            click.echo(
                f"Error: Post with ID '{post_id_option}' not found on blog '{blog_id_option}'.",
                err=True,
            )
        else:
            click.echo(f"Error updating post: {e.resp.status} {e._get_reason()}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo(f"Error: Markdown file not found at '{markdown_file_path}'.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {str(e)}", err=True)
        sys.exit(1)


@mdb.command("delete-posting", help="Deletes a blog post.")
@click.option("--blog-id", "blog_id_option", required=True, help="The ID of the blog.")
@click.option("--post-id", "post_id_option", required=True, help="The ID of the post to delete.")
def run_delete_posting(blog_id_option: str, post_id_option: str):
    """
    Deletes a specific blog post by its ID from a specified blog.
    """
    try:
        delete_post(blog_id=blog_id_option, post_id=post_id_option)
        click.echo(
            f"Post with ID '{post_id_option}' has been successfully deleted from blog '{blog_id_option}'."
        )
    except google_api_errors.HttpError as e:
        if e.resp.status == 404:
            click.echo(
                f"Error: Post with ID '{post_id_option}' not found on blog '{blog_id_option}'.",
                err=True,
            )
        else:
            click.echo(f"Error deleting post: {e.resp.status} {e._get_reason()}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {str(e)}", err=True)
        sys.exit(1)


