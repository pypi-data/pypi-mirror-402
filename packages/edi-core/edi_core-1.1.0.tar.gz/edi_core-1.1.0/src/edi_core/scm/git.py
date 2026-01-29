import git


def clone_and_checkout(path, url, branch):
    repo = git.Repo.clone_from(url=url, to_path=path)
    repo.create_head(branch).checkout()
