.PHONY: help build install install-dev clean test uninstall list-skills verify

help:
	@echo "Clickzetta Skills - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make build        - Build the distribution package"
	@echo "  make install      - Install the package locally"
	@echo "  make install-dev  - Install in development mode (editable)"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make test         - Run tests"
	@echo "  make verify       - Verify package structure"
	@echo "  make uninstall    - Uninstall the package"
	@echo "  make list-skills  - List all available skills"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make install      # Install the package"
	@echo "  2. cz-analyze-job plan.json job_profile.json output_dir"
	@echo ""
	@echo "Available skills:"
	@echo "  - Job Performance Analyzer: cz-analyze-job"

build: clean
	@echo "Building clickzetta-skills package..."
	python3 -m build
	@echo "✅ Build complete! Package files in dist/"

install: build
	@echo "Installing clickzetta-skills..."
	pip3 install dist/*.whl --force-reinstall
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Available commands:"
	@echo "  cz-analyze-job <plan.json> <job_profile.json> [output_dir]"

install-dev:
	@echo "Installing in development mode..."
	pip3 install -e .
	@echo "✅ Development installation complete!"
	@echo ""
	@echo "Changes to code will take effect immediately without reinstalling."

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info clickzetta_skills.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete!"

test:
	@echo "Running tests for all skills..."
	@echo ""
	@echo "Testing Job Performance Analyzer..."
	@cd job-performance-analyzer/tests && python3 test_incremental_logic.py
	@cd job-performance-analyzer/tests && python3 test_path_based_logic.py
	@cd job-performance-analyzer/tests && python3 test_improvements.py
	@echo ""
	@echo "✅ All tests complete!"

uninstall:
	@echo "Uninstalling clickzetta-skills..."
	pip3 uninstall -y clickzetta-skills
	@echo "✅ Uninstall complete!"

# Development helpers
dev-check:
	@echo "Checking installation..."
	@echo ""
	@pip3 show clickzetta-skills || echo "❌ Package not installed"
	@echo ""
	@echo "Checking available commands:"
	@which cz-analyze-job && echo "✅ cz-analyze-job found" || echo "❌ cz-analyze-job not found"

list-skills:
	@echo "Available skills in clickzetta-skills:"
	@echo ""
	@echo "1. Job Performance Analyzer"
	@echo "   Command: cz-analyze-job"
	@echo "   Description: 分析 plan.json 和 job_profile.json，识别性能瓶颈"
	@echo ""
	@echo "2. SQL History Expert"
	@echo "   Command: cz-sql-history"
	@echo "   Description: 分析 SQL 执行历史，识别性能趋势和异常"
	@echo ""
	@echo "3. Table Stats Expert"
	@echo "   Command: cz-table-stats"
	@echo "   Description: 分析表统计信息，提供优化建议"
	@echo ""
	@echo "To add more skills, see README.md"

rebuild: clean build
	@echo "✅ Rebuild complete!"

upload:
	@echo "Uploading package to PyPI..."
	@echo "Package: clickzetta-skills"
	twine upload dist/*
	@echo "✅ Upload complete!"

# Verify package structure before building
verify:
	@echo "Verifying package structure..."
	@echo ""
	@echo "Checking job-performance-analyzer:"
	@test -d job-performance-analyzer && echo "✅ job-performance-analyzer/ exists" || echo "❌ job-performance-analyzer/ missing"
	@test -f job-performance-analyzer/__init__.py && echo "✅ __init__.py exists" || echo "❌ __init__.py missing"
	@test -f job-performance-analyzer/__main__.py && echo "✅ __main__.py exists" || echo "❌ __main__.py missing"
	@test -f job-performance-analyzer/analyze_job.py && echo "✅ analyze_job.py exists" || echo "❌ analyze_job.py missing"
	@echo ""
	@echo "Checking pyproject.toml configuration:"
	@grep -q "job_performance_analyzer" pyproject.toml && echo "✅ Entry point configured correctly" || echo "❌ Entry point misconfigured"
	@echo ""
	@echo "✅ Verification complete!"