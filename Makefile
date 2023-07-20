IMAGE=ruuvi2mqtt
NAME=$(IMAGE)

build:
	docker build . -t $(IMAGE)

run:
	docker run -d --name $(NAME) --privileged --network=host --restart=unless-stopped -v $(PWD):/app $(IMAGE)

run_bash:
	docker run --rm -it --entrypoint bash $(IMAGE)

rm:
	docker rm $(NAME)

