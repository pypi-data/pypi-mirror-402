FROM ubuntu:jammy


RUN apt-get update \
	&& apt-get install -y git python3 python3-pip openjdk-11-jdk tree

RUN pip3 install lsr-benchmark[dev,test] && pip3 uninstall -y lsr-benchmark

