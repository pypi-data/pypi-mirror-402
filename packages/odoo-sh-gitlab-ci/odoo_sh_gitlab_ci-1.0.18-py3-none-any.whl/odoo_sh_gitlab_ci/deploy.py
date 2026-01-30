import os
import subprocess
import argparse


def check_env_vars():
    """Verifica que todas las variables de entorno necesarias estén definidas."""
    required_vars = [
        "PRIVATE_DEPLOY_KEY", "GITHUB_REPO", "GITHUB_REPO_NAME",
        "CI_COMMIT_REF_NAME", "CI_PROJECT_NAME", "CI_REPOSITORY_URL",
        "VERSION", "CI_SERVER_HOST", "CI_PROJECT_PATH"
    ]
    for var in required_vars:
        error = False
        if not os.getenv(var):
            error = True
            print(f"Missing required environment variable: {var}")
    if error:
        exit(1)


def setup_ssh_and_git():
    """Configura el agente SSH y las credenciales de Git."""
    try:
        private_key = os.environ.get("PRIVATE_DEPLOY_KEY", "")
        git_user = os.environ.get("GIT_USER", "Jarsabot")
        git_email = os.environ.get("GIT_EMAIL", "jarsabot@jarsa.com")
        known_hosts = os.environ.get("KNOWN_HOSTS", "github.com git.jarsa.com git.vauxoo.com")

        if not private_key:
            raise ValueError("PRIVATE_DEPLOY_KEY is not set or empty.")

        subprocess.run(f"echo \"{private_key}\" | tr -d '\\r' | ssh-add -", shell=True, check=True)
        print("SSH key added successfully.")

        os.makedirs(os.path.expanduser("~/.ssh"), exist_ok=True)
        os.chmod(os.path.expanduser("~/.ssh"), 0o700)
        subprocess.run(f"ssh-keyscan {known_hosts} >> ~/.ssh/known_hosts", shell=True, check=True)
        os.chmod(os.path.expanduser("~/.ssh/known_hosts"), 0o644)
        subprocess.run(f"git config --global user.email '{git_email}'", shell=True, check=True)
        subprocess.run(f"git config --global user.name '{git_user}'", shell=True, check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error initializing environment: {e}")
        exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)


