.PHONY: install test format clean run parse

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	pytest tests/

# Format code
format:
	black src/ tests/

# Clean up
clean:
	rm -rf .storage
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/*/__pycache__
	rm -rf tests/__pycache__

# Run a test file
run:
	python main.py run --test-file $(FILE) $(ARGS)

# Parse a test file
parse:
	python main.py parse --test-file $(FILE) $(ARGS)

# Create a .env file from template
env:
	cp .env.template .env
