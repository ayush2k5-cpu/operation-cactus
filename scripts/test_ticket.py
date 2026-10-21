from scripts.ticket import base_branch, branch_name, module_of, owner_of, slug


def test_module_from_label():
    assert module_of(["cycle-2", "module:mimicnet"]) == "mimicnet"
    assert module_of(["module:flowsight-capture"]) == "flowsight"
    assert module_of(["module:backend-console"]) == "backend"
    assert module_of(["module:data-eval"]) == "eval"
    assert module_of(["module:workflow"]) is None
    assert module_of(["cycle-2"]) is None


def test_owner_from_label_defaults_to_dev():
    assert owner_of(["owner:shivansh", "agent:agy"]) == "shivansh"
    assert owner_of(["cycle-2"]) == "dev"


def test_slug_is_short_and_clean():
    assert slug("Honeypot session and engage!") == "honeypot-session-and-engage"
    assert len(slug("x" * 100)) <= 40


def test_branch_names_never_collide_with_module_branches():
    assert branch_name("mimicnet", "shivansh", "Honeypot session and engage") == (
        "mimicnet/shivansh-honeypot-session-and-engage"
    )
    assert base_branch("mimicnet") == "mod/mimicnet"
    assert base_branch(None) == "main"
