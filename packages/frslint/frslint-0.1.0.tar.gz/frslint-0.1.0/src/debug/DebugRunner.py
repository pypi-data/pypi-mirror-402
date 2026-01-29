from typing import Dict, List

from debug.Action import Action
from debug.Freeswitch import Freeswitch
from debug.FreeswitchLoader import FreeswitchLoader
from debug.MetaAction import MetaAction
from log.Loggable import Loggable


class DebugRunner(Loggable):
    def __init__(self, file_path: str, verbose: bool = False):
        super().__init__(verbose=verbose)
        loader = FreeswitchLoader(verbose=verbose)
        self.freeswitch: Freeswitch = loader.load(file_path)

    def run(self, context_name: str, channel_variables: Dict[str, str]):
        print("-" * 60)
        if context_name not in self.freeswitch.context_instructions:
            raise ValueError(f"Context {context_name} not found")

        action_set: List[Action] = []
        context = self.freeswitch.context_instructions[context_name]
        for extension in context.extensions:
            if self.verbose:
                action_set.append(MetaAction("DEBUG", f"running extension: {extension.name}", "cyan"))

            at_least_one_condition_true = False
            for condition in extension.conditions:
                if self.verbose:
                    action_set.append(
                        MetaAction("DEBUG", f"evaluating condition: {condition.field} {condition.expression}", "cyan")
                    )

                value, local_variables = condition.evaluate(channel_variables, self.freeswitch)
                action_set.append(
                    MetaAction(
                        "> Condition match",
                        f"{condition.field} {'~' if value else '!~'} {condition.expression}",
                        "green" if value else "red",
                    )
                )
                if value:
                    at_least_one_condition_true = True
                    for action in condition.actions:
                        action_set.append(
                            action.var_evaluated({**local_variables, **channel_variables}, self.freeswitch.variables)
                        )
                    if condition.do_break == "on-true":
                        if self.verbose:
                            action_set.append(
                                MetaAction(
                                    "DEBUG",
                                    f"extension: {extension.name} condition: {condition.field} {condition.expression} breaking on true",
                                    "cyan",
                                )
                            )
                        break
                else:
                    for anti_action in condition.anti_actions:
                        action_set.append(
                            anti_action.var_evaluated(
                                {**local_variables, **channel_variables}, self.freeswitch.variables
                            )
                        )
                    if condition.do_break == "on-false":
                        if self.verbose:
                            action_set.append(
                                MetaAction(
                                    "DEBUG",
                                    f"extension: {extension.name} condition: {condition.field} {condition.expression} breaking on false",
                                    "cyan",
                                )
                            )
                        break
                if condition.do_break == "always":
                    if self.verbose:
                        action_set.append(
                            MetaAction(
                                "DEBUG",
                                f"extension: {extension.name} condition: {condition.field} {condition.expression} breaking on always",
                                "cyan",
                            )
                        )
                    break
                if condition.do_break == "never":
                    continue

            if not extension.do_continue and at_least_one_condition_true:
                if self.verbose:
                    action_set.append(
                        MetaAction("DEBUG", f"extension: {extension.name} breaking on do-continue false", "cyan")
                    )
                break

        for action in action_set:
            print(action.to_string())
        # TODO: follow transfers
        exit()
