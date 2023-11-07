MACH=$$(uname -m)
IMAGE=ruuvi2mqtt
NAME=$(IMAGE)
TAG=localhost:5000/$(IMAGE)-$(MACH)

build:
	docker build . -t $(IMAGE)

run:
	docker run -d --name $(NAME) --privileged --network=host --restart=unless-stopped $(IMAGE)

stop:
	docker stop $(NAME)

rm: stop
	docker rm $(NAME)

rmi: stop rm
	docker rmi $(IMAGE)

run_mount:
	docker run -d --name $(NAME) --privileged --network=host --restart=unless-stopped -v $(PWD):/app $(IMAGE)

run_bash:
	docker run --rm -it --entrypoint bash $(IMAGE)

logs:
	docker logs $(NAME)

restart:
	docker restart $(NAME)

start:
	docker start $(NAME)

tag:
	docker tag $(IMAGE) $(TAG)

push:
	docker push $(TAG)
