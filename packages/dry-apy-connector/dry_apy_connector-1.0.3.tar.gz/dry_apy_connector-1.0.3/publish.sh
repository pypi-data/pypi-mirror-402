#!/usr/bin/bash

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Please run 'uv sync' first."
    exit 1
fi

# Use virtual environment
source .venv/bin/activate

branch_name=$(git symbolic-ref -q HEAD)
branch_name=${branch_name##refs/heads/}
branch_name=${branch_name:-HEAD}

if [ "$branch_name" != "main" ]; then
    echo "Publishing is allowed only on main branch"
    exit 1
fi

if [[ -n $(git status --porcelain | grep -v "publish.sh") ]]; then
    echo "Repository contains changes, commit them before publishing"
    exit 1
fi

rm -f pyproject.toml.bak
cp ./pyproject.toml ./pyproject.toml.bak

# update version
VERSION=$(grep -Po '(?<=version = ")[^"]*' "./pyproject.toml")
echo "Set new version(${VERSION}):"
read NEW_VERSION
sed -i "s/version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$NEW_VERSION\"/g" ./pyproject.toml
VERSION=$(grep -Po '(?<=version = ")[^"]*' "./pyproject.toml")

if [ "$VERSION" != "$NEW_VERSION" ] || [ -z "$NEW_VERSION" ]; then
    echo "Error: Failed to set new version -> Rolling back"
    rm ./pyproject.toml
    mv ./pyproject.toml.bak ./pyproject.toml
    exit 1
    else echo "Version successfully updated to $NEW_VERSION"
fi

# build
echo "Installing build dependencies..."
uv pip install --quiet twine build

echo "Building package..."
python -m build
build_done=$?

if [ $build_done -ne 0 ]; then
    echo "Error: Failed to build package -> Rolling back"
    rm -rf ./dist
    uv pip uninstall --quiet -y twine build
    mv ./pyproject.toml.bak ./pyproject.toml
    exit 1
fi


echo "Uploading to local pypi server"
twine upload --repository-url http://pypi.navigo3.com:8080 dist/*
upload_done=$?

if [ $upload_done -ne 0 ]; then
    echo "Error: Failed to upload package to local pypi server -> Rolling back"
    rm -rf ./dist
    uv pip uninstall --quiet -y twine build
    mv ./pyproject.toml.bak ./pyproject.toml
    exit 1
fi
echo "Uploading to PyPI..."
# Use .pypirc from project directory
twine upload --config-file .pypirc --repository pypi dist/*
upload_done=$?

if [ $upload_done -ne 0 ]; then
    echo "Error: Failed to upload package -> Rolling back"
    rm -rf ./dist
    uv pip uninstall --quiet -y twine build
    mv ./pyproject.toml.bak ./pyproject.toml
    exit 1
fi

echo "Cleaning up..."
rm -rf ./dist
uv pip uninstall --quiet -y twine build

# commit new version
git add .
git commit -m "Version bump: $NEW_VERSION"
git push

# tag new version
git tag $NEW_VERSION
git push --tags