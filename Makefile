
tests:
	pytest

ensure-build:
	python -m pip install --upgrade build setuptools wheel

package: ensure-build
	python -m build

dist-only: ensure-build
	python -m build --wheel

clean:
	python - <<'PY'
		import shutil,glob,os
		patterns = ['build','dist','*.egg-info','.pytest_cache']
		for p in patterns:
			for f in glob.glob(p):
				if os.path.isdir(f):
					shutil.rmtree(f)
				else:
					try:
						os.remove(f)
					except Exception:
						pass
		print('cleaned')
	PY

