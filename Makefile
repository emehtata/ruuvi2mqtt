MACH=$$(uname -m)
IMAGE=ruuvi2mqtt
NAME=$(IMAGE)
DISTRO?=alpine
GBRANCH=$(shell git rev-parse --abbrev-ref HEAD)
GITTAG=$(shell git describe --tags)
TAG="localhost:5000/$(IMAGE)-$(MACH)-$(DISTRO):$(GBRANCH)"
RELTAG="localhost:5000/$(IMAGE)-$(MACH)-$(DISTRO):$(GITTAG)"

ifeq ($(GBRANCH),master)
	GBRANCH=latest
endif

version:
	@echo "$(TAG)"

build:
	docker build -f Dockerfile-$(DISTRO) . -t $(TAG)

run:
	docker run -d --name $(NAME) --privileged --network=host --restart=unless-stopped -v /etc/localtime:/etc/localtime:ro $(TAG)

stop:
	docker stop $(NAME)

rm: stop
	docker rm $(NAME)

rmi: stop rm
	docker rmi $(TAG)

run_mount:
	docker run -d --name $(NAME) --privileged --network=host --restart=unless-stopped -v $(PWD):/app $(TAG)

run_console:
	docker run --name $(NAME) --privileged --network=host --restart=unless-stopped -v $(PWD):/app $(TAG)

run_bash:
	docker run --rm -it --privileged -v $(PWD):/app --entrypoint bash $(TAG)

logs:
	docker logs $(NAME)

restart:
	docker restart $(NAME)

start:
	docker start $(NAME)

push:
	docker push $(TAG)
	docker tag $(TAG) $(RELTAG)
	docker push $(RELTAG)
