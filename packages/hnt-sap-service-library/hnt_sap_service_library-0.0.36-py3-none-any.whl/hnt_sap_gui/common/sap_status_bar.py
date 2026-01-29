import logging
import re

logger = logging.getLogger(__name__)

def sbar_extracted_text(patter, full_text):
    regex = re.compile(patter , re.IGNORECASE)
    text_list = regex.search(full_text)
    if text_list is None:
        return None
    text = text_list[1]
    logger.info(f"Extracted text: '{text}', from full_text: '{full_text}'")
    return text