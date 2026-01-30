"""Upgrade step to rename 'archived' transition to 'archive'"""

import logging

from Products.CMFCore.utils import getToolByName
from Products.DCWorkflow.Guard import Guard

logger = logging.getLogger("eea.dexterity.indicators")


def rename_archived_transition(context):
    """Rename the 'archived' transition to 'archive' in ims_indicator_workflow.

    The state 'archived' remains unchanged - only the transition name changes
    to follow Plone workflow naming conventions (verb form for transitions).
    """
    portal_workflow = getToolByName(context, "portal_workflow")

    workflow_id = "ims_indicator_workflow"
    if workflow_id not in portal_workflow:
        logger.warning("Workflow %s not found", workflow_id)
        return

    workflow = portal_workflow[workflow_id]

    # Check if the old transition exists and new one doesn't
    if "archived" in workflow.transitions and "archive" not in workflow.transitions:
        # Get the old transition's properties
        old_transition = workflow.transitions["archived"]
        old_guard = old_transition.guard

        # Create the new transition with the same properties
        workflow.transitions.addTransition("archive")
        new_transition = workflow.transitions["archive"]
        new_transition.new_state_id = "archived"  # State name stays the same
        new_transition.title = "Archive"
        new_transition.description = old_transition.description
        new_transition.actbox_name = "Archive"
        new_transition.actbox_category = "workflow"
        new_transition.actbox_url = old_transition.actbox_url

        # Copy the guard from old transition
        if old_guard:
            guard = Guard()
            guard.permissions = old_guard.permissions
            guard.roles = old_guard.roles
            guard.groups = old_guard.groups
            guard.expr = old_guard.expr
            new_transition.guard = guard

        # Delete the old transition
        workflow.transitions.deleteTransitions(["archived"])

        logger.info("Renamed 'archived' transition to 'archive'")

    elif "archive" in workflow.transitions:
        logger.info("Transition 'archive' already exists, skipping rename")
    else:
        logger.warning("Transition 'archived' not found in workflow")

    # Update exit-transitions in published and retracted states
    for state_id in ["published", "retracted"]:
        if state_id in workflow.states:
            state = workflow.states[state_id]
            transitions = list(state.transitions)

            # Replace 'archived' with 'archive' in transitions list
            if "archived" in transitions:
                transitions.remove("archived")
                if "archive" not in transitions:
                    transitions.append("archive")
                state.transitions = tuple(transitions)
                logger.info(
                    "Updated exit-transitions for %s state: replaced 'archived' with 'archive'",
                    state_id,
                )

    # Update the workflow role mappings
    workflow.updateRoleMappingsFor(context)

    logger.info("Workflow transition rename completed successfully")
