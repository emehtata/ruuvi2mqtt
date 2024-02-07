MACH=$$(uname -m)
IMAGE=ruuvi2mqtt
NAME=$(IMAGE)
TAG=localhost:5000/$(IMAGE)-$(MACH)

build:
	docker build . -t $(TAG)

run:
	docker run -d --name $(NAME) --privileged --network=host --restart=unless-stopped $(TAG)

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
	docker run --rm -it --entrypoint bash $(TAG)

logs:
	docker logs $(NAME)

restart:
	docker restart $(NAME)

start:
	docker start $(NAME)

push:
	docker push $(TAG)
