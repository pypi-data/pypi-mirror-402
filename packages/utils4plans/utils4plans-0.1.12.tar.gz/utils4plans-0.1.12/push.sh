# TODO run from root -> pass path 
source .env && uv version --bump patch && uv build && uv publish 