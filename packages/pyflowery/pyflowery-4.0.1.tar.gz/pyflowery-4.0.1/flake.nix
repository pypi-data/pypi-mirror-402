{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    devshell.url = "github:numtide/devshell";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      nixpkgs-python,
      ...
    }@inputs:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = with inputs; [
            devshell.overlays.default
          ];
        };
        name = "PyFlowery";
        pythonVersion = "3.11"; # 2.7, 3.3.1 - latest
      in
      {
        devShells.default = pkgs.devshell.mkShell {
          commands = with pkgs; [
            { package = uv; }
            { package = ruff; } # the ruff pip package installs a dynamically linked binary that cannot run on NixOS
            { package = basedpyright; } # same as ruff
            { package = typos; }
            {
              name = "mkdocs";
              command = ''mkdocs "$@"'';
              help = "Project documentation with Markdown / static website generator";
            }
            {
              name = "tests";
              command = "pytest --cov=pyflowery --cov-report=term-missing \"$@\"";
              help = "Run tests with pytest";
            }
            {
              name = "repl";
              command = ''
                tmpfile=$(mktemp)
                cat >$tmpfile <<'PYTHON'

                import pyflowery as pyf
                import logging
                from rich.logging import RichHandler
                from rich import print

                logging.basicConfig(
                  level=logging.INFO,
                  format="[cyan]%(name)s:[/cyan] %(message)s",
                  datefmt="[%X]",
                  handlers=[RichHandler(
                      rich_tracebacks=True,
                      tracebacks_show_locals=True,
                      show_time=True,
                      markup=True,
                  )]
                )

                logger = logging.getLogger("repl")
                logger.level = logging.DEBUG
                api = pyf.FloweryAPI(config=pyf.FloweryAPIConfig(user_agent="PyFloweryDevelopment", logger=logger.getChild("pyflowery")))
                logger.info("PyFlowery API available at [bold blue]api[/bold blue].")

                PYTHON
                ipython -i $tmpfile
                rm $tmpfile
              '';
              help = "Start an interactive Python REPL with PyFlowery already configured.";
            }
          ];

          packages = with pkgs; [
            stdenv.cc.cc
            stdenv.cc.cc.lib
            nixpkgs-python.packages.${system}.${pythonVersion}
            git
            # Material for MkDocs dependencies
            cairo
            pngquant
          ];

          env = [
            {
              name = "CPPFLAGS";
              eval = "-I$DEVSHELL_DIR/include";
            }
            {
              name = "LDFLAGS";
              eval = "-L$DEVSHELL_DIR/lib";
            }
            {
              name = "LD_LIBRARY_PATH";
              eval = "$DEVSHELL_DIR/lib:$LD_LIBRARY_PATH";
            }
            {
              name = "UV_PYTHON_PREFERENCE";
              value = "only-system";
            }
            {
              name = "UV_PYTHON_DOWNLOADS";
              value = "never";
            }
          ];

          motd = ''
            {33}🔨 Welcome to the {208}${name}{33} Devshell!{reset}
            $(type -p menu &>/dev/null && menu)
          '';

          devshell = {
            name = name;
            startup = {
              ensure-git-repository.text = ''
                if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
                  echo "❌ Git repository not found! Initializing..."
                  git init
                  git add flake.nix flake.lock # Add these files so Nix can detect the flake and its lockfile, now that we're in a git repository
                  echo "✅ Git repo initialized."
                fi
              '';
              bootstrap-project = {
                text = ''
                  set -euo pipefail

                  echo "🔧 Bootstrapping Python environment..."

                  has_pyproject=false
                  has_requirements=false
                  venv_exists=false

                  if [[ -d ".venv" ]]; then
                    venv_exists=true
                  fi

                  if [[ -f "pyproject.toml" ]]; then
                    echo "📦 Found pyproject.toml"
                    has_pyproject=true
                  else
                    echo "🚫 pyproject.toml not found."
                  fi

                  if [[ "$has_pyproject" = "false" ]]; then
                    requirements_files=(
                      "requirements.txt"
                      "requirements-dev.txt"
                      "requirements.dev.txt"
                      "dev-requirements.txt"
                      "dev.txt"
                      "test-requirements.txt"
                      "requirements_test.txt"
                    )

                    for file in "''${requirements_files[@]}"; do
                      if [[ -f "$file" ]]; then
                        echo "✅ Found: $file"
                        if [[ "$venv_exists" = false ]]; then
                          uv venv
                          venv_exists=true
                        fi
                        uv pip install -r "$file"
                        has_requirements=true
                      fi
                    done

                    mapfile -t wildcard_matches < <(find . -maxdepth 1 -type f -iname "requirements*.txt")

                    for match in "''${wildcard_matches[@]}"; do
                      if [[ ! " ''${requirements_files[*]} " =~ " ''${match##./} " ]]; then
                        echo "✅ Found (wildcard): $match"
                        if [[ "$venv_exists" = false ]]; then
                          uv venv
                          venv_exists=true
                        fi
                        uv pip install -r "$match"
                        has_requirements=true
                      fi
                    done
                  fi

                  if [[ "$has_pyproject" = false && "$has_requirements" = false ]]; then
                    echo "🧪 No pyproject.toml or requirements files found. Creating bare uv project..."
                    uv init --bare --name=change-me
                  fi

                  if [[ ! -f "uv.lock" && "$has_requirements" = false ]]; then
                    echo "🔒 uv.lock not found. Generating lockfile..."
                    uv sync --all-groups --all-extras
                  elif [[ "$has_requirements" = false ]]; then
                    echo "🔒 uv.lock found. Syncing with lockfile..."
                    uv sync --all-groups --all-extras --locked
                  fi

                  source .venv/bin/activate
                  export PATH="${pkgs.uv}/bin:${pkgs.ruff}/bin:${pkgs.basedpyright}/bin:$PATH"
                '';
                deps = [ "ensure-git-repository" ];
              };
              ensure-data-dir-exists.text = ''mkdir -p "$PRJ_DATA_DIR"'';
            };
          };
        };
      }
    );
}
