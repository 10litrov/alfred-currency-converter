.PHONY .SILENT: help format lint
.DEFAULT_GOAL := help

help: ## print this help
	# see https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	echo "Usage: make <command>\n"
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-10s %s\n", $$1, $$2}'

format: ## format sources with black
	black .

lint:  ## lint codebase with flake8
	flake8 .
