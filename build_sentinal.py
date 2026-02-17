def main():
    args = parse_args()
    proj_dir = pathlib.Path(__file__).resolve().parent
    os.chdir(proj_dir)

    check_python()
    check_build_deps()

    if args.rebuild:
        for d in ["build", "dist", "src/sentinal.egg-info"]:
            if pathlib.Path(d).exists():
                shutil.rmtree(d)

    if args.user:
        python_exec = sys.executable
        info(f"Using system python: {python_exec}")
    else:
        python_exec = str(make_venv())
        info(f"Using venv python: {python_exec}")

    wheel_file = build_wheel(proj_dir, python_exec)
    install_wheel(wheel_file, python_exec, args.user)

    if not args.no_index:
        index_initial_dirs(python_exec)

    smoke_test(python_exec)
    spawn_demo_terminal(python_exec)

    success("Sentinal build and install complete!")
