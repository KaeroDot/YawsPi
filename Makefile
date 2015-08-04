# documentation:
documentation:
	doxygen doxy_config
	ln -s ../../images doc/html/images
markdown:
	rm README.html
	markdown README.md >> README.html
