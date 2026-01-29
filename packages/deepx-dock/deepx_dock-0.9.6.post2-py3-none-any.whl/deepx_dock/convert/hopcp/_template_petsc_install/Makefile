download:
	bash ./_download.sh

install_offline:
	bash ./_install.sh

install: download install_offline

clean:
	rm -rf ./install
	rm -rf ./git.petsc

dist: clean
	rm -rf ./downloads

.PHONY: download install_offline install install_online clean dist
