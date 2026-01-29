"""Upgrade step to link indicator versions based on naming conventions."""

import logging
import re
from collections import defaultdict

from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName

logger = logging.getLogger("eea.dexterity.indicators")

# Threshold to distinguish 10-digit timestamps from other numeric suffixes
# Unix timestamps from 2001 onwards are > 1000000000
TIMESTAMP_THRESHOLD = 1000000000


def get_base_name_and_sort_key(obj_id):
    """Extract base name and sort key from indicator ID.

    Returns a tuple (base_name, sort_key) where:
    - base_name: The canonical name without version suffix
    - sort_key: A tuple (category, value) for sorting:
        - (0, N) for drafts (.N suffix)
        - (1, timestamp) for archived (-timestamp suffix)
        - (2, 0) for published (plain name, newest)

    Examples:
    - 'agricultural-area-used-for-organic-1732031108' -> ('agricultural-area-used-for-organic', (1, 1732031108))
    - 'circular-material-use-rate.2' -> ('circular-material-use-rate', (0, 2))
    - 'copy_of_circular-material-use-rate' -> ('circular-material-use-rate', (0, 1))
    - 'agricultural-area-used-for-organic' -> ('agricultural-area-used-for-organic', (2, 0))
    """
    # Pattern: base-name-TIMESTAMP (10 digits, value >= 1000000000)
    timestamp_match = re.search(r"-(\d{10,})$", obj_id)
    if timestamp_match:
        timestamp = int(timestamp_match.group(1))
        if timestamp >= TIMESTAMP_THRESHOLD:
            base = obj_id[: timestamp_match.start()]
            return base, (1, timestamp)

    # Pattern: base-name.N (draft)
    draft_match = re.search(r"\.(\d+)$", obj_id)
    if draft_match:
        n = int(draft_match.group(1))
        base = obj_id[: draft_match.start()]
        return base, (0, n)

    # Pattern: copy_of_base-name (draft)
    if obj_id.startswith("copy_of_"):
        base = obj_id[8:]  # len('copy_of_') = 8
        return base, (0, 1)

    # Plain name = published (newest in chain)
    return obj_id, (2, 0)


def link_indicator_versions(context):
    """Link indicator versions by populating copied_from and copied_to fields.

    This upgrade step:
    1. Queries all ims_indicator objects from the catalog
    2. Groups them by base name (without version suffixes)
    3. Sorts each group chronologically
    4. Links adjacent versions via copied_from/copied_to fields
    """
    catalog = getToolByName(context, "portal_catalog")

    # Query all indicators
    brains = catalog.searchResults(portal_type="ims_indicator")
    logger.info("Found %d indicators to process", len(brains))

    # Group by base name
    groups = defaultdict(list)
    for brain in brains:
        obj_id = brain.getId
        base_name, sort_key = get_base_name_and_sort_key(obj_id)
        groups[base_name].append((sort_key, brain))

    # Track statistics
    linked_count = 0
    skipped_count = 0
    error_count = 0

    # Process each group
    for base_name, versions in groups.items():
        if len(versions) < 2:
            # Single version, no linking needed
            continue

        # Sort by sort_key (chronologically: drafts < archived < published)
        versions.sort(key=lambda x: x[0])

        # Get objects and link them
        objects = []
        for sort_key, brain in versions:
            try:
                obj = brain.getObject()
                objects.append(obj)
            except Exception as e:
                logger.error("Failed to get object for %s: %s", brain.getPath(), str(e))
                error_count += 1

        if len(objects) < 2:
            continue

        logger.info(
            "Linking %d versions for base name '%s': %s",
            len(objects),
            base_name,
            [obj.getId() for obj in objects],
        )

        # Link adjacent versions
        for i in range(len(objects)):
            obj = objects[i]
            modified = False

            try:
                # Link to previous version (older)
                if i > 0:
                    prev_obj = objects[i - 1]
                    current_copied_from = getattr(obj, "copied_from", None)
                    expected_uid = IUUID(prev_obj)

                    if not current_copied_from:
                        obj.copied_from = expected_uid
                        modified = True
                        logger.debug(
                            "Set %s.copied_from = %s (%s)",
                            obj.getId(),
                            expected_uid,
                            prev_obj.getId(),
                        )

                # Link to next version (newer)
                if i < len(objects) - 1:
                    next_obj = objects[i + 1]
                    current_copied_to = getattr(obj, "copied_to", None)
                    expected_uid = IUUID(next_obj)

                    if not current_copied_to:
                        obj.copied_to = expected_uid
                        modified = True
                        logger.debug(
                            "Set %s.copied_to = %s (%s)",
                            obj.getId(),
                            expected_uid,
                            next_obj.getId(),
                        )

                if modified:
                    # Reindex the object to update catalog
                    obj.reindexObject(idxs=["copied_from", "copied_to"])
                    linked_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                logger.error("Failed to link %s: %s", obj.getId(), str(e))
                error_count += 1

    logger.info(
        "Indicator version linking complete: %d linked, %d skipped (already linked), %d errors",
        linked_count,
        skipped_count,
        error_count,
    )
