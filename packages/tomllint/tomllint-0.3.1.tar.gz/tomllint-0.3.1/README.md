# tomllint

A TOML Linter. Checks for basic syntactic errors in any TOML file.

## Installation

```bash
$ pip install tomllint
```

## Usage

Usage is self explanatory, simply name the files to lint, or use `-` to indicate that it should read
from `stdin`.

```
usage: tomllint [-h] toml_file [toml_file ...]

positional arguments:
  toml_file   TOML filenames or "-" for stdin

options:
  -h, --help  show this help message and exit
```

## Neovim Integration

To register tomllint with [nvim-lint](https://github.com/mfussenegger/nvim-lint), you'd add
something like this to your `~/.config/nvim/init.lua` or other imported file.

```lua
require("lint").linters_by_ft.toml = { "tomllint" }
local function parse_tomllint_output(output, bufnr, _linter_cwd)
	local diagnostics = {}
	for line in output:gmatch("[^\r\n]+") do
		local _, lnum, col, description = line:match("(.+):(%d+):(%d+): error: (.+)")
		if lnum and description then
			table.insert(diagnostics, {
				bufnr = bufnr,
				lnum = tonumber(lnum) - 1,
				col = tonumber(col) - 1,
				end_lnum = tonumber(lnum) - 1,
				end_col = tonumber(col),
				severity = vim.diagnostic.severity.ERROR,
				message = description,
			})
		end
	end
	return diagnostics
end
require("lint").linters.tomllint = {
	cmd = "tomllint",
	stdin = true,
	append_fname = false,
	args = { "-" },
	stream = "stderr",
	ignore_exitcode = false,
	env = nil,
	parser = parse_tomllint_output,
}
```
