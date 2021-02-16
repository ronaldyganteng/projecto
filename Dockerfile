# Using Groovy
FROM biansepang/weebproject:groovy

# Clone repo and prepare working directory
RUN git clone -b master https://github.com/ronaldyganteng/projecto /home/archiztec/
RUN mkdir /home/archiztec/bin/
WORKDIR /home/archiztec/

# Make open port TCP
EXPOSE 80 443

# Finalization
CMD ["python3","-m","userbot"]
