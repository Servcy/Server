# Contributing to Servcy

Thank you for showing an interest in contributing to Servcy! All kinds of contributions are valuable to us. In this guide, we will cover how you can quickly onboard and make your first contribution.

## Submitting an issue

Before submitting a new issue, please search the [issues](https://github.com/Servcy/Server/issues) tab. Maybe an issue or discussion already exists and might inform you of workarounds. Otherwise, you can give new information.

While we want to fix all the [issues](https://github.com/Servcy/Server/issues), before fixing a bug we need to be able to reproduce and confirm it. Please provide us with a minimal reproduction scenario using a repository or [Gist](https://gist.github.com/). Having a live, reproducible scenario gives us the information without asking questions back & forth with additional questions like:

- 3rd-party libraries being used and their versions
- a use-case that fails

Without said minimal reproduction, we won't be able to investigate all [issues](https://github.com/Servcy/Server/issues), and the issue might not be resolved.

You can open a new issue with this [issue form](https://github.com/Servcy/Server/issues/new).

## Missing a Feature?

If a feature is missing, you can directly _request_ a new one [here](https://github.com/Servcy/Server/issues/new?assignees=&labels=feature&template=feature_request.yml&title=%F0%9F%9A%80+Feature%3A+). You also can do the same by choosing "🚀 Feature" when raising a [New Issue](https://github.com/Servcy/Server/issues/new/choose) on our GitHub Repository.
If you would like to _implement_ it, an issue with your proposal must be submitted first, to be sure that we can use it. Please consider the guidelines given below.

## Coding guidelines

To ensure consistency throughout the source code, please keep these rules in mind as you are working:

In this project, we follow a set of coding style guidelines to maintain consistency and readability across our codebase. These guidelines are inspired by the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) and integrate the usage of `black` and `isort` for automatic code formatting.

### Python Style Guide

We adhere to the guidelines outlined in the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) with the following additions and modifications:

### Naming Conventions

- Follow PEP 8 conventions for naming variables, functions, classes, and modules.
- Use descriptive and meaningful names that accurately represent the purpose of the variable, function, class, or module.

### Code Formatting

We use `black` and `isort` to automatically format our Python code. These tools ensure consistent formatting across the codebase and help maintain readability.

### Documentation

- Document all public modules, classes, functions, and methods using docstrings.
- Follow the NumPy/SciPy documentation guidelines for docstrings.

## Code Formatting

We use `black` and `isort` for code formatting. Make sure to run these tools before committing your changes.

### black

[Black](https://black.readthedocs.io/en/stable/) is an uncompromising Python code formatter. It ensures that the entire codebase adheres to a consistent and readable style.

To format your code using black, run the following command:

```bash
black .
```

### isort

[isort](https://pycqa.github.io/isort/) is a Python utility that sorts imports alphabetically within each section and separated by a blank line between different sections.

```bash
isort .
```

## Ways to contribute

- Try Servcy and give feedback
- Add new integrations
- Help with open [issues](https://github.com/Servcy/Server/issues) or [create your own](https://github.com/Servcy/Server/issues/new/choose)
- Share your thoughts and suggestions with us
- Help create tutorials and blog posts
- Request a feature by submitting a proposal
- Report a bug
