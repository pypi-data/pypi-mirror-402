# ralph-code

Automated task implementation with Claude Code and Codex for "Ralph Coding". What is [Ralph Coding](https://ghuntley.com/ralph/)? It's a method of coding where context rot is avoided by controlling the retention of information. This method involves re-invoking claude or codex for each task, and passing information about the requirements, acceptance testing, and any progress that's made (or roadblocks/challenges faced) through files, rather than retaining all prompts + thinking + response tokens. It tends to result in more requests, some duplicated token work, but fairly consistent performance, and best of all it can largely be done unattended. Recommend Claude Max account or codex equivalent, but be aware that GPT-5 - GPT5.2's slow reasoning and response makes this ponderous, it's fine overnight.

Because LLMs are carrying out the work, we can specify a job of "Find all the python files in the project that directly or indirectly access sqlalchemy objects, and upgrade the code to work with sqlalchemy 2.* This will result in probably a single-task project, but that one task might add 50 other tasks (on per file) to the backlog, which are then processed sequentially."

## Installation

```bash
pipx install ralph-code
```

Or with pip:

```bash
pip install ralph-code
```

## Usage

```bash
ralph [OPTIONS] [DIRECTORY]
```

### Options

- `--debug`: Enable debug logging, logs are saved into the .ralph subdirectory of the project
- `DIRECTORY`: Target project directory (defaults to current directory)

## Usage

First create a task, give a short name for the task (used for the branch commits will be added to), and then give a description. 
Then you run the ralph-coder, it will produce a .md file of the specifications, which will be broken into small tasks put into a tasks.json file. Each task will be worked on independently. 

## Requirements

- Python 3.10+
- Claude Code or Codex CLI installed and configured

## License

MIT
