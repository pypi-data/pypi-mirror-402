import logging
import os
import uuid
import zipfile

from pathlib import Path
from typing import Union, List

from xgse.sandbox.sandbox_base import SkillSandbox, SkillSandboxResult


class E2BSkillSandbox(SkillSandbox):
    def __init__(self,
                 host_work_dir:str,
                 sandbox_work_dir:str,
                 timeout: int = 300
                 ):

        from e2b_code_interpreter import Sandbox as E2BSandbox

        self.host_work_dir = host_work_dir
        self.sandbox_work_dir = sandbox_work_dir

        self.sandbox: E2BSandbox = E2BSandbox.create(timeout=timeout)
        self.sandbox.files.make_dir(path=sandbox_work_dir)

        self.code_context = self.sandbox.create_code_context(cwd=sandbox_work_dir ,language='python')

        logging.info(f"🛠️ E2BSkillSandBox init: Create sandbox id='{self.sandbox.sandbox_id}' , workspace='{sandbox_work_dir}'")


    def destroy(self):
        try:
            if self.sandbox:
                self.sandbox.kill()
                logging.info(f"E2BSkillSandBox destroy: Kill sandbox id='{self.sandbox.sandbox_id}'")
        except Exception as e:
            logging.error(f"E2BSkillSandBox destroy: Error {e}")


    def upload_file(self,
                    file_name: str,
                    local_file_path: str = "",
                    sandbox_file_path: str = ""
                    ):
        try:
            local_file_path = Path(self.host_work_dir) / local_file_path.lstrip("/")
            sandbox_file_path = Path(self.sandbox_work_dir) / sandbox_file_path.lstrip("/")

            local_full_path = str(local_file_path / file_name)
            sandbox_full_path = str(sandbox_file_path / file_name)

            file_size = os.path.getsize(local_full_path)
            logging.info(f"E2BSkillSandBox upload_file: Begin upload '{local_full_path}' {file_size} bytes"
                         f" to sandbox '{sandbox_full_path}'")

            with open(local_full_path, "rb") as file:
                self.sandbox.files.write(sandbox_full_path, file)
            logging.info(f"E2BSkillSandBox upload_file: Upload '{local_full_path}' to sandbox '{sandbox_full_path}' completed")
        except Exception as e:
            logging.error(f"E2BSkillSandBox upload_file: Error {e}")
            raise e


    def upload_work_dir(self):
        self.upload_dir(local_dir_path="", sandbox_dir_path="")


    def upload_dir(self,
                   local_dir_path: str,
                   sandbox_dir_path: str,
                   ):
        zip_file_path = None
        try:
            local_dir_path = Path(self.host_work_dir) / local_dir_path.lstrip("/")
            sandbox_dir_path = Path(self.sandbox_work_dir) / sandbox_dir_path.lstrip("/")
            logging.info(f"E2BSkillSandBox upload_dir: Begin upload local '{local_dir_path}' to sandbox '{sandbox_dir_path}'")

            zip_file_name = f"skills_temp_{uuid.uuid4()}.zip"
            zip_temp_file_path = Path(self.host_work_dir).parent / zip_file_name

            with zipfile.ZipFile(zip_temp_file_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zip_file:
                for root, dirs, files in os.walk(local_dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_file = os.path.relpath(path=file_path, start=local_dir_path)
                        zip_file.write(file_path, arc_file)
            logging.info(f"E2BSkillSandBox upload_dir: Compress dir '{local_dir_path}' to '{zip_temp_file_path}' completed")

            zip_file_path = Path(self.host_work_dir) / zip_file_name
            os.rename(zip_temp_file_path, zip_file_path)
            self.upload_file(file_name=zip_file_name)

            sandbox_zip_path = str(Path(sandbox_dir_path) / zip_file_name)
            unzip_command = f"unzip -o -q '{sandbox_zip_path}' -d '{sandbox_dir_path}'"
            self.sandbox.commands.run(unzip_command)
            logging.info(f"E2BSkillSandBox upload_dir: Sandbox unzip '{sandbox_zip_path}' to '{sandbox_zip_path}' completed")
                
            rm_command = f"rm '{sandbox_zip_path}'"
            self.sandbox.commands.run(rm_command)
            
            logging.info(f"E2BSkillSandBox upload_dir: Upload local '{local_dir_path}' to sandbox '{sandbox_dir_path}' succeed")
        except Exception as e:
            logging.error(f"E2BSkillSandBox upload_dir: Error {e}")
            raise e
        finally:
            if os.path.exists(zip_file_path):
                os.unlink(zip_file_path)


    def install_requirements(self, requirements: list[str] | None):
        if requirements is None or len(requirements) == 0:
            logging.warning("E2BSkillSandBox install_requirements: requirements is empty !")

        requirements_file = Path(self.sandbox_work_dir) / f"{uuid.uuid4()}/requirements.txt"
        self.sandbox.files.write(str(requirements_file), '\n'.join(requirements))

        logging.info("-" * 10 + f"E2BSkillSandBox[{self.sandbox.sandbox_id}]: PIP INSTALL BEGIN" + "-" * 10)

        result_requirements = self.sandbox.commands.run(f'pip install -r {requirements_file}')

        logging.info("\n" + result_requirements.stdout)
        logging.info("-" * 10 + f"E2BSkillSandBox[{self.sandbox.sandbox_id}]: PIP INSTALL END" + "-" * 10)


    def run_code(self,
                 python_code: Union[str, List[str]],
                 requirements: List[str] = None
                 ) -> List[SkillSandboxResult]:
        from e2b.exceptions import SandboxException
        results = []

        self.install_requirements(requirements)

        if isinstance(python_code, str):
            python_code = [python_code]

        logging.info("-" * 10 + f"E2BSkillSandBox[{self.sandbox.sandbox_id}]: RUN CODE" + "-" * 10)
        for code in python_code:
            logging.info(code)

            code_result = self.sandbox.run_code(code=code, context=self.code_context)
            success  = True if code_result.error is None else False
            output = code_result.text if success else code_result.error.value
            results.append({
                'output': output,
                'success': success
            })

            logging.info(f"E2BSkillSandBox run_code: result='{output}'")
            if not success:
                # raise Exception for keeping up with 'exec_command' function
                raise SandboxException(f"E2BSkillSandBox run_code: Error {output}")

        return results


    def exec_command(self,
                     shell_command: Union[str, List[str]],
                     requirements: List[str] = None
                     ) -> List[SkillSandboxResult]:
        results = []

        self.install_requirements(requirements)

        if isinstance(shell_command, str):
            shell_command = [shell_command]

        logging.info("-" * 10 + f"E2BSkillSandBox[{self.sandbox.sandbox_id}]: EXEC COMMAND" + "-" * 10)
        for command in shell_command:
            logging.info(command)

            shell_result =  self.sandbox.commands.run(command)
            success  = True if shell_result.exit_code == 0 else False
            output = shell_result.stdout if success else shell_result.stderr
            results.append({
                'output': output,
                'success': success
            })

            logging.info(f"E2BSkillSandBox exec_command: result='{output}'")

        return results




if __name__ == '__main__':
    from xgse.utils.setup_env import setup_logging

    setup_logging()

    def main():
        run_path = Path(__file__).parent.resolve()
        project_path = run_path.parents[1]
        skill_work_dir = str(project_path / 'skill_workspace')
        skill_sandbox = E2BSkillSandbox(host_work_dir=skill_work_dir,
                                        sandbox_work_dir="/skill_workspace",
                                        timeout=300)

        try:
            skill_sandbox.upload_work_dir()

            test_run_code(skill_sandbox)

            #exec_command(skill_sandbox)
        finally:
            skill_sandbox.destroy()


    def test_exec_command(skill_sandbox: SkillSandbox):
        commands = ["pwd",
                    "eco sharky"]
        results = skill_sandbox.exec_command(commands)
        print(f"Sandbox exec_command: {results}")


    def test_run_code(skill_sandbox: SkillSandbox):
        code = """
from typing import Annotated, Optional
from pydantic import Field
def getHostFaultCause(
    faultCode: Annotated[str, Field(description="Fault Code")],
    severity: Annotated[int, Field(default=2, description="Fault Level，1-5，default: 1")]
    ):
    print(f"getHostFaultCause: faultCode={faultCode}, severity={severity}")
    faultCause = ""
    if (faultCode == 'F02'):
        faultCause = "Host Disk Fault，Change Disk"
    else:
        faultCause = f"Unknown Fault，FaultCode'{faultCode}'"        
    return faultCause

getHostFaultCause('F02', 2)    
    """
        requirements = ["pydantic", "typing"]
        results = skill_sandbox.run_code(python_code=code, requirements=requirements)

        print(f"Sandbox run getHostFaultCause result is {results}")


    main()