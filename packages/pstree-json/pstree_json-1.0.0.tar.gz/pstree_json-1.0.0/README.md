# pstree-json
**@readwithai** - [X](https://x.com/readwithai) - [blog](https://readwithai.substack.com/) - [machine-aided reading](https://www.reddit.com/r/machineAidedReading/) - [📖](https://readwithai.substack.com/p/what-is-reading-broadly-defined
)[⚡️](https://readwithai.substack.com/s/technical-miscellany)[🖋️](https://readwithai.substack.com/p/note-taking-with-obsidian-much-of)

An easily-installable command-line to output the process tree in machine readable format. Suitable for pasting into an LLM.

Warning. This is ai-generated and I cannot guarantee to not changing the options! If people use it I may freeze it but don't use it in automated scripts unless you are freezing.

## Motivation
Do you ever get a feeling like "what is wrong with the world". It feels very odd that this tool does not exist, so I am creating it.

Having a tree in JSON format makes it a lot easier to do things like find a processes parents and child etc.
Using programmatic tools and `grep` to interact with a process tree particular useful when you have a lot of processes.


## Installation
You can install `pstree-json` using [pipx](https://github.com/pypa/pipx):
```
pipx install pstree-json
```

## Usage
To list processes us `pstree-json`.

```
pstree-json $PID
```

You likely want to use a combination of [gron](https://github.com/tomnomnom/gron) or [json-leaves](https://github.com/talwrii/json-leaves) (written by the author) together with `grep` to search what is going on with tress and [jq](https://jqlang.org/) to then extract desired information.

## Attribution and prior work
This tool is a wrapper around the [psutil](https://github.com/giampaolo/psutil) library - but is useful from the shell.

You might like to use pgtree which combines pg with pstree to show a process tree. 
You can use pstree - but this did not show me enough information.


pgtree-tui provides a tui for interactive wit hthe process tree.


## About me
I am **@readwithai**. I create tools for reading, research and agency sometimes using the markdown editor [Obsidian](https://readwithai.substack.com/p/what-exactly-is-obsidian).

I also create a [stream of tools](https://readwithai.substack.com/p/my-productivity-tools) that are related to carrying out my work.

I write about lots of things - including tools like this - on [X](https://x.com/readwithai).
My [blog](https://readwithai.substack.com/) is more about reading and research and agency.
