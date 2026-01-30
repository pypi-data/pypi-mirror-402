#!/usr/bin/env python

import argparse
import atexit
import os
import select
import signal
import sys
import tempfile
from importlib.metadata import version

# line:col coordinate
Position = tuple[int, int]
# represents a list of Specs, where each spec
# is the start and end Position of a highlight
SpecList = list[tuple[Position, Position]]


# parses a string in the line-specs option type
def parse_specs(data: str):
	parsed: SpecList = []
	for entry in data.strip().split():
		# minimum length of a valid spec
		if not entry or len(entry) < 9:
			continue
		range_part, _ = entry.split("|", 1)
		start_str, end_str = range_part.split(",")
		sl, sc = map(int, start_str.split("."))
		el, ec = map(int, end_str.split("."))
		parsed.append(((sl, sc), (el, ec)))
	return parsed


# determine whether the cursor is overlapping with
# any of the ranges defined in the spec list
def is_cursor_in_any(cursor: Position, diagnostics: SpecList) -> bool:
	cl, cc = cursor
	for (sl, sc), (el, ec) in diagnostics:
		if cl < sl or cl > el:
			continue
		if sl == el:
			if cl == sl and sc <= cc <= ec:
				return True
		elif cl == sl:
			if cc >= sc:
				return True
		elif cl == el:
			if cc <= ec:
				return True
		elif sl < cl < el:
			return True
	return False


# clean up temp files before exiting
def cleanup(inp: str, outp: str, dir: str):
	try:
		os.remove(inp)
		os.remove(outp)
		os.rmdir(dir)
	except FileNotFoundError:
		pass


# returns the static portion of the kakscript that should be
# evaluated by Kakoune on init
def get_static_output() -> str:
	cmds = r"""define-command lsp-diag-set %{
    evaluate-commands %sh{
        {
            printf 'set %s\n' "$kak_opt_lsp_inline_diagnostics" >"$kak_opt_diagpipe_in"
            read result < "$kak_opt_diagpipe_out"
            if [ "$result" != "ok" ]; then
                cmd=$(printf "eval -try-client '$kak_client' -verbatim info -title lsp-diag 'failed to parse diagnostics'")
                echo "$cmd" | kak -p ${kak_session}
            fi
        } </dev/null >/dev/null 2>&1 &
    }
}

define-command -params 2 lsp-diag-query %{
    evaluate-commands %sh{
        printf 'query %s %s\n' "$1" "$2" >"$kak_opt_diagpipe_in"
        read result < "$kak_opt_diagpipe_out"
        if [ "$result" = "true" ]; then
            echo "trigger-user-hook lsp-diag-hover-true"
        else
            echo "trigger-user-hook lsp-diag-hover-false"
        fi
    }
}

hook global KakEnd .* %{
    nop %sh{
        printf 'exit\n' >"$kak_opt_diagpipe_in"
        read result < "$kak_opt_diagpipe_out"
    }
}

declare-option -hidden bool lsp_diags_enabled false

try %{ define-command -hidden true nop }
try %{ define-command -hidden false fail }

define-command lsp-diag-hover-enable %{
    lsp-diag-set

    hook -group lsp-diag window User lsp-diag-hover-false %{
        try %{
            %opt{lsp_diags_enabled}
            try %{
                lsp-inlay-diagnostics-disable window
                set-option window lsp_diags_enabled false
            }
        } 
    }

    hook -group lsp-diag window User lsp-diag-hover-true %{
        try %{
            %opt{lsp_diags_enabled}
        } catch %{
            try %{
                lsp-inlay-diagnostics-enable window
                set-option window lsp_diags_enabled true
            }
        }
    }
    hook -group lsp-diag window NormalIdle .* %{
        lsp-diag-query %val{cursor_line} %val{cursor_column}
    }
    hook -group lsp-diag window WinSetOption lsp_inline_diagnostics=.* %{
        lsp-diag-set
    }
    hook -group lsp-diag window ModeChange .+:normal:insert %{
        try %{ lsp-inlay-diagnostics-disable window }
    }
}
define-command lsp-diag-hover-disable %{
    remove-hooks window lsp-diag
    try %{
        lsp-inlay-diagnostics-disable window
        set-option window lsp_diags_enabled false
    }
}
	"""
	return cmds


# returns the kakscript that should be evaluated by Kakoune on init
# includes necessary options storing path of FIFOs
def gen_kakoune_output(inp: str, outp: str, print_static: bool) -> str:
	out_l = [
		f"declare-option -hidden str diagpipe_in {inp}",
		f"declare-option -hidden str diagpipe_out {outp}",
	]
	if print_static:
		out_l.append(get_static_output())
	out = "\n".join(out_l)
	return out


