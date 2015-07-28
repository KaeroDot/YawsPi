# documentation:
doxygen:
	doxygen doxy_config
markdown:
	rm README.html
	markdown README.md >> README.html
