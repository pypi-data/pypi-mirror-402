from typing import Literal

from xgse.sandbox.sandbox_base import SkillSandbox
from xgse.sandbox.e2b_sandbox import E2BSkillSandbox

def create_skill_sandbox(host_work_dir:str,
                         sandbox_work_dir:str,
                         sandbox_type: Literal["e2b"] = "e2b",
                         timeout: int = 300,
                         ) -> SkillSandbox|None:
    sandbox = None
    if sandbox_type == "e2b":
        sandbox = E2BSkillSandbox(host_work_dir = host_work_dir,
                                  sandbox_work_dir = sandbox_work_dir,
                                  timeout = timeout
                                  )
    return sandbox

