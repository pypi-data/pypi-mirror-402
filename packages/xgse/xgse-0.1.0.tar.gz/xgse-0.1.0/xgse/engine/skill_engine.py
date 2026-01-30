import json
import logging
import os.path
import shlex
import shutil
import subprocess
import sys

from pathlib import Path
from typing import Any, Dict, List, Union

from xgse.utils.llm_client import LLMClient, LLMConfig

from xgse.engine.loader import load_skills
from xgse.engine.retrieve import create_retriever
from xgse.engine.schema import ExecutionResult, SkillContext, SkillSchema
from xgse.engine.prompts import (
    PROMPT_SKILL_PLAN,
    PROMPT_SKILL_TASKS,
    PROMPT_TASKS_IMPLEMENTATION,
    SCRIPTS_IMPLEMENTATION_FORMAT
)
from xgse.utils.utils import (
    copy_with_exec_if_script,
    extract_cmd_from_code_blocks,
    extract_implementation,
    extract_packages_from_code_blocks,
    find_skill_dir,
    install_package,
    str_to_md5,
    valid_repo_id
)

from xgse.sandbox.sandbox_base import SkillSandbox
from xgse.sandbox.sandbox_factory import create_skill_sandbox

class XGASkillEngine:
    """
    LLM Agent with progressive skill loading mechanism.

    Implements a multi-level progressive context loading and processing mechanism:
        1. Level 1 (Metadata): Load all skill names and descriptions
        2. Level 2 (Retrieval): Retrieve and load SKILL.md when relevant with the query
        3. Level 3 (Resources): Load additional files (references, scripts, resources) only when referenced in SKILL.md
        4. Level 4 (Analysis and Execution): Analyze the loaded skill context and execute scripts as needed
    """

    def __init__(self,
                 skills: Union[str, List[str]],
                 work_dir: str = None,
                 use_sandbox: bool = True,
                 **kwargs
                 ):
        """
        Initialize Agent Skills.

        Args:
            skills: Path(s) to skill directories or the root path of skill directories
            work_dir: Working directory.
            use_sandbox: Whether to use sandbox environment for script execution.
                If True, scripts will be executed in the sandbox environment.
                If False, scripts will be executed directly in the local environment.
        """

        self.work_dir: Path = Path(work_dir) if work_dir else Path.cwd()
        os.makedirs(self.work_dir, exist_ok=True)

        self.use_sandbox: bool = use_sandbox
        self.kwargs = kwargs

        if not self.use_sandbox:
            logging.warning('XGASkillEngine: Sandbox is not enable, skill scripts will be executed in local environment.'
                            'Make sure to trust the skills being executed!')

        # Preprocess and Load skills
        skills = self._pre_process_skills(skills=skills)
        self.all_skills: Dict[str, SkillSchema] = load_skills(skills=skills)
        logging.info(f'XGASkillEngine: Loaded {len(self.all_skills)} skills from {skills}')

        # Initialize skill retriever
        self.retriever = create_retriever(skills=self.all_skills)

        self.llm = LLMClient(LLMConfig(stream=True))

        if self.use_sandbox:
            self.work_dir_in_sandbox = os.getenv('SANDBOX_WORK_DIR', "/skill_workspace")
            env_sandbox_type = os.getenv('SANDBOX_TYPE', "e2b")
            env_sandbox_timeout = int(os.getenv('SANDBOX_TIMEOUT', 300))
            self.sandbox:SkillSandbox  = create_skill_sandbox(host_work_dir=work_dir,
                                                              sandbox_work_dir=self.work_dir_in_sandbox,
                                                              sandbox_type=env_sandbox_type,
                                                              timeout=env_sandbox_timeout,
                                                              )
            self.sandbox.upload_work_dir()

        logging.info(f"🛠️ XGASkillEngin init: Skill engine initialized successfully !")


    def destroy(self):
        if hasattr(self, 'sandbox') and self.sandbox:
            self.sandbox.destroy()
            self.sandbox = None


    def _pre_process_skills(self,
                            skills: Union[str, List[str],
                            List[SkillSchema]]
                            ) -> Union[str, List[str]]:
        """
        Preprocess skills by copying them to the working directory.

        Args:
            skills: Path(s) to skill directories,
                the root path of skill directories, list of SkillSchema, or skill IDs on the hub

        Returns:
            Processed skills in the working directory.
        """

        results: Union[str, List[str]] = []

        if isinstance(skills, str):
            skills = [skills]

        if skills is None or len(skills) == 0:
            return results

        skill_paths: List[str] = find_skill_dir(skills)

        for skill_path in skill_paths:
            path_in_workdir = os.path.join(str(self.work_dir), Path(skill_path).name)
            
            if os.path.exists(path_in_workdir):
                shutil.rmtree(path_in_workdir, ignore_errors=True)
                
            os.makedirs(path_in_workdir, exist_ok=True)
            shutil.copytree(skill_path, 
                            path_in_workdir,
                            copy_function=copy_with_exec_if_script,
                            dirs_exist_ok=True
                            )
            results.append(path_in_workdir)

        return results


    def run(self, query: str) -> str:
        """
        Run the agent skill with the given query.

        Args:
            query: User query string

        Returns:
            Agent response string
        """
        logging.info(f'XGASkillEngin run: Received user query: {query}, starting skill retrieval...')

        relevant_skills = self.retriever.retrieve(
            query=query,
            method='semantic',
            top_k=5,
        )
        logging.info(f'XGASkillEngin run: Retrieve relevant {len(relevant_skills)} skills for query')

        if not relevant_skills:
            logging.warning('XGASkillEngin run: No relevant skills found')
            return "I can't find any relevant skills for your query. Could you please rephrase or provide more details?"

        # Use the most relevant skill
        # TODO: Support multiple skills collaboration
        top_skill_key, top_skill, score = relevant_skills[0]
        logging.info(f"XGASkillEngin run: USING SKILL '{top_skill.name}' SCORE: {score:.2f}")

        skill: SkillSchema = top_skill
        return self.run_skill(query=query, skill=skill)


    def run_skill(self,
                  query: str,
                  skill: SkillSchema
                  ) -> str:
        skill_context: SkillContext = SkillContext(skill=skill, root_path=self.work_dir)
        
        skill_name = skill.name
        logging.info(f"=" * 10 + f"XGASkillEngine: SKILL [{skill.name}]  START RUNNING..." + "=" * 10)
        skill_md_context: str = '\n\n<!-- SKILL_MD_CONTEXT -->\n' + skill_context.skill.content.strip()

        reference_context: str = '\n\n<!-- REFERENCE_CONTEXT -->\n' + '\n'.join(
            [
                json.dumps(
                    {
                        'name': ref.get('name', ''),
                        'path': ref.get('path', ''),
                        'description': ref.get('description', ''),
                    },
                    ensure_ascii=False) for ref in skill_context.references
            ])
        script_context: str = '\n\n<!-- SCRIPT_CONTEXT -->\n' + '\n'.join([
            json.dumps(
                {
                    'name': script.get('name', ''),
                    'path': script.get('path', ''),
                    'description': script.get('description', ''),
                },
                ensure_ascii=False) for script in skill_context.scripts
        ])
        resource_context: str = '\n\n<!-- RESOURCE_CONTEXT -->\n' + '\n'.join([
            json.dumps(
                {
                    'name': res.get('name', ''),
                    'path': res.get('path', ''),
                    'description': res.get('description', ''),
                },
                ensure_ascii=False) for res in skill_context.resources
        ])

        # PLAN: Analyse the SKILL.md, references, and scripts.
        logging.info("-" * 10 + f"XGASkillEngine: LLM SKILL PLAN BEGIN" + "-" * 10)
        prompt_skill_plan: str = PROMPT_SKILL_PLAN.format(
            query=query,
            skill_md_context=skill_md_context,
            reference_context=reference_context,
            script_context=script_context,
            resource_context=resource_context,
        )

        logging.debug("\n" + prompt_skill_plan)
        logging.debug("=" * 40)

        response_skill_plan = self._call_llm(
            user_prompt=prompt_skill_plan
        )
        skill_context.spec.plan = response_skill_plan

        logging.info("\n" + response_skill_plan)
        logging.info("-" * 10 + f"XGASkillEngine: LLM SKILL PLAN END" + "-" * 10)

        # TASKS: Get solutions and tasks based on analysis.
        logging.info("-" * 10 + f"XGASkillEngine: LLM SKILL TASK BEGIN" + "-" * 10)

        prompt_skill_tasks: str = PROMPT_SKILL_TASKS.format(
            skill_plan_context=response_skill_plan, )
        response_skill_tasks = self._call_llm(
            user_prompt=prompt_skill_tasks
        )
        skill_context.spec.tasks = response_skill_tasks

        logging.info("\n" + response_skill_tasks)
        logging.info("-" * 10 + f"XGASkillEngine: LLM SKILL TASK END" + "-" * 10)

        # IMPLEMENTATION & EXECUTION
        script_contents: str = '\n\n'.join([
            '<!-- ' + script.get('path', '') + ' -->\n'
            + script.get('content', '') for script in skill_context.scripts
            if script.get('name', '') in response_skill_tasks
        ])
        reference_contents: str = '\n\n'.join([
            '<!-- ' + ref.get('path', '') + ' -->\n' + ref.get('content', '')
            for ref in skill_context.references
            if ref.get('name', '') in response_skill_tasks
        ])
        resource_contents: str = '\n\n'.join([
            '<!-- ' + res.get('path', '') + ' -->\n' + res.get('content', '')
            for res in skill_context.resources
            if res.get('name', '') in response_skill_tasks
        ])

        logging.info("-" * 10 + f"XGASkillEngine: LLM TASK IMPLEMENTATION BEGIN" + "-" * 10)

        prompt_tasks_implementation: str = PROMPT_TASKS_IMPLEMENTATION.format(
            script_contents=script_contents,
            reference_contents=reference_contents,
            resource_contents=resource_contents,
            skill_tasks_context=response_skill_tasks,
            scripts_implementation_format=SCRIPTS_IMPLEMENTATION_FORMAT,
        )

        logging.debug("\n" + prompt_tasks_implementation)
        logging.debug("=" * 40)

        response_tasks_implementation = self._call_llm(
            user_prompt=prompt_tasks_implementation
        )
        skill_context.spec.implementation = response_tasks_implementation

        logging.info("\n" + response_tasks_implementation)
        logging.info("-" * 10 + f"XGASkillEngine: LLM TASK IMPLEMENTATION END" + "-" * 10)

        # Dump the spec files
        spec_output_path = skill_context.spec.dump(output_dir=str(self.work_dir))
        logging.info(f'XGASkillEngine run_skill[{skill_name}]: Spec files dumped to: {spec_output_path}')

        # Extract IMPLEMENTATION content and determine execution scenario
        _, implementation_content = extract_implementation(content=response_tasks_implementation)

        if not implementation_content or len(implementation_content) == 0:
            logging.error(f'XGASkillEngine run_skill[{skill_name}]: No IMPLEMENTATION content extracted from response')
            return f"I was unable to determine skill '{skill_name}' implementation steps required to complete your request."

        if isinstance(implementation_content[0], dict):
            execute_results: List[dict] = []
            summary = ""

            for _code_block in implementation_content:
                execute_result: ExecutionResult = self.execute(
                    code_block=_code_block,
                    skill_context=skill_context,
                )
                execute_results.append(execute_result.to_dict())
                if not execute_result.success:
                    logging.error(f"XGASkillEngine run_skill[{skill_name}]: Execute code fail, stop execute skill code !")
                    summary = f"Skill '{skill_name}' execute code fail \n"
                    break

            result = summary + json.dumps(execute_results, ensure_ascii=False, indent=2)
        elif isinstance(implementation_content[0], tuple):
            # Dump the generated code content to files
            for _lang, _code in implementation_content:
                if _lang == 'html':
                    file_ext = 'html'
                elif _lang == 'javascript':
                    file_ext = 'js'
                else:
                    file_ext = 'md'

                output_file_path = self.work_dir / f'{str_to_md5(_code)}.{file_ext}'
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(_code)
                logging.info(f'XGASkillEngine run_skill[{skill_name}]: Generated {_lang} file saved to: {output_file_path}')
            result = f"Generated files have been saved to the working directory: {self.work_dir}"
        elif isinstance(implementation_content[0], str):
            result = '\n\n'.join(implementation_content)
        else:
            logging.error(f"XGASkillEngine run_skill[{skill_name}: Unknown IMPLEMENTATION content format")
            result = f"Skill '{skill_name}' run, encounter an unexpected format in the implementation steps."

        return result


    def _analyse_code_block(self, code_block: dict,
                            skill_context: SkillContext
                            ) -> Dict[str, str]:
        """
        Analyse a code block from a skill context to extract executable command.

        Args:
            code_block: Code block dictionary containing 'script' or 'function' key
                e.g. {{'script': '<script_path>', 'parameters': {{'param1': 'value1', 'param2': 'value2', ...}}}}
            skill_context: SkillContext object

        Returns:
            Dictionary containing:
                'type': 'script' or 'function'
                'code': Executable command string or code block
                'packages': List of required packages
        """
        # type - script or function
        result = {'type': '', 'code': '', 'packages': []}
        skill_name = skill_context.skill.name
        # Get the script path
        if 'script' in code_block:
            script_str: str = code_block.get('script')
            parameters: Dict[str, Any] = code_block.get('parameters', {})

            # Get real script absolute path
            script_path: Path = skill_context.root_path / script_str
            if not script_path.exists():
                script_path: Path = skill_context.root_path / 'scripts' / script_str
            if not script_path.exists():
                raise FileNotFoundError(f"Skill '{skill_name}' script not found: {script_str}")

            # Read the content of script
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()

                script_content = script_content.strip()
                if not script_content:
                    raise RuntimeError(f"Skill '{skill_name}' script is empty: {script_str}")

                # Build command to execute the script with parameters
                prompt: str = (
                    f'According to following script content and parameters, '
                    f'find the usage for script and output the shell command in the form of: '
                    f'```shell\npython {script_str} ...\n``` with python interpreter. '
                    f'\nExtract the packages required by the script and output them in the form of: ```packages\npackage1\npackage2\n...```. '  # noqa
                    f'Note that you need to exclude the build-in standard library packages, and determine the specific PyPI package name according to the import statements in the script. '  # noqa
                    f'you must output the result very concisely and clearly without any extra explanation.'
                    f'\n\nSCRIPT CONTENT:\n{script_content}'
                    f'\n\nPARAMETERS:\n{json.dumps(parameters, ensure_ascii=False)}'
                )
                response: str = self._call_llm(
                    user_prompt=prompt,
                    system_prompt='You are a helpful assistant that extracts the shell command from code blocks.'
                )

                cmd_blocks = extract_cmd_from_code_blocks(response)
                if len(cmd_blocks) == 0:
                    raise RuntimeError(f"Skill '{skill_name}' no shell command found in LLM response for script {script_str}")

                cmd_str = cmd_blocks[0]  # TODO: NOTE
                packages = extract_packages_from_code_blocks(response)

                result['type'] = 'script'
                result['code'] = cmd_str
                result['packages'] = packages
            except Exception as e:
                raise RuntimeError(f"Skill '{skill_name}' failed to read script {script_str}: {str(e)}")
        elif 'function' in code_block:
            result['type'] = 'function'
            result['code'] = code_block.get('function')
        else:
            raise ValueError(f"Skill '{skill_name}' code block must contain either 'script' or 'function' key")

        return result


    def execute(self, code_block: Dict[str, Any],
                skill_context: SkillContext
                ) -> ExecutionResult:
        """
        Execute a code block from a skill context.

        Args:
            code_block: Code block dictionary containing 'script' or 'function' key
                e.g. {{'script': '<script_path>', 'parameters': {{'param1': 'value1', 'param2': 'value2', ...}}}}
            skill_context: SkillContext object

        Returns:
            (ExecutionResult) Dictionary containing execution results
        """
        exec_result = ExecutionResult()
        skill_name = skill_context.skill.name
        try:
            executable_code: Dict[str, str] = self._analyse_code_block(
                code_block=code_block,
                skill_context=skill_context,
            )
            code_type: str = executable_code.get('type')
            code_str: str = executable_code.get('code')
            packages: list = executable_code.get('packages', [])

            if not code_str:
                raise RuntimeError(f"Skill '{skill_name}' hasn't command to execute extracted from code block")
        except Exception as e:
            logging.error(f"XGASkillEngine execute[{skill_name}]: analyzing code block error: {str(e)}")
            exec_result.success = False
            exec_result.messages = str(e)

            return exec_result

        try:
            if self.use_sandbox:
                if 'script' == code_type:

                    code_split = shlex.split(code_str)
                    new_code_split: List[str] = []
                    for item in code_split[1:]:
                        # All paths should be relative to `self.work_dir`
                        item = os.path.join(
                            str(self.work_dir_in_sandbox),
                            Path(item).as_posix())
                        new_code_split.append(item)
                    code_str = ' '.join(code_split[:1] + new_code_split)

                    results  = self.sandbox.exec_command(
                        shell_command=code_str,
                        requirements=packages,
                    )
                    return ExecutionResult(
                        success=True,
                        output=results,
                        messages='Executed in sandbox successfully for script.',
                    )
                elif 'function' == code_type:
                    results = self.sandbox.run_code(
                        python_code=code_str,
                        requirements=packages,
                    )
                    return ExecutionResult(
                        success=True,
                        output=results,
                        messages='Executed in sandbox successfully for function.',
                    )
                else:
                    raise ValueError(f"Skill '{skill_name}' execute unknown code type: {code_type}")

            else:
                # TODO: Add `confirm manually`
                logging.warning(f"XGASkillEngine execute[{skill_name}]: Executing code block in local environment!")

                # Prepare execution environment
                logging.info(f"XGASkillEngine execute[{skill_name}]: Installing required packages: {packages}")
                for pack in packages:
                    install_package(package_name=pack)

                if 'script' == code_type:
                    code_split: List[str] = shlex.split(code_str)
                    new_code_split: List[str] = []
                    for item in code_split[1:]:
                        # All paths should be relative to `self.work_dir`
                        item = os.path.join(str(self.work_dir), Path(item).as_posix())
                        new_code_split.append(item)
                    new_code_split = code_split[:1] + new_code_split
                    code_str = ' '.join(new_code_split)
                    return self._execute_cmd(cmd_str=code_str)
                elif 'function' == code_type:
                    return self._execute_code_block(code=code_str)
                else:
                    raise ValueError(f"Skill '{skill_name}' execute unknown code type: {code_type}")
        except Exception as e:
            logging.error(f"XGASkillEngine execute[{skill_name}]: Error executing code block: {str(e)}")
            exec_result.success = False
            exec_result.messages = str(e)

            return exec_result


    @staticmethod
    def _execute_code_block(code: str):
        """
        Execute a Python code block.

        Args:
            code: Python code string to execute

        Returns:
            ExecutionResult containing execution results
        """
        code = code or ''

        try:
            exec(code)
            return ExecutionResult(success=True, messages='Code executed successfully.')
        except Exception as e:
            return ExecutionResult(success=False, messages=str(e))


    @staticmethod
    def _execute_cmd(cmd_str: str,
                     timeout: int = 180,
                     work_dir: str = None,
                     ) -> ExecutionResult:
        """
        Execute a Python script command in a subprocess.

        Args:
            cmd_str: Command string to execute, e.g. "python script.py --arg1 val1"
            timeout: Execution timeout in seconds
            work_dir: Working directory for execution

        Returns:
            ExecutionResult containing execution results
        """
        try:
            # Build command
            cmd_parts = shlex.split(cmd_str)
            cmd: list = [sys.executable] + cmd_parts[1:]

            # Execute subprocess
            result = subprocess.run(cmd,
                                    capture_output=True,
                                    text=True,
                                    timeout=timeout,
                                    cwd=work_dir
                                    )

            return ExecutionResult(success=result.returncode == 0,
                                   output=result.stdout,
                                   messages=result.stderr
                                   )

        except Exception as e:
            return ExecutionResult(success=False, messages=str(e))


    def _call_llm(self,
                  user_prompt: str,
                  system_prompt: str = None
                  ) -> str:
        default_system: str = 'You are an intelligent assistant that can help users by leveraging specialized skills.'
        system_prompt = system_prompt or default_system

        messages = [
            {"role": "assistant", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.llm.completion(messages=messages)
        result = self.llm.get_completion_response(response)

        return result