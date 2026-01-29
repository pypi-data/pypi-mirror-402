import platform
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from pyligent.core import Validator
from pyligent.core.action import DoneAction, NodeAction
from pyligent.core.path import PathContext
from pyligent.core.validator import HandlerResult


class ValidationExecutionError(Exception):
    pass


class BlocksworldValidator(Validator):
    def __init__(
        self,
        target_plans: Dict[str, str],
        target_instances: Dict[str, str],
        plan_buf_path: Path,
        instances_path: Path,
        val_path: Path,
        domain_path: Path,
    ):
        super().__init__([self._validate_node_action, self._validate_done_action])
        self.target_plans = target_plans
        self.target_instances = target_instances
        self.plan_buf_path = plan_buf_path
        self.instances_path = instances_path
        if "Windows" in platform.system():
            self.val_path = val_path / "bin/VAL.exe"
        elif "Linux" in platform.system():
            self.val_path = val_path / "validate"
        elif "Darwin" in platform.system():
            self.val_path = val_path / "bin/MacOSExecutables/vadilate"
        else:
            raise ValueError(f"Unexpected OS: {platform.system()}")
        self.domain_path = domain_path

        self.encode_object = {
            "a": "red",
            "b": "blue",
            "c": "orange",
            "d": "yellow",
            "e": "white",
            "f": "magenta",
            "g": "black",
            "h": "cyan",
            "i": "green",
            "j": "violet",
            "k": "silver",
            "l": "gold",
        }

        self.decode_object = {v: k for k, v in self.encode_object.items()}

    @staticmethod
    def parse_actions(
        plan: Union[NodeAction, DoneAction, PathContext, str],
        decode_object: Optional[Dict[str, str]] = None,
    ) -> str:
        plan = str(plan)
        regex = r"\((?:pick-up|put-down|stack|unstack) [\w ]+\)"
        matches = re.findall(regex, plan)

        if decode_object:
            decoded_matches = []
            for action in matches:
                decoded_action = []
                for token in action[1:-1].split():
                    decoded_token = decode_object.get(token, token)
                    decoded_action.append(decoded_token)
                decoded_matches.append("(" + " ".join(decoded_action) + ")")
            matches = decoded_matches

        return "\n".join(matches)

    def _val_call(
        self, plan_path: Path, instance_path: Path, decode: str = "CP866"
    ) -> Tuple[str, str]:
        cmd = f"{self.val_path} -v {self.domain_path} {instance_path} {plan_path}"
        result = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, error = result.communicate()
        output = output.decode(decode)
        error = error.decode(decode)
        return output, error

    def _validate_plan(
        self, plan: str, task: str, check_success: bool = False, decode: str = "CP866"
    ) -> HandlerResult:
        with open(self.plan_buf_path, "w") as f:
            f.write(plan)
        instance_num = self.target_instances[task]
        instance_path = self.instances_path / f"instance-{instance_num}.pddl"
        validation, error = self._val_call(self.plan_buf_path, instance_path)
        if len(error):
            print("Validation error occured:\n", error)
            print(f"[Instance Number {instance_num}] Proposed plan:\n", plan)
            return HandlerResult(False, error)
        if "Plan failed to execute" in validation:
            return HandlerResult(False, "plan failed to execute")
        elif "Plan invalid" in validation and check_success:
            return HandlerResult(False, "plan valid but not successful (not done)")
        else:
            return HandlerResult(True)

    def _validate_node_action(
        self,
        action: NodeAction,
        context: PathContext,
    ) -> HandlerResult:
        """
        Validate a node by ensuring all preconditions are met.
        """
        text = str(context) + str(action)
        actions = self.parse_actions(text, decode_object=self.decode_object)
        return self._validate_plan(actions, context.nodes[0].action.text)

    def _validate_done_action(
        self,
        action: DoneAction,
        context: PathContext,
    ) -> HandlerResult:
        """
        Validate a node by ensuring that plan is successful.
        """
        text = str(action)
        actions = self.parse_actions(text, decode_object=self.decode_object)
        return self._validate_plan(
            actions, context.nodes[0].action.text, check_success=True
        )
