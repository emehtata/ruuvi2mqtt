MACH := $(shell uname -m)
IMAGE := ruuvi2mqtt
APP := $(shell basename $(PWD))
NAME := $(IMAGE)
DISTRO ?= alpine
GBRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GITTAG := $(shell git describe --tags 2>/dev/null || echo "latest")

# Docker Tags
REPOHOST ?= localhost:5000
TAG := "$(REPOHOST)/$(IMAGE)-$(DISTRO):$(MACH)-$(GBRANCH)"
RELTAG := "$(REPOHOST)/$(IMAGE)-$(DISTRO):$(MACH)-$(GITTAG)"

.PHONY: version setup build run stop rm rmi run_mount run_console run_bash logs restart start push install uninstall venv test volume-inspect volume-backup volume-restore volume-rm

# Print version information
version:
	@echo "Branch Tag: $(TAG)"
	@echo "Release Tag: $(RELTAG)"

# Setup Python environment and install package
setup:
	python3 setup.py sdist bdist_wheel
	pip3 install -e .

# Docker build, run, and management
build:
	@TODAY=$$(date +%Y.%-m.%-d); \
	CURRENT_TAG=$$(git tag -l "$$TODAY" 2>/dev/null); \
	if [ -z "$$CURRENT_TAG" ]; then \
		echo "Creating new tag for $$TODAY"; \
		git tag -a $$TODAY -m "Release $$TODAY" 2>/dev/null || true; \
	fi; \
	VERSION=$$(git describe --long --tags 2>/dev/null || echo "$$TODAY-0-unknown"); \
	echo "$$VERSION" > VERSION; \
	echo "Building version: $$VERSION"
	docker build -f docker/Dockerfile-$(DISTRO) . -t $(TAG)

run:
	@docker volume create $(NAME)-data 2>/dev/null || true
	docker run -d --name $(NAME) --privileged\
	 --network=host --restart=unless-stopped\
	 --cap-add NET_ADMIN \
	 --cap-add NET_RAW \
	 -v /run/dbus:/run/dbus:ro \
	 -v /etc/localtime:/etc/localtime:ro \
	 -v $(NAME)-data:/data \
	 -e WEBAPP_PORT=5883 \
	 $(TAG)

stop:
	docker stop $(NAME)

rm: stop
	docker rm $(NAME)

rmi: stop rm
	docker rmi $(TAG)

# Development run modes
run_mount:
	docker run -d --name $(NAME) --privileged --network=host --restart=unless-stopped -v $(PWD):/app $(TAG)

run_console:
	docker run --rm --name $(NAME) --privileged --network=host -v $(PWD):/app $(TAG)

run_bash:
	docker run --rm -it --privileged -v $(PWD):/app --entrypoint bash $(TAG)

logs:
	docker logs $(NAME)

restart:
	docker restart $(NAME)

start:
	docker start $(NAME)

# Push image to registry
push: build
	docker push $(TAG)
	docker tag $(TAG) $(RELTAG)
	docker push $(RELTAG)

# Helm install/uninstall
install:
	helm upgrade --install $(APP) chart -n $(APP) --create-namespace

uninstall:
	helm uninstall $(APP) -n $(APP)

# Virtual environment setup
venv:
	python3 -m venv .venv
	@echo "Virtual environment created in .venv"

# Volume management
volume-inspect:
	@echo "Inspecting volume $(NAME)-data:"
	@docker volume inspect $(NAME)-data 2>/dev/null || echo "Volume does not exist"

volume-backup:
	@echo "Backing up settings from volume..."
	@docker run --rm -v $(NAME)-data:/data -v $(PWD):/backup alpine cp /data/settings.py /backup/settings.py.backup
	@echo "Backup saved to settings.py.backup"

volume-restore:
	@if [ ! -f settings.py.backup ]; then echo "No backup file found"; exit 1; fi
	@echo "Restoring settings to volume..."
	@docker run --rm -v $(NAME)-data:/data -v $(PWD):/backup alpine cp /backup/settings.py.backup /data/settings.py
	@echo "Settings restored from backup"

volume-rm:
	@echo "Removing volume $(NAME)-data..."
	@docker volume rm $(NAME)-data

# Run unit tests
test:
	@if [ ! -d ".venv" ]; then \
		echo "Virtual environment not found. Creating it..."; \
		make venv; \
	fi
	@echo "Installing dependencies..."
	@bash -c "source .venv/bin/activate && pip install -q -r requirements.txt"
	@echo "Running unit tests..."
	@bash -c "source .venv/bin/activate && python -m pytest test_ruuvi2mqtt.py --cov=ruuvi2mqtt --cov-report=term-missing -v"

# Version management (year.month.day format, patch from git describe)
tag:
	@TODAY=$$(date +%Y.%-m.%-d); \
	git tag -a $$TODAY -m "Release $$TODAY" 2>/dev/null || echo "Tag $$TODAY already exists"; \
	VERSION=$$(git describe --long --tags 2>/dev/null || echo "$$TODAY-0-unknown"); \
	echo "$$VERSION" > VERSION; \
	echo "Version set to: $$VERSION"

tag-push:
	@TODAY=$$(date +%Y.%-m.%-d); \
	echo "Pushing tag: $$TODAY"; \
	git push origin $$TODAY

dev-run:
	python3 ruuvi2mqtt.py
