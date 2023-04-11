PYXS = $(wildcard src/tarina/*.pyx)


src/tarina/%.c: src/tarina/%.pyx
	python -m cython -3 -o $@ $< -I src/tarina


cythonize: $(PYXS:.pyx=.c)