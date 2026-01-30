clean:
	rm -rf build dist *.egg-info
	find . | grep -E "(__pycache__)" | xargs rm -rf

dist: clean
	python3 -m build

publish-test: dist
	twine upload -r test --sign dist/*

publish: dist
	twine upload --sign dist/*
