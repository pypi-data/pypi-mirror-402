from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Union, List


@dataclass
class SkillSandboxResult:
    success: bool
    output: str


class SkillSandbox(ABC):
    @abstractmethod
    def run_code(self,
                 python_code: Union[str, List[str]],
                 requirements: List[str] = None
                 ) -> List[SkillSandboxResult]:
        pass

    @abstractmethod
    def exec_command(self,
                     shell_command: Union[str, List[str]],
                     requirements: List[str] = None
                     ) -> List[SkillSandboxResult]:
        pass

    @abstractmethod
    def upload_file(self,
                    file_name: str,
                    local_file_path: str = "",
                    sandbox_file_path: str = ""
                    ):
        pass

    @abstractmethod
    def upload_work_dir(self):
        pass

    @abstractmethod
    def upload_dir(self,
                   local_dir_path: str,
                   sandbox_dir_path: str,
                   ):
        pass

    @abstractmethod
    def destroy(self):
        pass