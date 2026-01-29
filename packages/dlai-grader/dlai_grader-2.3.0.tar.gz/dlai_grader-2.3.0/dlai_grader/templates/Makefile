.PHONY: sync learner build debug-unsafe debug-safe grade versioning tag undeletable uneditable init upgrade coursera zip

include .conf

PARTIDS = 123 456
COURSERA_PARTIDS = "123 456"

OS := $(shell uname)

sync:
	cp mount/submission.ipynb ../$(ASSIGNMENT_NAME)_Solution.ipynb
	cp learner/$(ASSIGNMENT_NAME).ipynb ../$(ASSIGNMENT_NAME).ipynb
	cp mount/$(UNIT_TESTS_NAME).py ../$(UNIT_TESTS_NAME).py

learner:
	dlai_grader --learner --output_notebook=./learner/$(ASSIGNMENT_NAME).ipynb
	jupyter nbconvert --clear-output --inplace ./learner/$(ASSIGNMENT_NAME).ipynb
# 	rsync -a --exclude="submission.ipynb" --exclude="__pycache__" --exclude=".*" ./mount/ ./learner/

build:
	docker build -t $(IMAGE_NAME):$(TAG_ID) .

debug-unsafe:
	docker run -it --rm --mount type=bind,source=$(PWD)/mount,target=/shared/submission --mount type=bind,source=$(PWD),target=/grader/ --env-file $(PWD)/.env --entrypoint ash $(IMAGE_NAME):$(TAG_ID)

debug-safe:
	docker run -it --rm --mount type=bind,source=$(PWD)/mount,target=/shared/submission --env-file $(PWD)/.env --entrypoint ash $(IMAGE_NAME):$(TAG_ID)

grade:
	docker run -it --rm --memory=$(HARD_MEMORY) --cpus="$(CPUS)" --memory-reservation=$(SOFT_MEMORY) --mount type=bind,source=$(PWD)/mount,target=/shared/submission --env-file $(PWD)/.env --entrypoint ash $(IMAGE_NAME):$(TAG_ID) -c 'for partId in $(PARTIDS); do export partId=$$partId; echo "Processing part $$partId"; python entry.py; done'

versioning:
	dlai_grader --versioning

tag:
	dlai_grader --tag

undeletable:
	dlai_grader --undeletable

uneditable:
	dlai_grader --uneditable

init:
	dlai_grader --versioning
	dlai_grader --tag
	dlai_grader --undeletable
	dlai_grader --uneditable

upgrade:
	dlai_grader --upgrade

coursera:
	dlai_grader --grade --partids=$(COURSERA_PARTIDS) --docker=$(IMAGE_NAME):$(TAG_ID) --memory=$(MEMORY_LIMIT) --submission=$(SUB_DIR)

zip:
	zip -r $(IMAGE_NAME)$(TAG_ID).zip .