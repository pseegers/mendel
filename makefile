clean:
	rm -rf ./dist/
	rm -rf ./build/
	rm -rf *.egg-info
	find . -name "*.pyc" -exec rm -rf {} \;
	rm -rf *.egg

test:
	python -m unittest discover