def clone_and_update_submodules():
    """Clona el repositorio y actualiza los submódulos."""
    try:
        production_branch = os.environ.get("PRODUCTION_BRANCH", "production")
        github_repo = os.environ["GITHUB_REPO"]
        github_repo_name = os.environ["GITHUB_REPO_NAME"]

        subprocess.run(f"git clone --recurse-submodules -b {production_branch} {github_repo}", shell=True, check=True)
        os.chdir(github_repo_name)
        subprocess.run("git submodule update --init --recursive", shell=True, check=True)
        subprocess.run("git submodule update --remote --force", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error cloning or updating submodules: {e}")
        exit(1)


def create_branch():
    """Crea la rama correspondiente dependiendo de la referencia del commit."""
    try:
        commit_ref_name = os.environ["CI_COMMIT_REF_NAME"]
        version = os.environ["VERSION"]
        staging_branch = os.environ.get("STAGING_BRANCH", "staging")
        gitlab_repo_url = os.environ["CI_REPOSITORY_URL"]
        gitlab_project_name = os.environ["CI_PROJECT_NAME"]
        gitlab_server_host = os.environ["CI_SERVER_HOST"]
        gitlab_project_path = os.environ["CI_PROJECT_PATH"]

        if commit_ref_name == version:
            subprocess.run(f"git checkout -b {staging_branch}", shell=True, check=True)
        else:
            os.chdir(gitlab_project_name)
            subprocess.run(f"git remote add forked_remote {gitlab_repo_url}", shell=True, check=True)
            subprocess.run(f"git fetch forked_remote {commit_ref_name}", shell=True, check=True)
            subprocess.run(f"git checkout -b {commit_ref_name} forked_remote/{commit_ref_name}", shell=True, check=True)
            os.chdir("..")
            subprocess.run(
                f"git submodule set-url -- {gitlab_project_name} "
                f"git@{gitlab_server_host}:{gitlab_project_path}.git", shell=True, check=True)
            subprocess.run(f"git checkout -b {commit_ref_name}", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error creating branch: {e}")
        exit(1)


def handle_dependencies():
    """Gestiona los submódulos definidos en el archivo oca_dependencies.txt."""
    def process_dependencies(repo_path, main_repo_path):
        """Procesa el archivo oca_dependencies.txt en la ruta especificada y añade submódulos al repositorio principal."""
        dependencies_file = os.path.join(repo_path, "oca_dependencies.txt")
        version = os.environ["VERSION"]
        github_org = os.environ.get("GITHUB_ORG", "Jarsa")

        if os.path.exists(dependencies_file):
            with open(dependencies_file, "r") as file:
                for line in file:
                    parts = line.strip().split()
                    if len(parts) == 3:
                        repo_name, repo_url, branch = parts
                    elif len(parts) == 2:
                        repo_name, repo_url = parts
                        branch = version
                    elif len(parts) == 1:
                        repo_name = parts[0]
                        repo_url = f"git@github.com:{github_org}/{repo_name}.git"
                        branch = version
                    else:
                        print(f"Invalid line format in {dependencies_file}: {line}")
                        continue

                    # Ignorar repositorios que ya están en Odoo.sh por defecto
                    if repo_name in ["enterprise", "design-themes"]:
                        continue

                    # Verificar si el submódulo ya existe en el repositorio principal
                    submodule_path = os.path.join(main_repo_path, repo_name)
                    if not os.path.exists(submodule_path):
                        print(f"Adding submodule: {repo_name} to the main repository.")
                        subprocess.run(f"git submodule add -b {branch} {repo_url} {repo_name}", shell=True, check=True, cwd=main_repo_path)
                        subprocess.run("git submodule update --init --recursive", shell=True, check=True, cwd=main_repo_path)

        # Procesar dependencias recursivamente en submódulos existentes
        try:
            submodules = subprocess.check_output("git submodule status --recursive", shell=True, cwd=repo_path).decode().strip().split("\n")
        except subprocess.CalledProcessError:
            print(f"No submodules found in {repo_path}. Continuing.")
            return
        for submodule in submodules:
            submodule_parts = submodule.strip().split()
            if len(submodule_parts) > 1:
                submodule_path = os.path.join(repo_path, submodule_parts[1])
                if os.path.isdir(submodule_path):
                    process_dependencies(submodule_path, main_repo_path)

    # El archivo oca_dependencies.txt está en el directorio padre del repositorio principal
    github_repo_name = os.environ["GITHUB_REPO_NAME"]
    parent_path = os.path.dirname(os.getcwd())
    main_repo_path = os.getcwd()
    process_dependencies(parent_path, main_repo_path)



def commit_and_push():
    """Realiza el commit y el push si hay cambios en los submódulos."""
    try:
        updated_submodules = subprocess.check_output(
            "git submodule status --recursive",
            shell=True
        ).decode().strip().split("\n")

        if not updated_submodules:
            print("No changes in submodules. Skipping commit.")
            subprocess.run("git push -f origin HEAD", shell=True, check=True)
            print("Pushed changes successfully.")
            return
        parsed_submodules = [
            {
                "sha": line.split()[0].strip(),
                "name": line.split()[1].strip()
            }
            for line in updated_submodules
        ]
        updated_list = "\n".join([f"{submodule['name']} {submodule['sha']}" for submodule in parsed_submodules])
        commit_message = f"""Update submodules

Updated submodules:

{updated_list}"""
        subprocess.run(f"git commit -am \"{commit_message}\"", shell=True, check=True)
        subprocess.run("git push -f origin HEAD", shell=True, check=True)
        print("Pushed changes successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during commit or push: {e}")
        exit(1)


def deploy():
    """Handles the deployment process for Odoo.sh."""
    check_env_vars()
    clone_and_update_submodules()
    handle_dependencies()
    create_branch()
    commit_and_push()


def main():
    parser = argparse.ArgumentParser(description="Manage Odoo.sh deployment.")
    parser.add_argument("--initialize", action="store_true", help="Initialize the environment (SSH agent, known hosts, Git config).")
    args = parser.parse_args()

    if args.initialize:
        setup_ssh_and_git()
    else:
        deploy()


if __name__ == "__main__":
    main()
