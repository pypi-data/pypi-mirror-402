"""Upgrade step to add archived state to workflow without web changes"""

import logging

from Products.CMFCore.utils import getToolByName
from Products.DCWorkflow.Guard import Guard

logger = logging.getLogger("eea.dexterity.indicators")


def update_workflow_for_archived_state(context):
    """Update workflow to ensure archived state is available
    without overwriting web changes
    """
    portal_workflow = getToolByName(context, "portal_workflow")

    workflow_id = "ims_indicator_workflow"
    if workflow_id not in portal_workflow:
        logger.warning("Workflow %s not found", workflow_id)
        return

    workflow = portal_workflow[workflow_id]

    # Check if archived state already exists
    if "archived" in workflow.states:
        logger.info("Archived state already exists in workflow")
    else:
        # Add the archived state programmatically
        workflow.states.addState("archived")
        state = workflow.states["archived"]
        state.title = "Archived"
        state.description = "This item has been archived"

        # Set permissions for archived state
        state.setPermission("Access contents information", 0, ["Manager", "Reader"])
        state.setPermission("Modify portal content", 0, ["Manager"])
        state.setPermission("View", 0, ["Manager", "Reader"])
        state.setPermission("eea.annotator: Edit", 0, ["Manager"])

        # Set group mappings
        state.group_roles = {
            "WebReviewers": ["Reader"],
            "indicatorsCopyEditors": ["Reader"],
        }

        logger.info("Added archived state to workflow")

    # Check if transition to archived exists from published and retracted states
    if "archived" not in workflow.transitions:
        workflow.transitions.addTransition("archived")
        transition = workflow.transitions["archived"]
        transition.new_state_id = "archived"
        transition.title = "Archived"
        transition.description = "Mark this content to be archived."
        transition.actbox_name = "Archived"
        transition.actbox_category = "workflow"

        # Create and set guard - same as markForDeletion transition
        guard = Guard()
        guard.permissions = ()
        guard.roles = ()
        guard.groups = ("indicatorsCopyEditors", "WebReviewers")
        transition.guard = guard

        logger.info("Added archived transition to workflow")

    # Ensure published and retracted states have exit transition to archived
    for state_id in ["published", "retracted"]:
        if state_id in workflow.states:
            state = workflow.states[state_id]
            transitions = list(state.transitions)
            if "archived" not in transitions:
                transitions.append("archived")
                state.transitions = tuple(transitions)
                logger.info("Added archived transition to %s state", state_id)

    # Add enable transition from archived state if not exists
    if "archived" in workflow.states:
        state = workflow.states["archived"]
        transitions = list(state.transitions)
        if "enable" not in transitions:
            transitions.append("enable")
            state.transitions = tuple(transitions)
            logger.info("Added enable transition from archived state")

    # Update the workflow
    workflow.updateRoleMappingsFor(context)

    logger.info("Workflow updated successfully for archived state")
