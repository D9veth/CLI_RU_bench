.PHONY: install test test-backend test-cli build-frontend docker-up docker-test clean-release

install:
	python -m pip install -e ".[dev,analysis]"
	cd backend && python -m pip install -r requirements.txt
	cd frontend && npm ci

test: test-cli test-backend build-frontend

test-cli:
	pytest -q tests

test-backend:
	cd backend && pytest -q
	cd backend && python manage.py check

build-frontend:
	cd frontend && npm run build

docker-up:
	docker compose up -d --build

docker-test:
	docker compose build
	docker compose ps

clean-release:
	scripts/make_release_archive.sh
