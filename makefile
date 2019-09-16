version = $(shell egrep -o "[0-9]+\.[0-9]+\.[0-9]+[a-z]+[0-0]+" mendel/version.py)

init:
	pip install -r requirements.txt

test:
	tox

release: test
	@echo "releasing version $(version)..."
	# only allow releasing from master branch
	[[ "`git rev-parse --abbrev-ref HEAD`" == "master" ]]
	# if tag fails, that means we're trying to build
	# a version that already exists
	git tag $(version)
	python setup.py sdist
	sudo twine upload --repository-url http://pypi.int.sproutsocial.com:7974 dist/*
	# dont push tag til successfully uploaded to pypi
	# git push origin $(version)

clean:
	rm -rf ./dist/
	rm -rf ./build/
	rm -rf *.egg-info
	find . -name "*.pyc" -exec rm -rf {} \;
	rm -rf *.egg
	rm -rf .cache/
	rm -rf .eggs/
	rm -rf .tox/
