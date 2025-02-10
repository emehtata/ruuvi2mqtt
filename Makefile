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

.PHONY: version setup build run stop rm rmi run_mount run_console run_bash logs restart start push install uninstall venv

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
	docker build -f docker/Dockerfile-$(DISTRO) . -t $(TAG)

run: build
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
run_mount: build
	docker run -d --name $(NAME) --privileged --network=host --restart=unless-stopped -v $(PWD):/app $(TAG)

run_console: build
	docker run --rm --name $(NAME) --privileged --network=host -v $(PWD):/app $(TAG)

run_bash: build
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
