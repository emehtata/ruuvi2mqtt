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

.PHONY: version setup build run stop rm rmi run_mount run_console run_bash logs restart start push install uninstall venv test

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
	docker build -f docker/Dockerfile-$(DISTRO) . -t $(TAG) --no-cache

run:
	docker run -d --name $(NAME) --privileged\
	 --network=host --restart=unless-stopped\
	 --cap-add NET_ADMIN \
	 --cap-add NET_RAW \
	 -v /run/dbus:/run/dbus:ro \
	 -v /etc/localtime:/etc/localtime:ro $(TAG)

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
