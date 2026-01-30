import os
import shutil

from pathlib import Path

from xgse.engine.skill_engine import XGASkillEngine
from xgse.utils.setup_env import setup_logging

setup_logging()

def main():
    run_path = Path(__file__).parent.resolve()
    project_path = run_path.parents[1]

    example_data_dir = str(run_path / 'example_data')
    skill_work_dir = str(project_path / 'skill_workspace')
    prepare_work_dir(example_data_dir, skill_work_dir)

    skills_root_path = run_path / "skills"

    # 1. Load all skills
    # skills_root_dir = str(skills_root_path)

    # 2. Load one skill
    # skills_root_dir = str(skills_root_path / 'pdf')

    # 3. Load some skills
    use_skill_names = ["pdf", "algorithmic-art"]
    skills_root_dir = [str(skills_root_path / name) for name in use_skill_names]

    use_sandbox = False
    skill_engine = XGASkillEngine(skills=skills_root_dir,
                                  use_sandbox=use_sandbox,
                                  work_dir=skill_work_dir
                                  )

    user_inputs = [
        f'Extract the form field info from pdf: OLYMPIC_MEDAL_TABLE_zh.pdf, generate result file as OLYMPIC_MEDAL_TABLE_zh_fields.json',
        #'Create generative art using p5.js with seeded randomness, flow fields, and particle systems, please fill in the details and provide the complete code based on the templates.'
    ]

    try:
        for query in user_inputs:
            print(f'*** User Input:\n{query}\n\n')
            response = skill_engine.run(query)
            print(f'\n\n*** Skill Run Results: {response}\n')
    finally:
        pass
        # skill_engine.destroy()


def prepare_work_dir(example_data_dir: str, skill_work_dir: str):
    if os.path.exists(skill_work_dir):
        print(f"Remove skill work space dir '{skill_work_dir}'")
        shutil.rmtree(skill_work_dir)
    else:
        print(f"Skill work space '{skill_work_dir}' is not exist")

    print(f"Create empty skill work space '{skill_work_dir}'")
    os.makedirs(skill_work_dir, exist_ok=True)

    shutil.copytree(example_data_dir, skill_work_dir, dirs_exist_ok=True)


if __name__ == '__main__':
    main()
