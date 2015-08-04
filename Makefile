# documentation:
documentation:
	doxygen doxy_config
	if [ ! -d "doc/html/images" ]; then ln -s ../../images doc/html/images; fi
markdown:
	rm README.html
	markdown README.md >> README.html
