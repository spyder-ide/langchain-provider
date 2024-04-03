# Release Procedure

In the commands below, replace `X.Y.Z` with the release version when needed.

**Note**: We use `pip` instead of `conda` here even on Conda installs, to ensure we always get the latest upstream versions of the build dependencies.


## PyPI

To release a new version of QtPy on PyPI:


### Prepare

* Close [GitHub milestone](https://github.com/spyder-ide/langchain-provider/milestones) and ensure all issues are resolved/moved

* Update local repo

  ```bash
  git restore . && git switch master && git pull upstream master
  ```

* Clean local repo

  ```bash
  git clean -xfdi
  ```


### Commit

* Install/upgrade Loghub

  ```bash
  pip install --upgrade loghub
  ```

* Update `CHANGELOG.md` using Loghub to generate the list of issues and PRs merged to add at the top of the file

  ```bash
  loghub -m vX.Y.Z spyder-ide/langchain-provider
  ```

* Update `version` in `pyproject.toml` (set release version, remove `.dev0`)

* Create release commit

  ```bash
  git commit -am "Release X.Y.Z"
  ```


### Build

* Update the packaging stack

  ```bash
  python -m pip install --upgrade pip
  pip install --upgrade --upgrade-strategy eager build setuptools twine wheel
  ```

* Build source distribution and wheel

  ```bash
  python -bb -X dev -W error -m build
  ```

* Check distribution archives

  ```bash
  twine check --strict dist/*
  ```


### Release

* Upload distribution packages to PyPI

  ```bash
  twine upload dist/*
  ```

* Create release tag

  ```bash
  git tag -a vX.Y.Z -m "Release X.Y.Z"
  ```


### Finalize

* Update `version` in `pyproject.toml` (add `.dev0` and increment minor)

* Create `Back to work` commit

  ```bash
  git commit -am "Back to work"
  ```

* Push new release commits and tags to `master`

  ```bash
  git push upstream master --follow-tags
  ```

* Create a [GitHub release](https://github.com/spyder-ide/langchain-provider/releases) from the tag
