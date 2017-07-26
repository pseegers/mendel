init:
	pip install -r requirements.txt

test:
	tox

clean:
	rm -rf ./dist/
	rm -rf ./build/
	rm -rf *.egg-info
	find . -name "*.pyc" -exec rm -rf {} \;
	rm -rf *.egg
	rm -rf .cache/
	rm -rf .eggs/
	rm -rf .tox/
