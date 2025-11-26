.PHONY: help install test run clean notebook

# Default target
help:
	@echo "Available targets:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run all tests"
	@echo "  make run        - Run the main analysis script"
	@echo "  make notebook   - Launch Jupyter notebook"
	@echo "  make clean      - Clean output files and cache"

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	PYTHONPATH=src python -m pytest tests/ -v

# Run the main script
run:
	PYTHONPATH=src python -m cme_gap_analyzer.main

# Launch Jupyter notebook
notebook:
	jupyter notebook notebooks/

# Clean output files
clean:
	rm -rf output/*.png output/*.csv
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

