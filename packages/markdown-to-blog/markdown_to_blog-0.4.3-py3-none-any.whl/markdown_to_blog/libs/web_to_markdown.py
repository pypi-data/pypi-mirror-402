import logging
from typing import Optional # Ensure Optional is imported
from playwright.sync_api import sync_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
from markdownify import markdownify

import time

# Configure a logger for this module (optional, but good practice)
logger = logging.getLogger(__name__)

class HTMLFetchError(Exception):
    """Custom exception for errors during HTML fetching via Playwright."""
    pass

def fetch_html_with_playwright(
    url: str, 
    timeout: int = 60000, 
    scroll_attempts: int = 3, 
    scroll_delay_ms: int = 500,
    start_comment: Optional[str] = None,
    end_comment: Optional[str] = None
) -> str:
    """
    Fetches HTML content from a URL, optionally extracting a specific section between comments.

    Args:
        url: The URL of the web page.
        timeout: Main navigation and operation timeout in milliseconds.
        scroll_attempts: Number of times to scroll for lazy-loaded content.
        scroll_delay_ms: Delay between scrolls.
        start_comment: Optional text of an HTML comment marking the start of desired content.
        end_comment: Optional text of an HTML comment marking the end of desired content.

    Returns:
        The HTML content of the page.

    Raises:
        HTMLFetchError: If any error occurs during fetching or Playwright operation.
    """
    logger.info(f"Attempting to fetch HTML from URL: {url} with Playwright (timeout: {timeout}ms, scrolls: {scroll_attempts}).")
    browser = None # Ensure browser is defined for the finally block
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch() # Consider headless=True for production/CI
            page = browser.new_page()
            
            logger.info(f"Navigating to {url} with wait_until='load'.")
            # Initial page load - use main timeout.
            # wait_until='load' fires when the load event is fired.
            page.goto(url, timeout=timeout, wait_until='load')
            logger.info(f"Initial page load event fired for {url}.")

            if scroll_attempts > 0:
                logger.info(f"Performing {scroll_attempts} scroll attempts for {url}.")
                for i in range(scroll_attempts):
                    logger.debug(f"Scroll attempt {i + 1}/{scroll_attempts} for {url}.")
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(scroll_delay_ms) 
                logger.info(f"Finished {scroll_attempts} scroll attempts for {url}.")

            logger.info(f"Waiting for network to be idle after all loading/scrolling for {url}...")
            try:
                # Use a significant portion of the main timeout for this final settle.
                # Ensure it's at least 1 second if timeout is small.
                final_network_idle_timeout = timeout // 2 if timeout >= 2000 else 1000
                if final_network_idle_timeout <= 0: # Ensure positive timeout
                    final_network_idle_timeout = 1000 
                page.wait_for_load_state('networkidle', timeout=final_network_idle_timeout)
                logger.info(f"Network is idle for {url}.")
            except PlaywrightTimeoutError:
                logger.warning(
                    f"Network did not become idle after scrolling/loading for {url} "
                    f"within {final_network_idle_timeout}ms. Proceeding to get content anyway."
                )
            
            target_html_content: Optional[str] = None

            if start_comment and end_comment:
                logger.info(f"Attempting to extract content between comments: '{start_comment}' and '{end_comment}'.")
                js_script = """
                ((startCommentText, endCommentText) => {
                    const walker = document.createNodeIterator(document.documentElement, NodeFilter.SHOW_COMMENT, null);
                    let node;
                    let startNode = null;
                    let endNode = null;

                    while (node = walker.nextNode()) {
                        if (node.nodeValue.trim() === startCommentText) {
                            startNode = node;
                        } else if (node.nodeValue.trim() === endCommentText) {
                            if (startNode && startNode !== node) { // Ensure startNode is found first and is different
                                endNode = node;
                                break; 
                            }
                        }
                    }

                    if (!startNode || !endNode) {
                        return null; // Comments not found or not in order
                    }

                    let contentHtml = "";
                    let currentNode = startNode.nextSibling;
                    while (currentNode && currentNode !== endNode) {
                        if (currentNode.nodeType === Node.ELEMENT_NODE) {
                            contentHtml += currentNode.outerHTML;
                        } else if (currentNode.nodeType === Node.TEXT_NODE) {
                            contentHtml += currentNode.nodeValue;
                        }
                        currentNode = currentNode.nextSibling;
                    }
                    return contentHtml || null; // Return null if contentHtml is empty string after collection
                })
                """
                extracted_html = page.evaluate(js_script, [start_comment, end_comment])

                if extracted_html is not None:
                    target_html_content = extracted_html
                    logger.info(f"Successfully extracted content between comments '{start_comment}' and '{end_comment}'. Length: {len(target_html_content)}")
                else:
                    logger.warning(
                        f"Start/end comments ('{start_comment}', '{end_comment}') not found or no content between them. "
                        f"Falling back to full page body HTML for {url}."
                    )
                    # Fallback logic if comments not found or content is empty
                    try:
                        target_html_content = page.locator('body').inner_html(timeout=timeout // 2 if timeout >=2000 else 1000)
                        logger.info(f"Fetched body HTML as fallback. Length: {len(target_html_content)}")
                    except PlaywrightTimeoutError:
                         logger.error(f"Timeout fetching body.inner_html as fallback for {url}.")
                         raise HTMLFetchError(f"Timeout fetching body.inner_html as fallback for {url}.")


            if target_html_content is None: # If not extracted by comments or comments not provided
                logger.info(f"No specific comments provided or extraction failed. Fetching entire page body HTML for {url}.")
                try:
                    target_html_content = page.locator('body').inner_html(timeout=timeout // 2 if timeout >=2000 else 1000)
                    logger.info(f"Fetched page body HTML. Length: {len(target_html_content)}")
                except PlaywrightTimeoutError:
                    logger.error(f"Timeout fetching body.inner_html for {url}.")
                    raise HTMLFetchError(f"Timeout fetching body.inner_html for {url}.")

            browser.close() # Close browser after successful operation
            browser = None # Set to None to indicate it's closed
        return target_html_content
    
    except PlaywrightTimeoutError as e: # This will catch timeout from the initial page.goto
        logger.error(f"Timeout error during initial page.goto('{url}') after {timeout}ms: {e}")
        raise HTMLFetchError(f"Timeout error while initially loading {url}. The page took too long to fire the 'load' event or for an earlier operation.")
    except PlaywrightError as e: # Catch other general Playwright errors
        logger.error(f"Playwright error while fetching {url}: {e}")
        raise HTMLFetchError(f"A Playwright error occurred while fetching {url}: {e}")
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error while fetching {url} with Playwright: {e}")
        raise HTMLFetchError(f"An unexpected error occurred: {e}")
    finally:
        if browser: # If browser was launched but not closed due to an error mid-try
            logger.info("Ensuring browser is closed in finally block.")
            browser.close()

def convert_html_to_markdown(html_content: str, **options) -> str:
    """
    Converts an HTML string to Markdown text using markdownify.

    Args:
        html_content: The HTML string to convert.
        **options: Additional options for markdownify.

    Returns:
        The Markdown text.
    """
    logger.info(f"Converting HTML content of length {len(html_content)} to Markdown.")
    try:
        # Example of default options you might want to set for markdownify
        # default_opts = {'heading_style': 'atx', 'bullets': '-'} 
        # combined_options = {**default_opts, **options}
        markdown_text = markdownify(html_content, **options)
        logger.info("Successfully converted HTML to Markdown.")
        return markdown_text
    except Exception as e:
        logger.error(f"Error during HTML to Markdown conversion: {e}")
        # Depending on markdownify's behavior, you might not expect exceptions
        # for typical HTML. If it can fail, wrap it or re-raise.
        raise # Re-raise for now, or define a ConvertError
