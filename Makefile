.PHONY: test

test:
	@echo "🧪 Running unit tests..."
	python -m unittest discover -s tests -p 'test_*.py' -v --failfast