# daemonize this process
def daemonize(inp: str, outp: str, dir: str):
	# fork and exit parent
	if os.fork() > 0:
		sys.exit(0)
	# new session
	os.setsid()
	# double fork
	if os.fork() > 0:
		# exit first child
		sys.exit(0)

	# redirect IO to /dev/null
	with open("/dev/null", "rb", 0) as dn:
		os.dup2(dn.fileno(), sys.stdin.fileno())
	with open("/dev/null", "ab", 0) as dn:
		os.dup2(dn.fileno(), sys.stdout.fileno())
		os.dup2(dn.fileno(), sys.stderr.fileno())
	# register cleanup function on exit
	_ = atexit.register(lambda: cleanup(inp, outp, dir))

	# ensure that SIGTERM & SIGINT trigger the cleanup
	def on_exit(*_):
		sys.exit(0)

	signal.signal(signal.SIGTERM, on_exit)
	signal.signal(signal.SIGINT, on_exit)


# entry point
def main():
	# parse options
	parser = argparse.ArgumentParser(
		description="LSP diagnostic hover plugin for Kakoune.",
		epilog="""
Author : Daniel Fichtinger
License: ISC
Contact: daniel@ficd.sh
        """,
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument(
		"-v",
		"--version",
		required=False,
		help="Print version info and exit.",
		action="store_true",
	)
	# if enabled, static kakscript won't be printed
	parser.add_argument(
		"--no-static",
		required=False,
		help="Don't output the contents of static.kak for evaluation. Useful if you want to change the commands yourself.",
		action="store_false",
	)
	# if enabled, static content is printed and program exits early
	# (akin to a dry run)
	parser.add_argument(
		"--print-static",
		required=False,
		help="Output the contents of static.kak but don't start daemon.",
		action="store_true",
	)
	args = parser.parse_args()
	if args.version:
		print(version("kak-lsp-diags"))
		exit(0)
	print_static: bool = args.no_static
	dry_run: bool = args.print_static
	# dry run if user provided the option
	if dry_run:
		print(get_static_output())
		sys.exit(0)

	# create temp directory and generate FIFO paths
	fifo_dir = tempfile.mkdtemp(prefix="diagpipe-")
	in_path = os.path.join(fifo_dir, "in")
	out_path = os.path.join(fifo_dir, "out")

	# create fifos
	os.mkfifo(in_path)
	os.mkfifo(out_path)

	# open the input FIFO reader non blocking
	read_fd = os.open(in_path, os.O_RDONLY | os.O_NONBLOCK)
	infile = os.fdopen(read_fd, "r", buffering=1)

	# open a non-blocking dummy reader for the output FIFO
	# necessary because the FIFO can't be opened for writing
	# if there isn't a reader present -- and it's not guaranteed
	# that Kakoune will be connected as a reader yet
	_dummy = os.open(out_path, os.O_RDONLY | os.O_NONBLOCK)

	# open the output FIFO writer non blocking
	write_fd = os.open(out_path, os.O_WRONLY | os.O_NONBLOCK)
	outfile = os.fdopen(write_fd, "w", buffering=1)

	# close file descriptors for a clean exit
	def cleanup_fifos():
		try:
			infile.close()
		except Exception:
			pass
		try:
			outfile.close()
		except Exception:
			pass

	# register cleanup function for exit
	atexit.register(cleanup_fifos)

	# print kakscript for Kakoune to evaluate on init
	output = gen_kakoune_output(in_path, out_path, print_static)
	print(output)
	sys.stdout.flush()

	# daemonize this process to return control to Kakoune
	daemonize(in_path, out_path, fifo_dir)

	# cache of parsed diagnostic specs
	diagnostics: SpecList = []

	# main event loop
	while True:
		# wait for the input FIFO to become available
		# avoiding high CPU usage from polling
		rlist, _, _ = select.select([infile], [], [])
		if rlist:
			# process line of input
			line = infile.readline()
			if not line:
				continue
			line = line.strip()
			assert isinstance(line, str)

			# specs have been updated and need to be parsed
			if line.startswith("set "):
				# extract specs from the input
				_, payload = line.split(" ", 1)
				# parse
				diagnostics = parse_specs(payload)
				# write success status to FIFO
				try:
					outfile.write("ok\n")
					outfile.flush()
				except BrokenPipeError:
					pass
			# query with cursor position for current speclist
			elif line.startswith("query "):
				# extract cursor position
				_, pos = line.split(" ", 1)
				line, col = map(int, pos.strip().split())
				# compare against cached spec list
				result = is_cursor_in_any((line, col), diagnostics)
				# write result to FIFO
				_ = outfile.write("true\n" if result else "false\n")
				outfile.flush()
			# received exit command
			elif line.startswith("exit"):
				# sys.exit triggers cleanup functions
				sys.exit(0)
			# ping for debugging IPC
			elif line.startswith("ping"):
				outfile.write("pong\n")
				outfile.flush()


# run main entry point if executed directly
if __name__ == "__main__":
	main()

# pyright: basic, reportUnusedCallResult=false
