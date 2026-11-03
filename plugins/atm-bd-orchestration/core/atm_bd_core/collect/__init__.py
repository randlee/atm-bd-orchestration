"""Read a phase snapshot without making orchestration decisions."""

from atm_bd_types import CollectError, FactKind, PhaseFacts, TaskFact

from . import atm, beads, git, provider, reported


def collect(phase, phase_file, ports, now, state_dir):
    errors = []

    def take(result):
        value, error = result
        if error is not None:
            errors.append(error)
        return value

    bead_list = take(beads.beads(ports.cache, phase))
    ready = take(beads.ready(ports.cache, phase))
    raw_tasks = take(atm.tasks(ports.runner))
    if raw_tasks is not None and bead_list is not None:
        ids = {bead.id for bead in bead_list}
        tasks = [TaskFact(task.task_id, task.assignee, task.state, task.task_id)
                 for task in raw_tasks if task.task_id in ids]
    else:
        tasks = None
        if raw_tasks is not None:
            errors.append(CollectError(FactKind.TASKS, [], "beads unavailable", "Restore the beads cache."))
    if tasks is None:
        events = None
        errors.append(CollectError(FactKind.TASK_EVENTS, [], "tasks unavailable", "Restore the task read."))
    else:
        events = take(atm.task_events(ports.runner, [task.task_id for task in tasks]))
    keys = take(reported.reported_keys(state_dir))
    branches = take(git.remote_branches(ports.runner))
    stack = None
    if bead_list is None:
        errors.append(CollectError(FactKind.STACK, [], "beads unavailable", "Restore the beads cache."))
    else:
        try:
            from atm_bd_types._core import stack_of
            stack = take(beads.stack(bead_list, phase_file, stack_of))
        except ImportError as error:
            errors.append(CollectError(FactKind.STACK, [], str(error), "Install the framework stack accessor."))
    if stack is None:
        ancestry = None
        checks = None
        bases = None
        for kind in (FactKind.ANCESTRY, FactKind.TOP_CHECKS, FactKind.PR_BASES):
            errors.append(CollectError(kind, [], "stack unavailable", "Restore the stack read."))
    else:
        layers = stack.stack.layers
        refs = [stack.trunk, *(layer.branch for layer in layers)]
        ancestry = take(git.ancestry(ports.runner, [(f"origin/{a}", f"origin/{b}") for a, b in zip(refs, refs[1:])]))
        selected, issue = provider.resolve_provider(ports.runner, phase_file.key("provider"))
        if issue:
            checks = bases = None
            for kind in (FactKind.TOP_CHECKS, FactKind.PR_BASES):
                errors.append(CollectError(kind, ["git", "remote", "get-url", "origin"], issue,
                                           "Set provider in the phase configuration."))
        else:
            bases = take(provider.pr_bases(ports.runner, selected, layers))
            if layers:
                checks = take(provider.top_checks(ports.runner, selected, layers[-1]))
            else:
                checks = None
                errors.append(CollectError(FactKind.TOP_CHECKS, [], "stack has no layers", "Record a stack layer."))
    return PhaseFacts(phase, now, phase_file, tasks, events, keys, branches, ancestry,
                      bead_list, ready, stack, checks, bases, errors)
